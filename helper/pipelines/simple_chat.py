from datetime import datetime
from openai import OpenAI
from config import Config
from logger import logger
import re


def simple_chat_pipeline(
    customer_query: str, model: str = Config.DEFAULT_OPENAI_MODEL
) -> str:
    """
    Query the csv file using the query pipeline.

    Args:
        customer_query (str): The query requested by the customer.
        model (str, optional): The OpenAI model to use for generating the response. Defaults to Config.DEFAULT_OPENAI_MODEL.

    Returns:
        str: The response generated by the OpenAI model.
    """

    openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

    system_prompt = f"""
    You are an assistance with data analyst and database expertise. You should
    answer the customer query and be helpful.
    """

    query_prompt = f"""
    The customer has requested the following query:
    {customer_query}
    response:
    """

    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query_prompt},
        ],
    )

    response_text = response.choices[0].message.content

    return response_text
