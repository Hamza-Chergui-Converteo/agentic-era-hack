import requests
from html_to_markdown import convert_to_markdown



def scrap_page(url: str) -> dict:
    """
    Retrieves the content of a page from a given URL.

    Args:
        url (str): The URL of the page to retrieve.

    Returns:
        dict: A dictionary with the status and either the page content in markdown
              or an error message.
    """
    try:
        response = requests.get(url)
        return {"status" : "success", "content" : convert_to_markdown(response.text)}
    except Exception as ex:
        return {"status" : "error", "error" : str(ex)}