import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
import json

# Load environment variables
load_dotenv()

# Sample engineering career rubric data
RUBRIC_DATA = [
    {
        "text": "L3 Engineer: Demonstrates solid technical skills, completes assigned tasks effectively, and works well within a team. Shows good problem-solving abilities and can implement solutions with guidance. Communicates clearly with team members and stakeholders.",
        "metadata": {"level": "L3", "category": "technical_skills"}
    },
    {
        "text": "L4 Engineer: Takes ownership of complex features and projects. Designs and implements solutions with minimal guidance. Mentors junior engineers and contributes to team processes. Identifies technical debt and proposes solutions.",
        "metadata": {"level": "L4", "category": "technical_leadership"}
    },
    {
        "text": "L5 Engineer: Leads technical direction for a team or project. Architects complex systems and makes high-level technical decisions. Mentors multiple engineers and influences cross-functional teams. Identifies strategic opportunities and drives technical initiatives.",
        "metadata": {"level": "L5", "category": "system_design"}
    },
    {
        "text": "L6 Engineer: Sets technical direction for multiple teams or a large organization. Architects complex distributed systems and makes critical technical decisions. Mentors senior engineers and influences company-wide technical strategy. Identifies and drives major technical initiatives.",
        "metadata": {"level": "L6", "category": "technical_strategy"}
    },
    {
        "text": "L7 Engineer: Shapes the technical direction of the entire company. Architects industry-leading systems and makes foundational technical decisions. Mentors technical leaders and influences the broader industry. Identifies and drives transformative technical initiatives.",
        "metadata": {"level": "L7", "category": "industry_leadership"}
    },
    {
        "text": "Technical Skills: Demonstrates proficiency in programming languages, frameworks, and tools relevant to the role. Writes clean, maintainable, and efficient code. Understands software design patterns and principles. Debugs and troubleshoots effectively.",
        "metadata": {"category": "technical_skills", "subcategory": "coding"}
    },
    {
        "text": "System Design: Can design and architect complex systems. Understands scalability, reliability, and performance considerations. Makes appropriate trade-offs in system design. Can explain design decisions clearly to stakeholders.",
        "metadata": {"category": "technical_skills", "subcategory": "architecture"}
    },
    {
        "text": "Problem Solving: Identifies root causes of complex problems. Develops innovative solutions to challenging technical issues. Evaluates multiple approaches and selects the most appropriate one. Balances short-term fixes with long-term solutions.",
        "metadata": {"category": "technical_skills", "subcategory": "problem_solving"}
    },
    {
        "text": "Leadership: Provides technical guidance and mentorship to team members. Delegates tasks effectively and holds team members accountable. Fosters a collaborative and inclusive team environment. Advocates for the team's needs and interests.",
        "metadata": {"category": "leadership", "subcategory": "team_leadership"}
    },
    {
        "text": "Communication: Communicates technical concepts clearly to both technical and non-technical audiences. Provides constructive feedback and actively listens to others. Documents work effectively and shares knowledge with the team.",
        "metadata": {"category": "soft_skills", "subcategory": "communication"}
    },
    {
        "text": "Impact: Delivers high-quality work that has a significant positive impact on the product or service. Identifies opportunities to improve efficiency and user experience. Balances technical excellence with business value.",
        "metadata": {"category": "impact", "subcategory": "product_impact"}
    },
    {
        "text": "Growth Mindset: Continuously learns and adapts to new technologies and methodologies. Seeks feedback and uses it to improve. Takes initiative to expand skills and knowledge. Embraces challenges and views failures as learning opportunities.",
        "metadata": {"category": "growth", "subcategory": "learning"}
    }
]

def load_data():
    """Load synthetic data into Qdrant."""
    print("Loading synthetic data into Qdrant...")
    
    # Initialize Qdrant client (using in-memory for testing)
    client = QdrantClient(":memory:")
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings()
    
    # Create collection
    collection_name = "rubrics"
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=1536,  # OpenAI embedding dimension
            distance=models.Distance.COSINE
        )
    )
    
    # Generate embeddings and upload data
    points = []
    for i, item in enumerate(RUBRIC_DATA):
        vector = embeddings.embed_query(item["text"])
        points.append(
            models.PointStruct(
                id=i,
                vector=vector,
                payload={"text": item["text"], "metadata": item["metadata"]}
            )
        )
    
    # Upload points in batches
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    
    print(f"Loaded {len(points)} rubric items into Qdrant.")
    
    # Save the client to a file for later use
    # Note: This is a workaround since we can't directly save the in-memory client
    # In a real application, you would use a persistent Qdrant instance
    print("Note: Using in-memory Qdrant. Data will be lost when the script ends.")
    print("For persistence, configure a local or remote Qdrant instance in .env")
    
    return client

if __name__ == "__main__":
    load_data()
    print("\nTo test the agent with this data, run:")
    print("python main.py") 