from google.adk.agents import Agent
from google.adk.tools import google_search
from .tools import scrap_page


root_agent = Agent(
    name="Agent_search_prospects",
    model="gemini-2.0-flash",
    instruction="""
    Retrieve the URL provided and use the scrap_page tool to retrieve the content of the page.
    """,
    tools=[scrap_page],
)
