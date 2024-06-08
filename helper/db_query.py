from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.engine import reflection
from datetime import datetime
from openai import OpenAI
from config import Config
from logger import logger
import re


def get_db_connection_string(db_type: str,
                             db_user: str,
                             db_password: str,
                             db_host: str,
                             db_port: int,
                             db_name: str
                             ) -> str:
    """
        Get the database connection string
    """

    if db_type == "mysql":
        db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == "postgres":
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == "sqlite":
        db_url = f"sqlite:///{db_name}"
    else:
        raise ValueError("Invalid database type")

    return db_url


def get_db_schema(db_url: str
                  ) -> str:
    """
        Get the schema of the database
    """

    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    inspector = reflection.Inspector.from_engine(engine)

    db_schema = ""
    for table_name, table in metadata.tables.items():
        db_schema += f"\n\nTable: {table_name}\n"
        db_schema += "-" * 30 + '\n'
        foreign_keys = inspector.get_foreign_keys(table_name)
        fk_dict = {fk['constrained_columns'][0]: fk for fk in foreign_keys}
        for column in table.columns:
            if column.name in fk_dict:
                fk = fk_dict[column.name]
                referenced_table = fk['referred_table']
                referenced_column = fk['referred_columns'][0]
                db_schema += f"  {column.name} ({column.type}) [Foreign Key: {referenced_table}.{referenced_column}]\n"
            else:
                db_schema += f"  {column.name} ({column.type})\n"

    return db_schema


def generate_sql_query(query: str, db_schema: str) -> str:
    """
        Process the customer query
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
        model=Config.DEFAULT_OPENAI_MODEL,
        temperature=0.0,
        top_p=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query_prompt},
        ]
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


def db_refine_query_result(query: str, query_result: str) -> str:
    """
        Refine the query result using OpenAI
    """

    system_prompt = f"""
    You are a data analyst and database expert. You have been given a task to
    see the user query and query result and refine the query result to make it more
    presentable to the user.
"""

    query_prompt = f"""
    The customer has requested the following query:
    {query}
    The query result is as follows:
    {query_result}
    Refine the query result to make it more presentable.
    Refined Response:
"""

    openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

    response = openai_client.chat.completions.create(
        model=Config.DEFAULT_OPENAI_MODEL,
        temperature=0.0,
        top_p=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query_prompt},
        ]
    )

    response_text = response.choices[0].message.content
    logger.debug(f"OpenAI response: {response_text}")

    return response_text


def db_config_pipeline(db_type: str, db_config: dict, query: str) -> str:
    """
        Pipeline to process the customer query
    """
    logger.debug("Fetching database schema")

    db_url = get_db_connection_string(
        db_type=db_type,
        db_user=db_config['user'],
        db_password=db_config['password'],
        db_host=db_config['hostname'],
        db_port=db_config['port'],
        db_name=db_config['dbname']
    )

    db_schema = get_db_schema(db_url)

    logger.debug("Processing customer query")
    sql_query = generate_sql_query(query, db_schema)
    logger.debug(f"Generated SQL query: {sql_query}")

    logger.debug("Executing SQL query")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        query_result = "\n".join([str(row) for row in result.fetchall()])

    logger.debug(f"Query result: {query_result}")
    logger.debug("Refining query result")

    refined_query_result = db_refine_query_result(query, query_result)

    logger.debug(f"Refined query result: {refined_query_result}")

    return refined_query_result, sql_query
