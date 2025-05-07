"""
Technical papers source implementation.
"""

import json
import logging
import re
import time
import os
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from bs4 import BeautifulSoup

from ...interfaces import ContentSource, ContentItem, ContentMetadata
from ...modules.pdf_processor import download_pdf, batch_download_pdfs

logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ArXiv API namespaces
ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}
ARXIV_NS = {'arxiv': 'http://arxiv.org/schemas/atom'}

class TechnicalPapersSource(ContentSource):
    """Content source for technical papers."""
    
    def __init__(self, cache_dir: Path, output_dir: Path):
        super().__init__(cache_dir, output_dir)
        self.cache_file = self.cache_dir / "papers_cache.json"
        self.cache = self._load_cache()
        
        # Initialize API clients if keys are available
        self.tavily_client = None
        self.openai_client = None
        
        if os.getenv("TAVILY_API_KEY"):
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                logger.info("Initialized Tavily API client")
            except ImportError:
                logger.warning("Tavily Python package not available")
        else:
            logger.warning("TAVILY_API_KEY not found in environment")
            
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                logger.info("Initialized OpenAI API client")
            except ImportError:
                logger.warning("OpenAI Python package not available")
        else:
            logger.warning("OPENAI_API_KEY not found in environment")
        
        # API endpoints
        self.arxiv_api_url = "http://export.arxiv.org/api/query"
        
        # PDF sources and their URL patterns
        self.paper_sources = {
            "arxiv": lambda url: "arxiv.org" in url and url.endswith(".pdf"),
            "ieee": lambda url: "ieee.org" in url and url.endswith(".pdf"),
            "acm": lambda url: "acm.org" in url and url.endswith(".pdf"),
            "springer": lambda url: "springer.com" in url and url.endswith(".pdf"),
            "sciencedirect": lambda url: "sciencedirect.com" in url and url.endswith(".pdf")
        }
        
        # Paper repositories to search
        self.paper_repositories = [
            "arxiv.org",
            "ieeexplore.ieee.org",
            "dl.acm.org",
            "link.springer.com",
            "sciencedirect.com"
        ]
    
    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading papers cache: {str(e)}")
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving papers cache: {str(e)}")
    
    def _search_arxiv(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search arXiv using their API."""
        cache_key = f"arxiv_search_{hashlib.md5(query.encode()).hexdigest()}"
        if cache_key in self.cache:
            cache_time = self.cache[cache_key].get("timestamp", 0)
            if time.time() - cache_time < 24 * 60 * 60:  # 24 hours
                return self.cache[cache_key].get("data", [])
        
        params = {
            'search_query': f"all:{query}",
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(self.arxiv_api_url, params=params)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            papers = []
            for entry in root.findall('.//atom:entry', ATOM_NS):
                try:
                    # Get paper ID
                    id_elem = entry.find('./atom:id', ATOM_NS)
                    entry_id = id_elem.text if id_elem is not None else ""
                    
                    # Get paper details
                    paper = {
                        "entry_id": entry_id,
                        "title": entry.find('./atom:title', ATOM_NS).text.strip(),
                        "summary": entry.find('./atom:summary', ATOM_NS).text.strip(),
                        "published_date": entry.find('./atom:published', ATOM_NS).text,
                        "url": None,
                        "pdf_url": None,
                        "authors": [],
                        "categories": []
                    }
                    
                    # Get authors
                    for author in entry.findall('./atom:author', ATOM_NS):
                        name = author.find('./atom:name', ATOM_NS)
                        if name is not None:
                            paper["authors"].append(name.text)
                    
                    # Get categories
                    for category in entry.findall('./atom:category', ATOM_NS):
                        term = category.get('term')
                        if term:
                            paper["categories"].append(term)
                    
                    # Get links
                    for link in entry.findall('./atom:link', ATOM_NS):
                        href = link.get('href')
                        rel = link.get('rel')
                        title = link.get('title')
                        
                        if rel == 'alternate':
                            paper["url"] = href
                        elif title == 'pdf':
                            paper["pdf_url"] = href
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.error(f"Error parsing arXiv entry: {str(e)}")
                    continue
            
            # Cache the results
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": papers
            }
            self._save_cache()
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv: {str(e)}")
            return []
    
    def _validate_paper_with_llm(self, paper_info: Dict) -> bool:
        """Use LLM to validate if a paper is relevant and high-quality."""
        if not self.openai_client:
            # If no OpenAI client, assume all papers are valid
            return True
            
        try:
            prompt = f"""Please analyze this technical paper and determine if it's relevant and high-quality:

Title: {paper_info.get('title', '')}
Authors: {', '.join(paper_info.get('authors', []))}
Summary: {paper_info.get('summary', '')}
Source: {paper_info.get('source', '')}

Please respond with either 'yes' or 'no' based on these criteria:
1. Is it a technical/academic paper (not a blog post or article)?
2. Is it from a reputable source?
3. Does it appear to be peer-reviewed or professionally published?
4. Is it likely to contain substantive technical content?

Response (yes/no):"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().lower()
            return answer == 'yes'
            
        except Exception as e:
            logger.error(f"Error validating paper with LLM: {str(e)}")
            return True  # Default to accepting if LLM validation fails
    
    def discover(self, query: str, limit: int = 10) -> List[ContentItem]:
        """Discover technical papers based on query."""
        discovered_items = []
        seen_urls = set()
        
        # 1. Search arXiv papers using their API
        try:
            papers = self._search_arxiv(query, max_results=limit)
            
            # List to hold paper download metadata
            paper_downloads = []
            
            for paper in papers:
                if len(discovered_items) >= limit:
                    break
                    
                pdf_url = paper.get("pdf_url")
                if not pdf_url or pdf_url in seen_urls:
                    continue
                
                seen_urls.add(pdf_url)
                
                paper_info = {
                    "title": paper.get("title", ""),
                    "url": pdf_url,
                    "source": "arxiv",
                    "authors": paper.get("authors", []),
                    "published_date": paper.get("published_date"),
                    "summary": paper.get("summary", ""),
                    "categories": paper.get("categories", []),
                    "entry_id": paper.get("entry_id", "")
                }
                
                # Validate paper with LLM if available, otherwise accept all
                if not self._validate_paper_with_llm(paper_info):
                    logger.info(f"Skipping paper {paper_info['title']} - failed LLM validation")
                    continue
                
                # Add to download list
                paper_downloads.append({
                    "url": pdf_url,
                    "source": "arxiv",
                    "title": paper_info["title"],
                    "metadata": paper_info
                })
            
            # Batch download PDFs
            if paper_downloads:
                logger.info(f"Batch downloading {len(paper_downloads)} PDFs from arXiv")
                downloaded_papers = batch_download_pdfs([
                    {"url": p["url"], "source": p["source"], "title": p["title"]} 
                    for p in paper_downloads
                ])
                
                # Match downloaded papers with metadata
                for i, download_result in enumerate(downloaded_papers):
                    if "error" not in download_result:
                        # Merge info from both sources
                        paper_info = paper_downloads[i]["metadata"]
                        paper_info["local_pdf_path"] = download_result.get("path")
                        
                        # Convert paper to ContentItem
                        try:
                            item = self._paper_to_content_item(paper_info)
                            if item:
                                discovered_items.append(item)
                        except Exception as e:
                            logger.error(f"Error converting paper to ContentItem: {str(e)}")
                            continue
                
        except Exception as e:
            logger.error(f"Error discovering arXiv papers: {str(e)}")
        
        # 2. Use Tavily to discover papers from other sources if available
        if self.tavily_client:
            try:
                # Enhance query for academic paper search
                search_query = f"technical paper research paper pdf {query} site:({' OR site:'.join(self.paper_repositories)})"
                
                # Search with Tavily
                search_results = self.tavily_client.search(
                    query=search_query,
                    search_depth="advanced",
                    include_answer=False,
                    include_raw_content=False,
                    max_results=limit * 2  # Request more to account for filtering
                )
                
                # List to hold paper download metadata
                tavily_papers = []
                
                for result in search_results.get('results', []):
                    if len(discovered_items) + len(tavily_papers) >= limit:
                        break
                    
                    url = result.get('url')
                    if not url or url in seen_urls:
                        continue
                    
                    # Check if URL matches any of our paper sources
                    source = None
                    for src, matcher in self.paper_sources.items():
                        if matcher(url):
                            source = src
                            break
                    
                    if not source:
                        continue
                    
                    seen_urls.add(url)
                    
                    # Create paper info from search result
                    paper_info = {
                        "title": result.get('title', ''),
                        "url": url,
                        "source": source,
                        "summary": result.get('description', ''),
                        "authors": [],  # Would need additional parsing
                        "published_date": None  # Would need additional parsing
                    }
                    
                    # Validate paper with LLM
                    if not self._validate_paper_with_llm(paper_info):
                        logger.info(f"Skipping paper {paper_info['title']} - failed LLM validation")
                        continue
                    
                    # Add to download list
                    tavily_papers.append({
                        "url": url,
                        "source": source,
                        "title": paper_info["title"],
                        "metadata": paper_info
                    })
                
                # Batch download PDFs from Tavily results
                if tavily_papers:
                    logger.info(f"Batch downloading {len(tavily_papers)} PDFs from Tavily search")
                    downloaded_papers = batch_download_pdfs([
                        {"url": p["url"], "source": p["source"], "title": p["title"]} 
                        for p in tavily_papers
                    ])
                    
                    # Match downloaded papers with metadata
                    for i, download_result in enumerate(downloaded_papers):
                        if "error" not in download_result:
                            # Merge info from both sources
                            paper_info = tavily_papers[i]["metadata"]
                            paper_info["local_pdf_path"] = download_result.get("path")
                            
                            # Convert paper to ContentItem
                            try:
                                item = self._paper_to_content_item(paper_info)
                                if item:
                                    discovered_items.append(item)
                            except Exception as e:
                                logger.error(f"Error converting paper to ContentItem: {str(e)}")
                                continue
                    
            except Exception as e:
                logger.error(f"Error discovering papers with Tavily: {str(e)}")
        
        return discovered_items
    
    def process_url(self, url: str) -> Optional[ContentItem]:
        """Process a single paper URL."""
        if not self.is_source_url(url):
            return None
            
        try:
            # Determine source type
            source = None
            for src, matcher in self.paper_sources.items():
                if matcher(url):
                    source = src
                    break
            
            if not source:
                return None
            
            # Download the PDF
            pdf_data = download_pdf(url, source)
            if not pdf_data:
                return None
            
            # Create paper info
            paper_info = {
                "title": pdf_data.get("title", ""),
                "url": url,
                "source": source,
                "authors": [],  # Not available from just URL
                "published_date": None,  # Not available from just URL
                "local_pdf_path": pdf_data.get("path"),
                "text_content": pdf_data.get("text_content")
            }
            
            return self._paper_to_content_item(paper_info)
            
        except Exception as e:
            logger.error(f"Error processing paper URL {url}: {str(e)}")
            return None
    
    def is_source_url(self, url: str) -> bool:
        """Check if URL is from a supported paper source."""
        return any(matcher(url) for src, matcher in self.paper_sources.items())
    
    def _paper_to_content_item(self, paper: Dict) -> Optional[ContentItem]:
        """Convert a paper to a ContentItem."""
        try:
            # Create metadata
            metadata = ContentMetadata(
                source_type="technical_paper",
                content_type="pdf",
                source_quality=9.0,  # Academic papers are generally high quality
                is_curated=True,
                source_name=f"Paper - {paper.get('source', 'unknown')}",
                additional_meta={
                    "source": paper.get("source"),
                    "categories": paper.get("categories", []),
                    "entry_id": paper.get("entry_id")
                }
            )
            
            # Parse publish date if available
            publish_date = None
            if paper.get("published_date"):
                try:
                    # Try various date formats
                    date_str = paper["published_date"]
                    for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            publish_date = datetime.strptime(date_str, fmt)
                            if fmt.endswith("Z"):
                                # UTC time, make it naive
                                publish_date = publish_date.replace(tzinfo=None)
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    logger.warning(f"Error parsing publish date {paper.get('published_date')}: {str(e)}")
            
            # Create content item
            return ContentItem(
                id=hashlib.md5(paper.get("url", "").encode()).hexdigest(),
                url=paper.get("url", ""),
                title=paper.get("title", ""),
                description=paper.get("summary", ""),
                authors=paper.get("authors", []),
                publish_date=publish_date,
                metadata=metadata,
                text_path=paper.get("local_pdf_path"),
                raw_data=paper
            )
            
        except Exception as e:
            logger.error(f"Error converting paper to ContentItem: {str(e)}")
            return None 