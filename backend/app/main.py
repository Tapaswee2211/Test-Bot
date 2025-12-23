from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage 

from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = """
You are the Smart Solar Energy Assistant for Sungrow iSolarCloud.

You have DIRECT ACCESS to the user's private solar plant data ONLY through tools.
You MUST strictly follow the rules below.

────────────────────────────────────────
STRICT ORDER OF OPERATIONS
────────────────────────────────────────

1) LISTING
If the user asks to:
- "List the power plants"
- "Display my plants"
- "Show my plants"

You MUST:
- Call ONLY the tool: list_solar_plants
- DO NOT call solar_plants_basic_info
- Summarize the returned string immediately

2) DISCOVERY (Plant by Name)
If the user asks about a specific plant by name (e.g., "Ovobel Foods Limited"):

You MUST:
- FIRST call list_solar_plants
- Extract the numeric ps_id for the plant
- If no match is found, respond:
  "I couldn't find a plant with that name in your account."

3) INSPECTION
ONLY AFTER a numeric ps_id is found:
- Call solar_plants_basic_info
- Pass ONLY numeric IDs (comma-separated, no spaces)

────────────────────────────────────────
CRITICAL CONSTRAINTS (NON-NEGOTIABLE)
────────────────────────────────────────

- NEVER guess or invent plant IDs
- NEVER call solar_plants_basic_info unless a plant name is explicitly requested
- NEVER use web search for private plant data
- NEVER say "data fetched" without displaying results
- NEVER skip list_solar_plants before solar_plants_basic_info

────────────────────────────────────────
RESPONSE FORMATTING RULES
────────────────────────────────────────

When LISTING plants:
• Name
• ID
• Status
• Location

When showing PLANT DETAILS:
• Name
• ID
• Capacity (kW)
• Status
• Location

────────────────────────────────────────
FAILURE HANDLING
────────────────────────────────────────

If a plant name is not found:
"I couldn't find a plant with that name in your account."

You MUST obey these rules exactly.

"""

#                           -- Model Setup --
model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    max_retries=2,
    max_tokens=1024,
)
#Bind Tools
model_with_tools = model.bind_tools(ALL_TOOLS)


#                      -- State Definition --

#track conversation history automatically
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

#                        -- Nodes --

def chatbot_node(state :AgentState):
    """
    The main node that calls the LLM.
    Receivese Current State/ History and returns LLM's new message.
    """
    response = model_with_tools.invoke(state["messages"])
    return {"messages" : [response]}

#Buit-In tool node will handle manual tool_executor.
#It handles parallel executionk, argument validation and error formatting
tool_node = ToolNode(tools=ALL_TOOLS)

def final_node(state):
    # The agent already produced tool output → just end
    return state

#                         -- Build the Graph ---

workflow = StateGraph(AgentState)
workflow.add_node("agent", chatbot_node)
workflow.add_node("tools", tool_node)
workflow.add_node("final", final_node)
# Define workflow 
workflow.add_edge(START, "agent")
#Conditional Edge: Check if agent wants to call a tool
# if yes go to tools 
# if no go to end 
workflow.add_conditional_edges(
        "agent",
        tools_condition,
)
workflow.add_edge("tools", "agent")
workflow.add_edge("tools", "final")
workflow.add_edge("final", END)


#                       -- Persistance --

#memory Saver 
checkpointer = MemorySaver()


bot = workflow.compile(checkpointer=checkpointer)


async def run_chatbot(user_message: str, session_id: str= "default"):
    """
    Runs the chatbot for a specific sessoin
    """

    config = {"configurable" : {"thread_id": session_id}}

    #if new session -> Add system prompt first
    #for now we will add system prompt for every query

    input_messages = [HumanMessage(content=user_message)]
    #if history is empty Strictly enforce System Prompt at start
    state_snapshot = await bot.aget_state(config)

    if len(state_snapshot.values.get("messages", [])) == 0:
        input_messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    #Stream the events
    #stream_mode= 'values' gives the full list of messages at each step
    events = bot.astream(
            {"messages" : input_messages},
            config,
            stream_mode="values"
    )
    final_response = ""
    async for event in events:
        messages = event.get("messages")
        if messages:
            last_message = messages[-1]

            if last_message.content:
                print(f"DEBUG STEP: {last_message.type.upper()}")
                
            if isinstance(last_message, type(model.invoke("test"))):
                final_response = last_message.content

    snapshot = await bot.aget_state(config)
    if snapshot.values.get("messages"):
        return snapshot.values["messages"][-1].content

    return final_response

app = FastAPI(title="Solar AI Backend")

# CORS (required for Streamlit / browser access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Request schema --------

class Query(BaseModel):
    message: str
    session_id: str = "user1"

# -------- Health check --------

@app.get("/")
def health():
    return {"status": "ok"}

# -------- Chat endpoint --------

@app.post("/chat")
async def chat(query: Query):
    """
    Chat endpoint used by Streamlit frontend
    """
    response = await run_chatbot(
        user_message=query.message,
        session_id=query.session_id
    )

    return {"response": response}

if __name__ == "__main__":
    async def main():
        print("--- Starting Solar Assistant----")
        reply5 = await run_chatbot("From my power plants give basic information of Rama burger king", session_id="user1")
        print(f"\nBot: {reply5}")
    asyncio.run(main())

