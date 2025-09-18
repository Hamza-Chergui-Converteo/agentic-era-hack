
import os
import requests
import json
from google.adk.tools import google_search, ToolContext
from google.genai.types import GenerateContentConfig, UrlContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import LlmAgent
from google import genai
from bs4 import BeautifulSoup
from google.adk import Agent
from dotenv import load_dotenv
from pydantic import BaseModel, Field
load_dotenv()

# Initialize the generative model once and reuse it.
client = genai.Client()
model = os.getenv("MODEL", "gemini-2.5-flash")

def generate_gso_analysis(tool_context: ToolContext) -> str:
    """
    Analyzes the top 10 search results to generate a markdown summary
    explaining their high ranking for Global Search Optimization (GSO).
    """
    results = tool_context.state.get("top_10_results", [])
    if not results:
        return "No results to analyze."

    urls_for_context = [result.get("link") for result in results if result.get("link")]

    instruction = """You are a GSO Analyzer (Global Search Optimization). Your goal is to analyze the provided pages from the given URLs.
    Generate a detailed markdown report to explain why these brands are on top of Google search results.
    Consider SEO factors like keywords, content quality, page structure, user experience signals, and brand authority.
    Structure your report with a section for each URL, and a final summary of common themes.
    """

    prompt = instruction + "\n---Analyze these URLs:---\n" + "\n".join(urls_for_context)

    tools = [
      {"url_context": {}},
    ]

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=GenerateContentConfig(tools=tools),
    )

    summary = response.text
    tool_context.state["summary_best_brands_content"] = summary
    return summary

gso_analyzer = LlmAgent(
    name="GSO Analyzer",
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    instruction=(
        "You are a GSO Analyzer (Global Search Optimization). Your goal is to analyze the pages in the 'top_10_results' state variable.\n"
        "Call the `generate_gso_analysis` tool to generate a detailed markdown report explaining why these brands are top Google retrieved brands.\n"
        "Return the result from the tool as your final answer."
    ),
    tools=[generate_gso_analysis],
    output_key="summary_best_brands_content"
)