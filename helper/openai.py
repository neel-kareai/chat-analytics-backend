from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, SimpleDirectoryReader
from config import Config
from fastapi import HTTPException, status
from logger import logger


def create_document_embedding(
    document_path: str,
    customer_uuid: str,
) -> str:
    """
    Create a document embedding for the given document path and customer UUID.

    Args:
        document_path (str): The path of the document to create the embedding for.
        customer_uuid (str): The UUID of the customer.

    Returns:
        str: The name of the chroma collection where the document embedding is stored.
    """

    try:
        openai_embedding = OpenAIEmbedding(model=Config.DEFAULT_OPENAI_EMBEDDING_MODEL)
        doc = SimpleDirectoryReader(
            input_files=[document_path],
        ).load_data()

        db = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
        filename = document_path.split("/")[-1]
        chroma_collection_name = f"{customer_uuid}_{filename}"

        chroma_collection = db.get_or_create_collection(chroma_collection_name)
        vector_store = ChromaVectorStore(
            chroma_collection=chroma_collection,
        )
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
        )

        index = VectorStoreIndex.from_documents(
            doc,
            storage_context=storage_context,
            embed_model=openai_embedding,
        )
    except Exception as e:
        logger.error(f"Failed to create document embedding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document embedding",
        )

    return chroma_collection_name
