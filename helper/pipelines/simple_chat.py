from datetime import datetime
from config import Config
from logger import logger
from helper.openai import openai_chat_completion_with_retry
from helper.pipelines import post_processed_html_response
from llama_index.core.query_pipeline import QueryPipeline, InputComponent
from llama_index.storage.chat_store.redis import RedisChatStore
from llama_index.core.memory import ChatMemoryBuffer
from typing import Any, Dict, List, Optional
from llama_index.core.bridge.pydantic import Field
from llama_index.core.llms import ChatMessage
from llama_index.core.query_pipeline import CustomQueryComponent
from llama_index.llms.openai import OpenAI


class SimpleResponseWithChatHistory(CustomQueryComponent):
    llm: OpenAI = Field(..., description="LLM")
    system_prompt: Optional[str] = Field(
        default=None, description="System prompt to use for the LLM"
    )
    context_prompt: str = Field(
        description="Context prompt to use for the LLM",
    )

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        # NOTE: this is OPTIONAL but we show you where to do validation as an example
        return input

    @property
    def _input_keys(self) -> set:
        """Input keys dict."""
        # NOTE: These are required inputs. If you have optional inputs please override
        # `optional_input_keys_dict`
        return {"chat_history", "query_str"}

    @property
    def _output_keys(self) -> set:
        return {"response"}

    def _prepare_context(
        self,
        chat_history: List[ChatMessage],
        query_str: str,
    ) -> List[ChatMessage]:

        formatted_context = self.context_prompt.format(query_str=query_str)
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

        prepared_context = self._prepare_context(chat_history, query_str)

        response = self.llm.chat(prepared_context)

        return {"response": response}

    async def _arun_component(self, **kwargs: Any) -> Dict[str, Any]:
        """Run the component asynchronously."""
        # NOTE: Optional, but async LLM calls are easy to implement
        chat_history = kwargs["chat_history"]
        query_str = kwargs["query_str"]

        prepared_context = self._prepare_context(chat_history, query_str)

        response = await self.llm.achat(prepared_context)

        return {"response": response}


def simple_chat_pipeline(
    customer_query: str, chat_uuid: str, model: str = Config.DEFAULT_OPENAI_MODEL
) -> str:
    """
    Query the csv file using the query pipeline.

    Args:
        customer_query (str): The query requested by the customer.
        model (str, optional): The OpenAI model to use for generating the response. Defaults to Config.DEFAULT_OPENAI_MODEL.

    Returns:
        str: The response generated by the OpenAI model.
    """
    chat_store = RedisChatStore(redis_url=Config.REDIS_STORE_URL)
    chat_memory = ChatMemoryBuffer.from_defaults(
        chat_store=chat_store, chat_store_key=chat_uuid, token_limit=5000
    )

    llm = OpenAI(model=model, temperature=0.0, top_p=0.2, api_key=Config.OPENAI_API_KEY)

    response_component = SimpleResponseWithChatHistory(
        llm=llm,
        context_prompt="""
            The customer has requested the following query:
            {query_str}
            response:
            """,
        system_prompt="""
            You are an assistance with data analyst and database expertise. You should
            answer the customer query and be helpful. Your response should always be in HTML 
            format inside a <div> tag. Make sure to include any inline code with <pre> tag and multiline code within <code> tag.
            """,
    )
    input_component = InputComponent()
    chat_history = chat_memory.get()
    logger.debug(f"Chat history: {chat_history}")

    p = QueryPipeline(verbose=True)
    p.add_modules(
        {
            "input": input_component,
            "response_component": response_component,
        }
    )
    p.add_link(
        "input",
        "response_component",
        src_key="query_str",
        dest_key="query_str",
    )
    p.add_link(
        "input", "response_component", src_key="chat_history", dest_key="chat_history"
    )

    response = p.run(query_str=customer_query, chat_history=chat_history)

    # update the memory
    user_msg = ChatMessage(role="user", content=customer_query)
    chat_memory.put(user_msg)
    chat_memory.put(response.message)

    return post_processed_html_response(response.message.content)
