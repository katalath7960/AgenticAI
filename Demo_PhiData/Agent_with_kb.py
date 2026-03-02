import os
from typing import Optional, List
from pathlib import Path
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.embedder.openai import OpenAIEmbedder
from phi.knowledge.text import TextKnowledgeBase
from phi.vectordb.lancedb import LanceDb, SearchType
from phi.document.chunking.fixed import FixedSizeChunking

    
from dotenv import load_dotenv
load_dotenv()

def create_csv_analyst():
    """csv analyst"""

    # RAG DB
    knowledge_base = TextKnowledgeBase(
        path="./data/sample_article.txt",
        vector_db=LanceDb(
            table_name="sample_article_vector",
            uri="./tmp/lancedb",
            search_type=SearchType.vector,
            embedder=OpenAIEmbedder(model="text-embedding-3-small"),
        ),
        chunking_strategy=FixedSizeChunking(
            chunk_size=512,
            overlap=64,
        ),
        num_documents=6,
    )

    knowledge_base.load(recreate=True)

    agent = Agent(
        name="Jarvis",
        model=OpenAIChat(id="gpt-4o", temperature=0.1),
        description="You are a helpful AI assistant.",
        instructions=[
            "You are an article analysis assistant.",
            "Always search the knowledge base before answering.",
            "Base your answers strictly on the retrieved context.",
            "Quote or reference the relevant passage when possible.",
            "If the context does not contain the answer, say so clearly.",
        ],
        markdown=True,
        debug_mode=True,  
        search_knowledge=True,
        knowledge_base=knowledge_base
    )
    return agent

if __name__ == "__main__":
    agent = create_csv_analyst()
    agent.print_response("What are AI capabilities", stream=True)