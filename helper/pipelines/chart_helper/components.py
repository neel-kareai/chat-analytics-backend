import pandas as pd
from typing import Any, Dict, List, Optional

from llama_index.core.query_pipeline import (
    QueryPipeline,
    InputComponent,
    FunctionComponent,
    CustomQueryComponent,
)
from llama_index.core import PromptTemplate
from datetime import datetime
import time
from llama_index.storage.chat_store.redis import RedisChatStore
from llama_index.core.memory import ChatMemoryBuffer
from pydantic import RootModel, BaseModel, Field
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI
from llama_index.legacy.llms.llm import LLM
import json
import pandas as pd
import re


class ChartTypeSelector(CustomQueryComponent):
    llm: Any = Field(..., description="LLM")
    system_prompt: Optional[str] = Field(
        default=None, description="System prompt to use for the LLM"
    )
    context_prompt: Optional[str] = Field(
        description="Context prompt to use for the LLM",
    )

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        return input

    @property
    def _input_keys(self) -> set:
        """Input keys dict."""
        return {"chat_history", "query_str", "data_schema"}

    @property
    def _output_keys(self) -> set:
        return {"chart_type"}

    def _prepare_context(
        self,
        chat_history: List[ChatMessage],
        query_str: str,
        data_schema: str,
    ) -> List[ChatMessage]:

        formatted_context = self.context_prompt.replace(
            "{query_str}", query_str
        ).replace("{data_schema}", data_schema)
        user_message = ChatMessage(role="user", content=formatted_context)

        chat_history.append(user_message)

        if self.system_prompt is not None:
            chat_history = [
                ChatMessage(role="system", content=self.system_prompt)
            ] + chat_history

        return chat_history

    def _run_component(self, **kwargs) -> Dict[str, Any]:
        """Run the component."""
        chat_history = kwargs["chat_history"]
        query_str = kwargs["query_str"]
        data_schema = kwargs["data_schema"]

        prepared_context = self._prepare_context(chat_history, query_str, data_schema)
        response = self.llm.chat(prepared_context)
        return {"chart_type": response}

    async def _arun_component(self, **kwargs: Any) -> Dict[str, Any]:
        """Run the component asynchronously."""
        chat_history = kwargs["chat_history"]
        query_str = kwargs["query_str"]
        data_schema = kwargs["data_schema"]

        prepared_context = self._prepare_context(chat_history, query_str, data_schema)
        response = await self.llm.achat(prepared_context)

        return {"chart_type": response}


def chart_data_schema_tool(chart_type: Any) -> str:
    chart_info = json.loads(extract_backticks_content(chart_type, "json"))
    print(chart_info)
    chart_type_data = chart_info["chart_type"]
    chart_schemas = {}
    chart_schemas["bar"] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Generalized Bar Chart Data Schema",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The label or name for the data point",
                },
                "values": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "number",
                        "description": "A numerical value for a specific metric",
                    },
                    "description": "A set of key-value pairs where the key is the metric name and the value is the numerical data",
                },
            },
            "required": ["name", "values"],
        },
    }
    chart_schemas["area"] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Generalized Area Chart Data Schema",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The label or name for the data point",
                },
                "values": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "number",
                        "description": "A numerical value for a specific metric",
                    },
                    "description": "A set of key-value pairs where the key is the metric name and the value is the numerical data",
                },
            },
            "required": ["name", "values"],
        },
    }
    chart_schemas["line"] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Generalized Line Chart Data Schema",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The label or name for the data point",
                },
                "values": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "number",
                        "description": "A numerical value for a specific metric",
                    },
                    "description": "A set of key-value pairs where the key is the metric name and the value is the numerical data",
                },
            },
            "required": ["name", "values"],
        },
    }
    chart_schemas["radar"] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Generalized Radar Chart Data Schema",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The label or name for the data point",
                },
                "values": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "number",
                        "description": "A numerical value for a specific metric",
                    },
                    "description": "A set of key-value pairs where the key is the metric name and the value is the numerical data",
                },
            },
            "required": ["name", "values"],
        },
    }
    chart_schemas["pie"] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Generalized Pie Chart Data Schema",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The label or name for the data point",
                },
                "values": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "number",
                        "description": "A numerical value for a specific metric",
                    },
                    "description": "A set of key-value pairs where the key is the metric name and the value is the numerical data",
                },
            },
            "required": ["name", "values"],
        },
    }
    return f"{chart_schemas[chart_type_data]}"


class ChartDataGeneratorViaPython(CustomQueryComponent):
    llm: Any = Field(..., description="LLM")
    system_prompt: Optional[str] = Field(
        default=None, description="System prompt to use for the LLM"
    )
    context_prompt: Optional[str] = Field(
        description="Context prompt to use for the LLM",
    )

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        return input

    @property
    def _input_keys(self) -> set:
        """Input keys dict."""
        return {
            "chat_history",
            "query_str",
            "chart_type",
            "chart_schema",
            "data_schema",
        }

    @property
    def _output_keys(self) -> set:
        return {"python_code"}

    def _prepare_context(
        self,
        chat_history: List[ChatMessage],
        query_str: str,
        chart_type: str,
        chart_schema: str,
        data_schema: str,
    ) -> List[ChatMessage]:

        formatted_context = (
            self.context_prompt.replace("{query_str}", query_str)
            .replace("{chart_type}", chart_type)
            .replace("{chart_schema}", chart_schema)
            .replace("{data_schema}", data_schema)
        )
        user_message = ChatMessage(role="user", content=formatted_context)

        chat_history.append(user_message)

        if self.system_prompt is not None:
            chat_history = [
                ChatMessage(role="system", content=self.system_prompt)
            ] + chat_history

        return chat_history

    def _run_component(self, **kwargs) -> Dict[str, Any]:
        """Run the component."""
        chat_history = kwargs["chat_history"]
        query_str = kwargs["query_str"]
        chart_type = kwargs["chart_type"]
        chart_schema = kwargs["chart_schema"]
        data_schema = kwargs["data_schema"]

        chart_type = extract_backticks_content(chart_type, "json")
        chart_type = json.loads(chart_type)["chart_type"]

        prepared_context = self._prepare_context(
            chat_history, query_str, chart_type, chart_schema, data_schema
        )
        response = self.llm.chat(prepared_context)

        return {"python_code": response}

    async def _arun_component(self, **kwargs: Any) -> Dict[str, Any]:
        """Run the component asynchronously."""
        chat_history = kwargs["chat_history"]
        query_str = kwargs["query_str"]
        chart_type = kwargs["chart_type"]
        chart_schema = kwargs["chart_schema"]
        data_schema = kwargs["data_schema"]

        chart_type = extract_backticks_content(chart_type, "json")
        chart_type = json.loads(chart_type)["chart_type"]

        prepared_context = self._prepare_context(
            chat_history, query_str, chart_type, chart_schema, data_schema
        )
        response = await self.llm.achat(prepared_context)

        return {"python_code": response}


class ChartDataCodeExecutor(CustomQueryComponent):
    df: Any = Field(..., description="The dataframe variable")

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        return input

    @property
    def _input_keys(self) -> set:
        """Input keys dict."""
        return {"python_code"}

    @property
    def _output_keys(self) -> set:
        return {"chart_data"}

    def _run_component(self, **kwargs) -> Dict[str, Any]:
        """Run the component."""
        python_code = kwargs["python_code"]
        global_dict = {"df": self.df}
        exec(extract_backticks_content(python_code, "python"), global_dict)

        response = global_dict["chart_data"]

        return {"chart_data": response}

    async def _arun_component(self, **kwargs: Any) -> Dict[str, Any]:
        """Run the component asynchronously."""
        python_code = kwargs["python_code"]
        global_dict = {"df": self.df}
        exec(extract_backticks_content(python_code, "python"), global_dict)

        response = global_dict["chart_data"]

        return {"chart_data": response}


