from urllib.parse import quote
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv 
import httpx
import os 
import json
from pathlib import Path
import time
from models import Base, OAuthToken
from db import SessionLocal,engine
from helper import save_token, load_token

Base.metadata.create_all(bind=engine)

load_dotenv()


app = FastAPI()
scid = os.getenv("SUNGROW_APP_KEY")
scs = os.getenv("SUNGROW_APP_SECRET")
FILE = Path("token_store.json")


@app.get("/")
def helloWorld():
    return {"message" :"Hello World"}

redirect_url = "http://localhost:3000/callback"
@app.get("/login")
def sungrow_login():
    token = load_token("isolarcloud")
    print("login point hit")
    if token:
        return JSONResponse({
                "message" : "Already Authorized",
                "access_token" : token.access_token,
                "expires_at" : token.expires_at
        })
    encoded_redirect = quote(redirect_url, safe="") 
    sungrow_url = (
        f"https://web3.isolarcloud.com.hk/#/authorized-app?cloudId=2&applicationId=1943"
        f"&redirectUrl={encoded_redirect}"
    )
    print("redirecting to", sungrow_url)
    return RedirectResponse(sungrow_url)

@app.get("/callback")
async def sungrow_callback(request : Request):
    print("Callback point hit")
    code = request.query_params.get("code")
    if not code:
        return JSONResponse({"error": "No authorization code received"})
    print("got code")
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://gateway.isolarcloud.com.hk/openapi/apiManage/token",
            headers={
                "Content-Type": "application/json",
                "x-access-key": scs or ""  
            },
            json={
                "appkey": scid,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "http://localhost:3000/callback"
            }
        )

    print("===== TOKEN ENDPOINT DEBUG =====")
    print("Status Code :", token_response.status_code)
    print("Headers     :", dict(token_response.headers))
    print("Raw Body    :")
    print(token_response.text)
    print("================================")


@app.get("/me")
async def get_me():
    token = load_token("isolarcloud")
    if not token:
        return JSONResponse({"errro" : "Not Authenticated"})

    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization" : f"Bearer {token.access_token}"

            }
        )
    return res.json()

@app.get("/tokens")
def get_tokens():
    db = SessionLocal()
    try:
        tokens = db.query(OAuthToken).all()
        return [
            {
                "id" : t.id,
                "provider" : t.provider,
                "access_token" : t.access_token,
                "expires_at" : t.expires_at
            }
            for t in tokens
        ]
    finally:
        db.close()


