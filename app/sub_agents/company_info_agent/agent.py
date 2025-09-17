
import os
import requests
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import LlmAgent
from google import genai
from bs4 import BeautifulSoup
from google.adk import Agent
from dotenv import load_dotenv
load_dotenv()


def fetch_page_content(url: str) -> str:
    """Fetches and extracts text content from a web page.
    
    Args:
        url: Absolute URL to fetch content from.
    Returns:
        Extracted text content from the page, truncated to 3000 characters.
    """
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (compatible; SEOAgent/1.0)"})
        if resp.status_code >= 400 or not resp.text:
            return ""
    except Exception:
        return ""

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove non-content elements
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Truncate to keep token usage low
        return text[:3000]
    except Exception:
        return ""


# Create a specialized agent for product page detection
product_page_detection_agent = LlmAgent(
    name="product_page_detector",
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    instruction=(
        "You are a specialist in identifying company product pages and official company websites. "
        "Analyze the provided URL and page content to determine if it represents a company product page "
        "(e.g., shows products, describes company offerings) or an official company homepage. "
        "Consider factors like: product listings, company information, service descriptions, "
        "contact information, about pages, and overall website structure. "
        "Respond with 'yes' if it's a company product page or homepage, 'no' otherwise."
    ),
    description="Specialized agent for detecting company product pages and official websites",
    tools=[fetch_page_content]
)

# Create a specialized agent for Google search
google_search_agent = LlmAgent(
    name="google_searcher",
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    instruction=(
        "You are a Google search specialist. When given a search query, use the google_search tool "
        "to find relevant information. Focus on finding accurate, up-to-date information about "
        "companies, including their names, employee counts, contact information, and other relevant details. "
        "Provide clear, structured responses based on the search results."
    ),
    description="Specialized agent for performing Google searches and extracting company information",
    tools=[google_search]
)

# Wrap the agents as tools using AgentTool
is_product_page_tool = AgentTool(agent=product_page_detection_agent)
google_search_tool = AgentTool(agent=google_search_agent)

company_info_agent = LlmAgent(
    name="company_info_agent",
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    instruction=(
        "You are a company info agent. You use the list of URLs from {urls_list} "
        "First you use the product_page_detector tool to filter out non-product pages. "
        "If it's a product page use the google_searcher tool to find and return: "
        "the company name, number of employees, and a contact email. "
        "Return a list of objects with keys: url, company_name, num_employees, email. "
        "If information is not found, leave the value empty."
    ),
    tools=[google_search_tool, is_product_page_tool]
)
