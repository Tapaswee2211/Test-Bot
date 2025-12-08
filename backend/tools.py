from pydantic import BaseModel, Field
import requests
from langchain_core.messages import AIMessage #, HumanMessage, SystemMessage 


def get_cat_fact(**kwargs) -> AIMessage:
    """Fetch a random cat fact from an external API and return it as an AIMessage."""
    try:
        r = requests.get("https://catfact.ninja/fact",timeout=5)
        r.raise_for_status()
        fact = r.json().get("fact", "No fact Found")
        return AIMessage(content=f"Cat Fact: {fact}")
    except Exception as e:
        return AIMessage(content=f"Could not fetch cat fact")


TOOLS = {
        "get_cat_fact": get_cat_fact,
}
