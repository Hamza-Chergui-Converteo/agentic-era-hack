import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
from google.adk.agents import LlmAgent


# Charger le .env
load_dotenv()

# --- Tool : Recherche Google via SerpAPI ---
def search_google(query: str) -> list[dict]:
    """Performs a Google search using SerpAPI and returns the top 100 organic result URLs.

    Args:
        query: The search query string.

    Raises:
        ValueError: If the SERPAPI_KEY environment variable is not set.
        Exception: If the SerpAPI call returns an error.

    Returns:
        A string containing the URLs of the top 10 search results,
        separated by double newlines. Returns a message if no results are found.
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError("SERPAPI_KEY environment variable not set!")
    top_100_results = []
    for i in range(0,100,10):
        search = GoogleSearch({
            "q": query,
            "hl": "en",
            "gl": "fr",
            "start": i,
            "num": 10,
            "api_key": api_key
        })
        results = search.get_dict()
        if "error" in results:
            raise Exception(f"SerpAPI error: {results['error']}")

        organic_results = results.get("organic_results", [])
        if not organic_results:
            return "No organic results found for the query."
        # Formatage avec rank (position réelle)
        
        for r in organic_results:
            result_infos = {'postion': r.get("position"),
            'title': r.get("title"),
            'link': r.get("link"),
            'snippet': r.get("snippet"),
            'snippet_highlighted_words': r.get("snippet_highlighted_words")
            }
            top_100_results.append(result_infos)
    # sort the list top result by position and remove duplications
    top_100_results = sorted(top_100_results, key=lambda x: x['postion'])
    return top_100_results

# --- Agent configuré ---

search_agent = LlmAgent(
    name="search_agent",
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    description=(
        "An intelligent research assistant capable of finding and summarizing "
        "the top 100 Google search results on any requested topic. "
        "It provides clear, structured, and useful answers!"
    ),
    instruction="""
    Your role is to act as a research expert.
    Take the user request and using search_google retrieve top_100_results
    """,
    tools=[search_google],
    output_key="top_100_results"
)
