import os 
import asyncio
from typing import Annotated, Literal
from typing_extensions import TypedDict
import os 
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

from backend.tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = """You are a Smart Solar Energy Assistant.

Your goals:
- Help users ask about solar energy monitoring.
- Respond in a friendly and simple tone. Use the provided tools to fetch weather or search the web when necessary.
Fetch the private list of solar power plants from iSolarCloud.
You are a Sungrow iSolarCloud assistant. You have DIRECT ACCESS to the user's solar data via tools
NEVER search the web for 'list of solar plants'—that will only find public information.
ALWAYS use the list_solar_plants tool to see the user's actual hardware.
If you encounter an error, report the specific technical error instead of guessing
This is the only way to see the user's actual plant IDs and Status.


"""

#                           -- Model Setup --
model = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
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

#                         -- Build the Graph ---

workflow = StateGraph(AgentState)
workflow.add_node("agent", chatbot_node)
workflow.add_node("tools", tool_node)

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


#                       -- Persistance --

#memory Saver 
checkpointer = MemorySaver()


app = workflow.compile(checkpointer=checkpointer)


async def run_chatbot(user_message: str, session_id: str= "default"):
    """
    Runs the chatbot for a specific sessoin
    """

    config = {"configurable" : {"thread_id": session_id}}

    #if new session -> Add system prompt first
    #for now we will add system prompt for every query

    input_messages = [HumanMessage(content=user_message)]
    #if history is empty Strictly enforce System Prompt at start
    state_snapshot = await app.aget_state(config)

    if len(state_snapshot.values.get("messages", [])) == 0:
        input_messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    #Stream the events
    #stream_mode= 'values' gives the full list of messages at each step
    events = app.astream(
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

    snapshot = await app.aget_state(config)
    if snapshot.values.get("messages"):
        return snapshot.values["messages"][-1].content

    return final_response

#if __name__ == "__main__":
#    async def main():
#        print("--- Starting Solar Assistant----")
#        reply1 = await run_chatbot("Hello Who are you", session_id="user1")
#        print(f"\nBot: {reply1}")
#
#        reply2 = await run_chatbot("What is the weather like at lat 12.97 long 77.59 right now?", session_id="user1")
#        print(f"\nBot: {reply2}")
#
#        reply3 = await run_chatbot("Search for the latest solar panel efficiency records 2024", session_id="user1")
#        print(f"\nBot: {reply3}")
#
#        reply4 = await run_chatbot("List my solar power plants with the available tool", session_id="user1")
#        print(f"\nBot: {reply4}")

#    asyncio.run(main())

