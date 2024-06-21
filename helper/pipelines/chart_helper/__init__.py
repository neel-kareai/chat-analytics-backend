from typing import Any
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
