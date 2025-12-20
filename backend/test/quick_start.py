from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage , HumanMessage, SystemMessage 
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
from backend.tools import TOOLS
from dotenv import load_dotenv
load_dotenv()
SYSTEM_PROMPT = """You are a Smart Solar Energy Assistant.

Your goals:
- Help users ask about solar energy monitoring.
- Respond in a friendly and simple tone.

How you speak:
- Keep responses short unless the user asks for details.
- You will use the Tool created to fetch weather details whenver user asks
"""

model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_retries=2,
    max_tokens=1024,
    # other params...
)
chat_history0 = [
    ("system", SYSTEM_PROMPT),
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
        func, schema = tools[tool_name]

        try:
            result = func(**args)
            #if isinstance(result, dict) and "result" in result:
            if isinstance(result, AIMessage):
                pretty = result.content
                #value = result["result"]
                #responses.append(f" Calculation complete: {value}")
            else:
                #responses.append(f"{tool_name} succeeded → {result}")
                pretty = str(result)
            responses.append(f"{pretty}")

        except Exception as e:
            responses.append(f"{tool_name} failed: {e}")

    return AIMessage(content="Tool result : \n"+ "\n".join(responses))



lc_tools = [
    Tool(
        name=name,
        func=func,
        args_schema=schema,
        description=f"Tool: {name}() executes an action."
    )
    for name, (func,schema) in TOOLS.items()
]

# Bind tools to model
model_with_tools = model.bind_tools(lc_tools)

chat_sessions = {}
def get_session_history(session_id : str):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = [SystemMessage(content=SYSTEM_PROMPT)]
    return chat_sessions[session_id]

def run_chatbot(message :str, session_id: str= "default"):
    chat_history = get_session_history(session_id)
    
    chat_history.append(HumanMessage(content=message))
    ai_response = model_with_tools.invoke(chat_history)

    if isinstance(ai_response, AIMessage) and ai_response.tool_calls:
        res_msg = tool_executor(ai_response)
        bot_reply = res_msg.content
        chat_history.append(AIMessage(content=bot_reply))
    else:
        bot_reply = ai_response.content
        chat_history.append(ai_response)

    chat_sessions[session_id] = chat_history
    return bot_reply
