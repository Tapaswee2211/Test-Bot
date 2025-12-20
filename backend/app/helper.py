from typing import cast, Optional
from dotenv import load_dotenv 
import httpx
import os 
from pathlib import Path
import time
from .models import init_db, OAuthToken
from .db import SessionLocal
load_dotenv()

scid = os.getenv("SUNGROW_APP_KEY")
scs = os.getenv("SUNGROW_APP_SECRET")

def save_token(provider, access_token, refresh_token, expires_in):
    db = SessionLocal()
    expires_at = int(time.time()) + expires_in if expires_in else None
    db.query(OAuthToken).filter(OAuthToken.provider == provider).delete()
    token = OAuthToken(
        provider=provider,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at
    )
    db.add(token)
    db.commit()
    db.close()

def load_token(provider):
    db = SessionLocal()
    token = db.query(OAuthToken).filter(OAuthToken.provider==provider).first()
    print(token)
    db.close()
    return token

def is_token_expired(token:OAuthToken):
    exp = cast(Optional[int], token.expires_at)
    if exp is None:
        return False
    return time.time() > exp

async def refresh_access_token():
        token = load_token("isolarcloud")
        if not token: 
            raise Exception("Token is not present")

        if token.refresh_token is None:
            raise Exception("No refresh Token Available")

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
            data = res.json()
            if data.get("result_code") != "1":
                raise Exception("Failed to Refresh Token")
            result =data["result_data"]
            save_token(
                provider="isolarcloud",
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
                expires_in= result["expires_in"]
            )

async def get_valid_token():
    init_db()
    token = load_token("isolarcloud")
    if not token or is_token_expired(token):
        await refresh_access_token()
        token = load_token("isolarcloud")
    if token is None:
        raise RuntimeError("Failed to obtail access Token")
    return token.access_token


