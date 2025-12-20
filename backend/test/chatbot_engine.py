from dotenv import load_dotenv
load_dotenv()

import os
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langchain_core.messages import AIMessage, HumanMessage

from backend.company_api import company_client

from langchain_core.tools import Tool


# ---------------------------------------------------
# Model + Tools
# ---------------------------------------------------
assert os.getenv("GROQ_API_KEY")
assert os.getenv("TAVILY_API_KEY"), "TAVILY_API_KEY missing in .env"

llm = ChatGroq(model="deepseek-r1-distill-llama-70b")
tavily = TavilySearch(max_results=3)


class State(TypedDict):
    messages: Annotated[list, add_messages]


# ---------------------------------------------------
# Energy Tool
# ---------------------------------------------------
def get_energy_tool(state: State):
    try:
        data = company_client.get_energy_summary()
    except Exception as e:
        return {"messages": [AIMessage(content=f"Failed to fetch energy data: {e}")]}

    summary = (
        f"🔌 Live Energy Summary:\n"
        f"• Current Power: {data.get('current_power_w')} W\n"
        f"• Energy Today: {data.get('energy_today_kwh')} kWh\n"
        f"• Peak Power: {data.get('peak_power_w')} W\n"
        f"• System Status: {data.get('system_status','Unknown')}\n"
        "\n(Ask: 'Show history')"
    )

    return {"messages": [AIMessage(content=summary)]}


# ---------------------------------------------------
# History Tool
# ---------------------------------------------------
def get_history_tool(state: State):
    try:
        data = company_client.get_energy_summary()
    except Exception as e:
        return {"messages": [AIMessage(content=f"History fetch failed: {e}")]}

    history = data.get("history", [])

    if not history:
        return {"messages": [AIMessage(content="No history available yet!")]}

    lines = ["🕒 Timestamp | ⚡ Power (W)"]
    lines += [f"{t} | {w} W" for t, w in history]

    return {"messages": [AIMessage(content="\n".join(lines))]}


# ---------------------------------------------------
# Chatbot Node — handles everything else
# ---------------------------------------------------
energy_summary_tool = Tool(
    name="energy_summary",
    description="Returns live solar production summary data.",
    func=lambda _: get_energy_tool({"messages": []})["messages"][0].content
)

energy_history_tool = Tool(
    name="energy_history",
    description="Returns recent historical solar energy values.",
    func=lambda _: get_history_tool({"messages": []})["messages"][0].content
)

web_search_tool = Tool(
    name="web_search",
    description="Search the web for general info using Tavily",
    func=lambda q: tavily.invoke({"query": q})["results"]
)

tools = [energy_summary_tool, energy_history_tool, web_search_tool]

llm_with_tools = llm.bind_tools(tools)

llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    msg = llm_with_tools.invoke(state["messages"])
    return {"messages": [msg]}


# ---------------------------------------------------
# Tool Execution Node
# ---------------------------------------------------
def tool_executor(state: State):
    msg = state["messages"][-1]
    tool_call = msg.tool_calls[0]
    tool_name = tool_call["name"]
    args = tool_call.get("args", "")

    # Find tool by name
    tool = next(t for t in tools if t.name == tool_name)

    result = tool.run(args)

    return {"messages": [AIMessage(content=str(result))]}


# ---------------------------------------------------
# Graph Logic
# ---------------------------------------------------
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tool", tool_executor)


def route(state: State):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool"
    return END


graph_builder.add_conditional_edges("chatbot", route)
graph_builder.add_edge("tool", END)
graph_builder.add_edge(START, "chatbot")


memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)


# ---------------------------------------------------
# Public API for FastAPI/Streamlit
# ---------------------------------------------------
def run_chatbot(user_input: str, session_id="1"):
    events = graph.stream(
        {"messages": [HumanMessage(content=user_input)]},
        {"configurable": {"thread_id": session_id}},
        stream_mode="values",
    )
    for event in events:
        if "messages" in event:
            msg = event["messages"][-1]
            if isinstance(msg, AIMessage):
                return msg.content

    return "No response"


# ---------------------------------------------------
# Interactive mode (optional)
# ---------------------------------------------------
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        reply = run_chatbot(user_input)
        print("Bot:", reply)

