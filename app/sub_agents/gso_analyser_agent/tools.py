import requests
from html_to_markdown import convert_to_markdown



def scrap_page(url: str):
    """
    Retrieves the content of a page from a given URL.

    Args:
        url (str): The URL of the page to retrieve.

    Returns:
        str: The content of the page as a string (in markdown format).
    """
    try:
        response = requests.get(url)
        return {"status" : "success", "content" : convert_to_markdown(r.text)}
    except Exception as ex:
        return {"status" : "error", "error" : str(ex)}
   