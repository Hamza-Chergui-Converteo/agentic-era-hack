
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

class CompanyInfo(BaseModel):
    """Extracted company information."""
    company_name: str = Field(description="Name of the company.")
    num_employees: str = Field(description="Number of employees, as a string.")
    email: str = Field(description="Contact email of the company.")

class IsProductPage(BaseModel):
    """Whether the page is a product page or not."""
    is_product_page: bool = Field(description="True if the page is a company product page or homepage, False otherwise.")

# Initialize the generative model once and reuse it.
# This is more efficient than creating a new model for each function call.
client = genai.Client()
model = os.getenv("MODEL", "gemini-2.5-flash")

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

def filter_product_pages(tool_context: ToolContext) -> str:
    """Fetches content for pages in 'other_results', uses Gemini to analyze if they are
    product pages, and returns a JSON string of the pages that are.
    """
    tools = [
      {"url_context": {}},
    ]
    product_pages = []
    instruction = """You are a specialist in identifying company product pages and official company websites.
    Analyze the provided URL and page content to determine if it represents a company product page
    (e.g., shows products, describes company offerings) or an official company homepage.
    Consider factors like: product listings, company information, service descriptions,
    contact information, about pages, and overall website structure. STRICT Answer ONLY with 'yes' or 'no'"""

    results = tool_context.state.get("other_results", [])

    for result_page in results:
        link = result_page.get("link")
        if not link:
            continue
        # For each fetched content, call Gemini and analyze
        prompt = f"{instruction}\n\nURL: {link}"
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=GenerateContentConfig(tools=tools),
        )
        print(response.text)
        if response.text and "yes" in response.text.lower():
            product_pages.append(result_page)
    tool_context.state["product_pages"] = product_pages
    return 'Product pages detection done'

def get_infos_companies(tool_context: ToolContext) -> dict:
    tools = [
      {"url_context": {}},
      {"google_search": {}},
    ]
    companies_info = []
    extraction_instruction = """From the URL, use the google_search and url_context tools to get the following information about the company: "company_name", "num_employees" and "email".
    If a piece of information is not found, use an empty string "" as the value.
    """
    product_pages = tool_context.state.get("product_pages", [])
    if not product_pages:
        return "[]"
    for page in product_pages:
        link = page.get("link")
        if not link:
            continue
        prompt = f" URL: {link} {extraction_instruction}"
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=GenerateContentConfig(tools=tools)
        )
        print(response.text)
        print('*****************')
        response = client.models.generate_content(
            model=model,
            contents=f"Structure the output : {response.text}",
            config=GenerateContentConfig(response_mime_type="application/json", response_schema=CompanyInfo)
        )
        print(response.text)
        info = json.loads(response.text)
        info['url'] = link
        companies_info.append(info)
    tool_context.state["companies_to_filter"] = companies_info
    return json.dumps(companies_info)

company_info_agent = LlmAgent(
    name="company_info_agent",
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    instruction="""You are a company info agent. Your goal is to find information about companies from a list of URLs.
    The initial list of URLs is in the 'other_results' state variable.
    1. First, call the `filter_product_pages` tool to identify which of these are product/company pages. This will populate the 'product_pages' state.
    2. Then, call the `get_infos_companies` tool to search for and extract company details for each page. This will populate the 'companies_to_filter' state.
    3. Finally, return the content of the 'companies_to_filter' state variable as your final answer in JSON format.""",
    tools=[filter_product_pages, get_infos_companies],
    output_key="companies_to_filter"
)