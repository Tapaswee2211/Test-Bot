from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage #, HumanMessage, SystemMessage 
from langchain_core.tools import Tool
from pydantic import BaseModel
from backend.tools import TOOLS
from dotenv import load_dotenv
load_dotenv()
SYSTEM_PROMPT = """You are a Smart Solar Energy Assistant.

Your goals:
- Help users ask about solar energy monitoring.
- Respond in a friendly and simple tone.
- If asked about data or tools, politely say:
  “I am not connected to data yet — but I can still explain concepts!”

How you speak:
- Keep responses short unless the user asks for details.
- Do not invent real-time energy numbers yet.
- You *can* explain solar concepts (power, efficiency, etc.)
- Encourage the user to ask about real monitoring later.
"""

model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_retries=2,
    max_tokens=1024,
    # other params...
)
SYSTEM_PROMPT2= "You are a dummy bot with which I'm experimenting tools"
chat_history = [
    ("system", SYSTEM_PROMPT2),
]


tools = TOOLS

def tool_executor(message: AIMessage):
    print("tool_executor called with tool_calls:", message.tool_calls)
    if not message.tool_calls:
        return AIMessage(content="No tools were called ")

    responses = []

    for tool_call in message.tool_calls:
        tool_name = tool_call.get("name")
        args = tool_call.get("args", {})

        if tool_name not in tools:
            responses.append(f"Unknown tool: {tool_name}")
            continue

        try:
            result = tools[tool_name](**args)
            if isinstance(result, dict) and "result" in result:
                value = result["result"]
                responses.append(f" Calculation complete: {value}")
            else:
                responses.append(f"{tool_name} succeeded → {result}")

        except Exception as e:
            responses.append(f"{tool_name} failed: {e}")

    return AIMessage(content="\n".join(responses))


class EmptyArgs(BaseModel):
    pass

lc_tools = [
    Tool(
        name=name,
        func=func,
        args_schema=EmptyArgs,
        description=f"Tool: {name}() executes an action."
    )
    for name, func in TOOLS.items()
]

# Bind tools to model
model_with_tools = model.bind_tools(lc_tools)

while True:
    q = input("Human: ")
    chat_history.append(("human", q))
    if q in ("exit", "quit", "q"):
        break
    ai_response = model_with_tools.invoke(chat_history)

    if isinstance(ai_response, AIMessage) and ai_response.tool_calls:
        res_msg = tool_executor(ai_response)
        print("Result: " ,res_msg.content)
    else:
        print("Bot:", ai_response.content)



