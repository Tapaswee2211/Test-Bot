from tavily import TavilyClient
from langchain_core.tools import tool
from dotenv import load_dotenv
import os 

load_dotenv()

tavily = TavilyClient()

@tool
def search_web(query: str):
    """
    Perform a real internet search using Tavily.
    Use this to find information not present in your training data.
    """
    try:
        result = tavily.search(query=query, max_results=5)
        summaries = []
        for i in result.get("results", []):
            title = i.get("title", "No title")
            link = i.get("url", "No Link")
            snippet = i.get("content", "")
            summaries.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}")
        return "\n\n".join(summaries)
    except Exception as e :
        return "Tavily Search Failed : {e}"

