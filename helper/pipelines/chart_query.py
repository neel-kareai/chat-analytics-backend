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


def extract_backticks_content(content: Any, lang: str = "") -> str:
    content = content.message.content
    extracted_content = re.search(
        r"```" + re.escape(lang) + "(.*)```", content, re.DOTALL
    )
    if extracted_content:
        return extracted_content.group(1)

    extracted_content = re.search(r"```(.*)```", content, re.DOTALL)
    if extracted_content:
        return extracted_content.group(1)

    return content


