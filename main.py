from urllib.parse import quote
from fastapi import FastAPI, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv 
import httpx
import os 
import json
from pathlib import Path
import time
from models import Base, OAuthToken
from db import SessionLocal,engine
from helper import get_valid_token, load_token, save_token

Base.metadata.create_all(bind=engine)

load_dotenv()


app = FastAPI()
scid = os.getenv("SUNGROW_APP_KEY")
scs = os.getenv("SUNGROW_APP_SECRET")
FILE = Path("token_store.json")

@app.get("/")
def helloWorld():
    return {"message" : "Hello World"}

redirect_url = "http://localhost:3000/callback"
api = "https://gateway.isolarcloud.com.hk"

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
        "https://web3.isolarcloud.com.hk/#/authorized-app?cloudId=2&applicationId=1943"
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
                "https://web3.isolarcloud.com.hk/openapi/apiManage/token",
                headers={
                    "Content-Type":"application/json",
                    "x-access-key": scs or ""

                },
                json={
                    "appkey":scid,
                    "grant_type":"authorization_code",
                    "code":code,
                    "redirect_uri": redirect_url
                }
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        print("===== iSolarCloud TOKEN RESPONSE =====")
        print(json.dumps(token_data, indent=2))
        print("======================================")

        if not access_token:
            return JSONResponse({"error": "Failed to get access token"})
        
        save_token(
            provider="isolarcloud",
            access_token=access_token,
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in", 3600)
        )
    print("token saved")
    return {
            "message":"OAuth Successful, token stored",
            "Token expires in " : token_data.get("expires_in")
    }

@app.get("/tokens")
async def get_tokens():
    token = await get_valid_token()
    return {"Access_token " : token}

@app.get("/plants")
async def get_plants(
    page : int = Query(1,ge=1),
    size : int = Query(10,ge=1, le= 100),
    ps_type : str | None = "1,3,4,5",
    valid_flag : str | None = "1,3",
    ps_name : str | None = ""
):
    access_token = await get_valid_token()
    payload = {
        "appkey" : scid,
        "page" : page, 
        "size" : size, 
        "ps_type" : ps_type, 
        "ps_name" : ps_name, 
        "valid_flag" : valid_flag
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{api}/openapi/platform/queryPowerStationList",
            headers={
                "Authorization" : f"Bearer {access_token}",
                "Content-Type" : "application/json",
                "x-access-key" : scs or ""
            },
            json = payload
        )
    data = res.json()
    
    if data.get("result_code") != '1':
        return{
                "error" : "Failed to fetch Plants",
                "response" : data
        }
    result_data = data.get("result_data", {})

    return {
        "total": (
            result_data.get("rowCount")
            or result_data.get("row_count")
            or result_data.get("total")
            or len(result_data.get("pageList", []))
        ),
        "plants": result_data.get("pageList", [])
    }
