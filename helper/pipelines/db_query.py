from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.engine import reflection
from datetime import datetime
from openai import OpenAI
from config import Config
from logger import logger
import re


def get_db_connection_string(
    db_type: str,
    db_user: str,
    db_password: str,
    db_host: str,
    db_port: int,
    db_name: str,
) -> str:
    """
    Get the database connection string.

    Args:
        db_type (str): The type of the database (e.g., "mysql", "postgres", "sqlite").
        db_user (str): The username for the database connection.
        db_password (str): The password for the database connection.
        db_host (str): The host address of the database server.
        db_port (int): The port number of the database server.
        db_name (str): The name of the database.

    Returns:
        str: The database connection string.

    Raises:
        ValueError: If an invalid database type is provided.
    """

    if db_type == "mysql":
        db_url = (
            f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
    elif db_type == "postgres":
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == "sqlite":
        db_url = f"sqlite:///{db_name}"
    else:
        raise ValueError("Invalid database type")

    return db_url


def get_db_schema(db_url: str) -> str:
    """
    Get the schema of the database.

    Args:
        db_url (str): The URL of the database.

    Returns:
        str: The schema of the database.

    """
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    inspector = reflection.Inspector.from_engine(engine)

    db_schema = ""
    for table_name, table in metadata.tables.items():
        db_schema += f"\n\nTable: {table_name}\n"
        db_schema += "-" * 30 + "\n"
        foreign_keys = inspector.get_foreign_keys(table_name)
        fk_dict = {fk["constrained_columns"][0]: fk for fk in foreign_keys}
        for column in table.columns:
            if column.name in fk_dict:
                fk = fk_dict[column.name]
                referenced_table = fk["referred_table"]
                referenced_column = fk["referred_columns"][0]
                db_schema += f"  {column.name} ({column.type}) [Foreign Key: {referenced_table}.{referenced_column}]\n"
            else:
                db_schema += f"  {column.name} ({column.type})\n"

    return db_schema


def generate_sql_query(query: str, db_schema: str, model: str) -> str:
    """
    Generates an SQL query based on the given prompt and user query using the OpenAI GPT-3 model.

    Args:
        query (str): The user query.
        db_schema (str): The database schema.
        model (str): The OpenAI GPT-3 model to use.

    Returns:
        str: The generated SQL query.

    """

    system_prompt = f"""
    You are a data analyst and database expert. You have been given a task to
    write a query to extract the information from the database. The time is now 
    {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}. You have to write sql query enclosed
    in triple backticks.
"""
    query_prompt = f"""
    The customer has requested the following query:
    {query}
    The database schema is as follows:
    {db_schema}
    Write a SQL query to extract the information from the database.
    SQL query:
"""

    openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

    response = openai_client.chat.completions.create(
        model=model,
        temperature=0.0,
        top_p=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query_prompt},
        ],
    )

    response_text = response.choices[0].message.content
    logger.debug(f"OpenAI response: {response_text}")

    # assuming we have received sql in ```sql``` format
    sql_query = re.search(r"```sql(.*)```", response_text, re.DOTALL)
    if sql_query:
        return sql_query.group(1)

    # assuming we have received sql in ``` ``` format
    sql_query = re.search(r"```(.*)```", response_text, re.DOTALL)
    if sql_query:
        return sql_query.group(1)

    # assuming we have received sql in plain text format
    sql_query = response_text

    return sql_query


def db_refine_query_result(query: str, query_result: str, model: str) -> str:
    """
    Refines the query result by converting it into a more readable format using OpenAI's chat completions.

    Args:
        query (str): The user query.
        query_result (str): The query result.
        model (str): The OpenAI model to use for chat completions.

    Returns:
        str: The refined query result.

    """
    system_prompt = f"""
    You are a data analyst and database expert bot. You have been given a task to
    see the user query and query result and convert it into a more readable format.
"""

    query_prompt = f"""
    The customer has requested the following query:
    {query}
    The query result is as follows:
    {query_result}
    Combine the result for more readability.
    response:
"""

    openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

    response = openai_client.chat.completions.create(
        model=model,
        temperature=0.0,
        top_p=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query_prompt},
        ],
    )

    response_text = response.choices[0].message.content
    logger.debug(f"OpenAI response: {response_text}")

    return response_text


def db_config_pipeline(
    db_type: str, db_config: dict, query: str, model: str = Config.DEFAULT_OPENAI_MODEL
) -> str:
    """
    Executes a database query pipeline.

    Args:
        db_type (str): The type of the database.
        db_config (dict): The configuration details for the database.
        query (str): The query to be executed.
        model (str, optional): The OpenAI model to be used for query generation. Defaults to Config.DEFAULT_OPENAI_MODEL.

    Returns:
        tuple: A tuple containing the refined query result and the generated SQL query.

    """
    logger.debug("Fetching database schema")

    db_url = get_db_connection_string(
        db_type=db_type,
        db_user=db_config["user"],
        db_password=db_config["password"],
        db_host=db_config["hostname"],
        db_port=db_config["port"],
        db_name=db_config["dbname"],
    )

    db_schema = get_db_schema(db_url)

    logger.debug("Processing customer query")
    sql_query = generate_sql_query(query, db_schema, model)
    logger.debug(f"Generated SQL query: {sql_query}")

    logger.debug("Executing SQL query")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        # check for empty result
        if result.rowcount == 0:
            query_result = "No results found"
        else:
            query_result = "\n".join([str(row) for row in result.fetchall()])

    logger.debug(f"Query result: {query_result}")
    logger.debug("Refining query result")

    refined_query_result = db_refine_query_result(query, query_result, model)

    logger.debug(f"Refined query result: {refined_query_result}")

    return refined_query_result, sql_query
