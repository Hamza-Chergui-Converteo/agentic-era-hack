from google.adk import Agent
from google.adk.tools import google_search
from dotenv import load_dotenv

from .sub_agents.search_agent.agent import search_agent
from .sub_agents.company_info_agent.agent import company_info_agent
import os
from google.adk.agents import SequentialAgent


load_dotenv()


root_agent = SequentialAgent(name="seo_agent", sub_agents=[search_agent, company_info_agent])#
