from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from config import Config
from fastapi import HTTPException, status
from logger import logger


def csv_pipeline(embedding_path: str, customer_query: str) -> str:
    """
        load the embedding and query the csv file
    """
    try:
        logger.debug(f"Querying csv: {embedding_path}")
        db = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
        embed_model = OpenAIEmbedding(
            model=Config.DEFAULT_OPENAI_EMBEDDING_MODEL)
        llm = OpenAI(model=Config.DEFAULT_OPENAI_MODEL)
        chroma_collection = db.get_or_create_collection(embedding_path)

        vector_store = ChromaVectorStore(
            chroma_collection=chroma_collection,
        )
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model
        )

        query_engine = index.as_query_engine(llm=llm)

        response = query_engine.query(customer_query)
    except Exception as e:
        logger.error(f"Failed to query csv: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query csv"
        )

    return str(response)
