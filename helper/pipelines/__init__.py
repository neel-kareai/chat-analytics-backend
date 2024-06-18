import re


def post_processed_html_response(response: str) -> str:
    """
    Extracts processed HTML content from the given response.

    Args:
        response (str): The response string to extract processed HTML from.

    Returns:
        str: The extracted processed HTML content, if found. Otherwise, returns the original response.
    """

    processed_html = re.search(r"```html(.*)```", response, re.DOTALL)
    if processed_html:
        return processed_html.group(1)

    processed_html = re.search(r"```(.*)```", response, re.DOTALL)
    if processed_html:
        return processed_html.group(1)

    return response
