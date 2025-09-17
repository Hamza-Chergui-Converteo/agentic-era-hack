import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field


# Charger le .env
load_dotenv()

# --- Tool : Recherche Google via SerpAPI ---
def search_google(query: str) -> str:
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return "Erreur: la clé SERPAPI_KEY n'est pas définie!"

    search = GoogleSearch({
        "q": query,
        "hl": "fr",
        "gl": "fr",
        "num": 10,
        "api_key": api_key
    })
    results = search.get_dict()
    organic_results = results.get("organic_results", [])

    if not organic_results:
        return "Aucun résultat trouvé!"

    # Formatage avec rank (position réelle)
    top_results = []
    for r in organic_results[:10]:
        rank = r.get("position", "?")
        title = r.get("title", "")
        link = r.get("link", "")
        snippet = r.get("snippet", "")
        # top_results.append(f"{rank}. {title}\n   {link}\n   {snippet}")
        top_results.append(link)
    return "\n\n".join(top_results)

# --- Agent configuré ---


class SearchAgentOutput(BaseModel):
    search_results: list[str] = Field(description="List of URLs obtained from a Google search")

search_agent = LlmAgent(
    name="search_agent",
    model=os.getenv("MODEL", "gemini-2.0-flash"),
    description=(
        "An intelligent research assistant capable of finding and summarizing "
        "the top 10 Google search results on any requested topic. "
        "It provides clear, structured, and useful answers!"
    ),
    instruction="""
Your role is to act as a research expert!
1. When a question involves an internet search, use the GoogleSearchTool.
2. Summarize the results found in a concise and readable manner.
3. Highlight important points or common trends among the results.
4. If a search is not necessary, answer using your own knowledge.
5. Structure your answers with headings, bullet points, or short paragraphs for clarity.
6. Always end your sentences with an exclamation mark!
""",
    tools=[search_google],
    output_key="urls_list"
)


