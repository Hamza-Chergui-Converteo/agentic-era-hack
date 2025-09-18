
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

def generate_gso_recommendation(tool_context: ToolContext) -> str:
    companies = tool_context.state.get("companies_filtered", [])
    gso_analysis = tool_context.state.get("summary_best_brands_content", "")
    if not companies:
        return "No companies to generate recommendations for."
    if not gso_analysis:
        return "No GSO analysis found to base recommendations on."

    recommendations = []

    instruction = """You are a GSO (Global Search Optimization) expert. Your primary goal is to provide actionable recommendations to help a company improve its search engine ranking on a global scale.

You are provided with:
1. An analysis of top-ranking websites for a specific search query. This is the 'Competitor GSO Analysis'.
2. The URL of a company that wants to improve its ranking.

Based on the best practices from the Competitor GSO Analysis and a deep analysis of the company's URL, generate a set of recommendations.

Focus on **Global Search Optimization (GSO)**. While including general SEO is fine, your main focus should be on international aspects. The recommendations should be in markdown format and cover areas like:

- **International SEO Strategy:**
  - Use of `hreflang` tags for language and regional targeting.
  - URL structure for international sites (e.g., ccTLDs, subdomains, or subdirectories).
  - Geotargeting settings in search engine webmaster tools.

- **Content Localization:**
  - Translating content vs. localizing it to fit cultural nuances (e.g., currency, date formats, local idioms).
  - Keyword research for different languages and regions.
  - Creating culturally relevant content and imagery.

- **Global On-Page & Technical SEO:**
  - Optimizing meta tags, headings, and content for local keywords.
  - Ensuring the website is mobile-friendly and fast-loading for a global audience, considering varying internet speeds.
  - Structured data (Schema.org) that supports multiple languages.

- **International Off-Page SEO:**
  - Building backlinks from reputable sources within target countries.
  - Establishing brand authority and social signals in different regional markets.

Here is the Competitor GSO Analysis:
---
{gso_analysis}
---

Now, analyze the following company URL and provide GSO recommendations for it.
    """

    tools = [
      {"url_context": {}},
    ]

    for company in companies:
        company_url = company.get("url")
        if not company_url:
            continue

        prompt = instruction.format(gso_analysis=gso_analysis) + f"\nCompany URL to analyze: {company_url}"

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=GenerateContentConfig(tools=tools),
        )

        company_with_recommendation = company.copy()
        company_with_recommendation["gso_recommendation"] = response.text
        recommendations.append(company_with_recommendation)

    tool_context.state["recommendations"] = recommendations
    return json.dumps(recommendations, indent=2)

gso_improver = LlmAgent(
    name="gso_improver",
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    instruction=(
        "You are a GSO Improver (Global Search Optimization) expert. Your goal is to help companies improve their global search ranking.\n"
        "The state contains 'companies_filtered' (a list of companies to analyze) and 'summary_best_brands_content' (an analysis of top competitors).\n"
        "Call the `generate_gso_recommendation` tool to generate specific **Global Search Optimization (GSO)** recommendations for each company in 'companies_filtered', focusing on internationalization and localization.\n"
        "Return the result from the tool as your final answer in JSON format."
    ),
    tools=[generate_gso_recommendation],
    
)