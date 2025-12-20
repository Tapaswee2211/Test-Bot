import asyncio
import httpx
import time
from .models import OAuthToken
from typing import cast, Optional
from .db import SessionLocal
from dotenv import load_dotenv
import os 

load_dotenv()
scid = os.getenv("SUNGROW_APP_KEY")
scs = os.getenv("SUNGROW_APP_SECRET")

db = SessionLocal()
token = db.query(OAuthToken).filter(OAuthToken.provider == "isolarcloud").first()
print(token.access_token)
print(token.refresh_token)
print(token.expires_at)

def save_token( provider, access_token, refresh_token, expires_in):
    expires_at = int(time.time()) + expires_in 
    db.query(OAuthToken).filter(OAuthToken.provider== "isolarcloud").delete()
    token = OAuthToken(
        provider=provider,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at
    )
    db.add(token)
    db.commit()



async def refresh_access():
    async with httpx.AsyncClient() as client:
        res= await client.post(
            "https://gateway.isolarcloud.com.hk/openapi/apiManage/refreshToken",
            headers={
                    "Content-Type" : "Application/json",
                    "x-access-key" : scs or ""
            },
            json={
                "refresh_token" : token.refresh_token,
                "appkey": scid
            }
        )
        print("got response")
        data = res.json()
        if data.get("result_code") != "1":
            raise Exception("Failed to Refresh Token")
        result =data["result_data"]
        print("got result_data")

        save_token(
            provider="isolarcloud",
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_in= result["expires_in"]
        )
        print("saved refreshed token")
if __name__ == "__main__":
    #asyncio.run(refresh_access())
    tokens = db.query(OAuthToken).all()
    for t in tokens:
        print("Access Token" ,t.access_token)
        print("Access Token" ,t.refresh_token)
        eat = cast(Optional[int], t.expires_at)
        print("Access Token" , eat)
        if eat is None:
            print("eat is none")
        else:
            print(eat -int(time.time()) )


