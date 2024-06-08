from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex
from config import Config
from fastapi import HTTPException, status
from logger import logger

import pandas as pd
from llama_index.core.query_pipeline import (
    QueryPipeline as QP,
    Link,
    InputComponent,
)
from llama_index.experimental.query_engine.pandas import PandasInstructionParser
from llama_index.core import PromptTemplate
from datetime import datetime


def csv_pipeline(embedding_path: str, customer_query: str) -> str:
    """
    load the embedding and query the csv file
    """
    try:
        logger.debug(f"Querying csv: {embedding_path}")
        db = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
        embed_model = OpenAIEmbedding(model=Config.DEFAULT_OPENAI_EMBEDDING_MODEL)
        llm = OpenAI(model=Config.DEFAULT_OPENAI_MODEL)
        chroma_collection = db.get_or_create_collection(embedding_path)

        vector_store = ChromaVectorStore(
            chroma_collection=chroma_collection,
        )
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, embed_model=embed_model
        )

        query_engine = index.as_query_engine(llm=llm)

        response = query_engine.query(customer_query)
    except Exception as e:
        logger.error(f"Failed to query csv: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query csv",
        )

    return str(response)


def csv_pipeline_v2(csv_path: str, customer_query: str) -> str:
    """
    Query the csv file using the query pipeline
    """

    logger.debug(f"Reading csv file: {csv_path}")
    df = pd.read_csv(csv_path)

    instruction_str = (
        "1. Convert the query to executable Python code using Pandas.\n"
        "2. The final line of code should be a Python expression that can be called with the `eval()` function.\n"
        "3. The code should represent a solution to the query.\n"
        "4. PRINT ONLY THE EXPRESSION.\n"
        "5. Do not quote the expression.\n"
        f"6. The current timestamp is {datetime.utcnow()}.\n"
    )

    pandas_prompt_str = (
        "You are working with a pandas dataframe in Python.\n"
        "The name of the dataframe is `df`.\n"
        "This is the result of `print(df.head())`:\n"
        "{df_str}\n\n"
        "Follow these instructions:\n"
        "{instruction_str}\n"
        "Query: {query_str}\n\n"
        "Expression:"
    )
    response_synthesis_prompt_str = (
        "Given an input question, synthesize a response from the query results.\n"
        "Query: {query_str}\n\n"
        "Pandas Instructions (optional):\n{pandas_instructions}\n\n"
        "Pandas Output: {pandas_output}\n\n"
        "Response: "
    )

    pandas_prompt = PromptTemplate(pandas_prompt_str).partial_format(
        instruction_str=instruction_str, df_str=df.head(5)
    )
    pandas_output_parser = PandasInstructionParser(df)
    response_synthesis_prompt = PromptTemplate(response_synthesis_prompt_str)
    llm = OpenAI(model=Config.DEFAULT_OPENAI_MODEL)

    qp = QP(
        modules={
            "input": InputComponent(),
            "pandas_prompt": pandas_prompt,
            "llm1": llm,
            "pandas_output_parser": pandas_output_parser,
            "response_synthesis_prompt": response_synthesis_prompt,
            "llm2": llm,
        },
        verbose=False,
    )
    qp.add_chain(["input", "pandas_prompt", "llm1", "pandas_output_parser"])
    qp.add_links(
        [
            Link("input", "response_synthesis_prompt", dest_key="query_str"),
            Link("llm1", "response_synthesis_prompt", dest_key="pandas_instructions"),
            Link(
                "pandas_output_parser",
                "response_synthesis_prompt",
                dest_key="pandas_output",
            ),
        ]
    )
    # add link from response synthesis prompt to llm2
    qp.add_link("response_synthesis_prompt", "llm2")

    logger.debug("Running the Query Pipeline...")
    result = qp.run(
        query_str=customer_query,
    )

    response = result.message.content
    logger.debug(f"Query Pipeline response: {response}")

    return response
