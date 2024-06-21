import pandas as pd
from typing import Any, Dict, List, Optional

from llama_index.core.query_pipeline import (
    QueryPipeline,
    InputComponent,
    FunctionComponent,
)
from llama_index.storage.chat_store.redis import RedisChatStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI
import json
import pandas as pd
import random, os
from datetime import datetime
from helper.pipelines.chart_helper.components import (
    ChartTypeSelector,
    ChartDataGeneratorViaPython,
    ChartDataCodeExecutor,
    CaptionGenerator,
    chart_data_schema_tool,
    chart_validator_tool,
)
from db.queries.user_documents import UserDocumentQuery
from db.queries.chart import ChartQuery
from db import get_db
from helper.aws_s3 import download_from_s3
from helper.pipelines.chart_helper import extract_backticks_content
from config import Config


def chart_query_pipeline(
    query_str: str,
    chat_uuid: str,
    query_type: str,
    data_source_id: int,
    model: str = Config.DEFAULT_OPENAI_MODEL,
) -> Dict[str, Any]:
    """
    Query pipeline for chart queries
    """

    if query_type not in ["chart", "chart_data"]:
        raise ValueError("Invalid query type")

    user_doc = UserDocumentQuery.get_user_document_by_id(data_source_id)
    if not user_doc:
        raise ValueError("Invalid data source id")

    file_s3_url = user_doc.document_url
    object_url = file_s3_url.split("amazonaws.com/")[-1]
    file_extension = object_url.split(".")[-1]
    file_name = random.randbytes(10).hex() + "." + file_extension
    temp_file_path = f"/tmp/{file_name}"

    if not download_from_s3(object_url, temp_file_path):
        raise Exception("Failed to download the file from s3")

    if file_extension == "csv":
        df = pd.read_csv(temp_file_path)
    else:
        df = pd.read_excel(temp_file_path, sheet_name=None)

    chat_store = RedisChatStore(Config.REDIS_STORE_URL)
    chat_memory = ChatMemoryBuffer.from_defaults(
        chat_store=chat_store, chat_store_key=chat_uuid, token_limit=5000
    )
    chat_history = chat_memory.get()
    llm = OpenAI(model=model)

    input_component = InputComponent()
    chart_type_selector_component = ChartTypeSelector(
        llm=llm,
        context_prompt=(
            "1. Your task is to analyze user query and given data schema.\n"
            "2. You need to pick the best chart type which can be used for the given user query.\n"
            "3. Only following chart types are allowed: 'area', 'bar', 'line', 'pie', 'radar'.\n"
            "4. You must output a JSON with a key 'chart_type' with the value of best chart which fits on the user query."
            '5. Makes sure to have the following output schema: {"chart_type":"<The best chart type which fits on the user query>"}\n'
            "6. You should enclose JSON within 3 backticks.\n"
            f"7. The current timestamp is {datetime.utcnow()}.\n"
            "Data Schema:\n"
            "{data_schema}\n"
            "User Query:\n"
            "{query_str}\n"
            "Response:\n"
        ),
    )
    chart_data_schema_tool_component = FunctionComponent(
        fn=chart_data_schema_tool, output_key="chart_schema"
    )
    chart_data_generator_component = ChartDataGeneratorViaPython(
        llm=llm,
        context_prompt=(
            "1. You are a expert developer in python and data science\n"
            "2. Your task to write a python code which generate the desired chart data with given schema so that it can be used for rendering.\n"
            "3. The python should be generated in such a way it can executed using python's in-built `exec()` function.\n"
            "4. You should not use print statement.\n"
            "5. You should store the final chart data into `chart_data` variable so that it can be captured after `exec()` call.\n"
            "6. You are allowed to use pandas library and the name of the dataframe is `df`. Its context will be provided later through `exec()`.\n"
            "7. You should output the Python code enclosed in 3 backticks.\n"
            f"8. The current timestamp is {datetime.utcnow()}.\n"
            "User Query: \n"
            "{query_str}\n"
            "`df.head()` Output: \n"
            "{data_schema}\n"
            "Chart Type: {chart_type}\n"
            "Chart Data Structure Schema: \n"
            "{chart_schema}\n"
            "Python code:\n"
        ),
    )
    chart_data_code_executor_component = ChartDataCodeExecutor(df=df)
    chart_validator_tool_component = FunctionComponent(
        fn=chart_validator_tool, output_key="validated_chart_data"
    )
    caption_generator_component = CaptionGenerator(
        llm=llm,
        context_prompt=(
            "1. You are very good writer and response synthesier.\n"
            "2. Your task is to generate caption for the charts requested by the user.\n"
            "3. You will be given user query and you need to generate the caption for the same.\n"
            "4. Assume that the appropiate chart has already been generated for the user."
            "5. You should output a JSON enclosed with 3 backticks with a key 'caption'."
            f"6. The current timestamp is {datetime.utcnow()}.\n"
            "User Query:\n"
            "{query_str}\n"
            "Caption: \n"
        ),
        system_prompt=None,
    )

    p = QueryPipeline(verbose=True)

    p.add_modules(
        {
            "input_component": input_component,
            "chart_type_selector_component": chart_type_selector_component,
            "chart_data_schema_tool_component": chart_data_schema_tool_component,
            "chart_data_generator_component": chart_data_generator_component,
            "chart_data_code_executor_component": chart_data_code_executor_component,
            "chart_validator_tool_component": chart_validator_tool_component,
            "caption_generator_component": caption_generator_component,
        }
    )

    p.add_link(
        "input_component",
        "chart_type_selector_component",
        src_key="query_str",
        dest_key="query_str",
    )
    p.add_link(
        "input_component",
        "chart_type_selector_component",
        src_key="chat_history",
        dest_key="chat_history",
    )
    p.add_link(
        "input_component",
        "chart_type_selector_component",
        src_key="data_schema",
        dest_key="data_schema",
    )

    p.add_link(
        "chart_type_selector_component",
        "chart_data_schema_tool_component",
        src_key="chart_type",
        dest_key="chart_type",
    )

    p.add_link(
        "input_component",
        "chart_data_generator_component",
        src_key="query_str",
        dest_key="query_str",
    )
    p.add_link(
        "input_component",
        "chart_data_generator_component",
        src_key="chat_history",
        dest_key="chat_history",
    )
    p.add_link(
        "input_component",
        "chart_data_generator_component",
        src_key="data_schema",
        dest_key="data_schema",
    )
    p.add_link(
        "chart_type_selector_component",
        "chart_data_generator_component",
        src_key="chart_type",
        dest_key="chart_type",
    )
    p.add_link(
        "chart_data_schema_tool_component",
        "chart_data_generator_component",
        src_key="chart_schema",
        dest_key="chart_schema",
    )

    p.add_link(
        "chart_data_generator_component",
        "chart_data_code_executor_component",
        src_key="python_code",
        dest_key="python_code",
    )

    p.add_link(
        "chart_type_selector_component",
        "chart_validator_tool_component",
        src_key="chart_type",
        dest_key="chart_type",
    )
    p.add_link(
        "chart_data_code_executor_component",
        "chart_validator_tool_component",
        src_key="chart_data",
        dest_key="chart_data",
    )

    p.add_link(
        "input_component",
        "caption_generator_component",
        src_key="query_str",
        dest_key="query_str",
    )
    p.add_link(
        "input_component",
        "caption_generator_component",
        src_key="chat_history",
        dest_key="chat_history",
    )
    p.add_link(
        "chart_validator_tool_component",
        "caption_generator_component",
        src_key="validated_chart_data",
        dest_key="validated_chart_data",
    )

    result, intermediates = p.run_with_intermediates(
        query_str=query_str, chat_history=chat_history, data_schema=f"{df.head()}"
    )

    os.remove(temp_file_path)

    chart_type_info = json.loads(
        extract_backticks_content(
            intermediates["chart_type_selector_component"].outputs["chart_type"], "json"
        )
    )
    python_code = extract_backticks_content(
        intermediates["chart_data_generator_component"].outputs["python_code"], "python"
    )

    chart_data = intermediates["chart_validator_tool_component"].outputs[
        "validated_chart_data"
    ]
    caption_info = json.loads(
        extract_backticks_content(
            intermediates["caption_generator_component"].outputs["caption"], "json"
        )
    )
    # save the chart
    chart = ChartQuery.create_chart(
        chat_uuid=chat_uuid,
        chart_type=chart_type_info["chart_type"],
        code=python_code,
        data=chart_data,
        caption=caption_info["caption"],
    )

    db = get_db()

    # update the memory
    chat_memory.put(ChatMessage(role="user", content=query_str))
    response_message = ChatMessage(
        role="assistant", content=result.message.content, chart_uuid={"chart_uuid": str(chart.uuid)}
    )
    chat_memory.put(response_message)
