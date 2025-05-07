"""
Markdown table generator for content visualization.
"""

from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from ..interfaces import ContentItem, ContentVisualizer

class MarkdownTableVisualizer(ContentVisualizer):
    """Generates markdown tables from content items."""
    
    def __init__(self, data_dir: Path):
        super().__init__(data_dir)
        self.exports_dir = data_dir / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_table(self, items: List[ContentItem]) -> str:
        """Generate a markdown table of content items."""
        if not items:
            return "No content items to display."
        
        # Table header
        table = [
            "| Title | Source | Authors | Published | Quality | URL |",
            "|-------|---------|---------|-----------|----------|-----|"
        ]
        
        # Table rows
        for item in items:
            pub_date = item.publish_date.strftime("%Y-%m-%d") if item.publish_date else "N/A"
            authors = ", ".join(item.authors) if item.authors else "Unknown"
            quality = f"{item.metadata.source_quality:.1f}/10"
            
            row = [
                item.title[:50] + "..." if len(item.title) > 50 else item.title,
                item.metadata.source_name,
                authors[:30] + "..." if len(authors) > 30 else authors,
                pub_date,
                quality,
                f"[Link]({item.url})"
            ]
            
            # Escape pipe characters in cells
            row = [cell.replace("|", "\\|") for cell in row]
            table.append(f"| {' | '.join(row)} |")
        
        return "\n".join(table)
    
    def generate_stats(self, items: List[ContentItem]) -> Dict[str, Any]:
        """Generate statistics for content items."""
        if not items:
            return {"error": "No content items to analyze"}
        
        stats = {
            "total_items": len(items),
            "by_source": {},
            "by_type": {},
            "avg_quality": 0.0,
            "date_range": {
                "earliest": None,
                "latest": None
            }
        }
        
        total_quality = 0
        
        for item in items:
            # Count by source
            source = item.metadata.source_type
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
            # Count by type
            content_type = item.metadata.content_type
            stats["by_type"][content_type] = stats["by_type"].get(content_type, 0) + 1
            
            # Track quality
            total_quality += item.metadata.source_quality
            
            # Track date range
            if item.publish_date:
                if not stats["date_range"]["earliest"] or item.publish_date < stats["date_range"]["earliest"]:
                    stats["date_range"]["earliest"] = item.publish_date
                if not stats["date_range"]["latest"] or item.publish_date > stats["date_range"]["latest"]:
                    stats["date_range"]["latest"] = item.publish_date
        
        # Calculate average quality
        stats["avg_quality"] = total_quality / len(items)
        
        # Convert dates to strings
        if stats["date_range"]["earliest"]:
            stats["date_range"]["earliest"] = stats["date_range"]["earliest"].strftime("%Y-%m-%d")
        if stats["date_range"]["latest"]:
            stats["date_range"]["latest"] = stats["date_range"]["latest"].strftime("%Y-%m-%d")
        
        return stats
    
    def save_table(self, items: List[ContentItem], filename: str = None) -> Path:
        """
        Save the markdown table to a file.
        
        Args:
            items: List of content items
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to the saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"content_table_{timestamp}.md"
        
        output_path = self.exports_dir / filename
        table_content = self.generate_table(items)
        
        # Add stats section
        stats = self.generate_stats(items)
        stats_section = "\n\n## Statistics\n\n"
        stats_section += f"- Total Items: {stats['total_items']}\n"
        stats_section += f"- Average Quality: {stats['avg_quality']:.1f}/10\n"
        stats_section += f"- Date Range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}\n\n"
        
        stats_section += "### By Source\n"
        for source, count in stats["by_source"].items():
            stats_section += f"- {source}: {count}\n"
        
        stats_section += "\n### By Type\n"
        for type_, count in stats["by_type"].items():
            stats_section += f"- {type_}: {count}\n"
        
        with open(output_path, 'w') as f:
            f.write("# Content Curation Results\n\n")
            f.write("## Content Table\n\n")
            f.write(table_content)
            f.write(stats_section)
        
        return output_path 