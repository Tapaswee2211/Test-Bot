from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from backend.quick_start import run_chatbot

app =FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = [""],
    allow_headers = ["*"],
)

class ChatRequest(BaseModel):
    message :str
    session_id : str = "default"

@app.post("/chat")
def chat (req : ChatRequest):
    response = run_chatbot(req.message, session_id = req.session_id)
    return  {"reply": response}
