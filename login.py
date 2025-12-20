import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional


app = FastAPI()

class LoginRequest(BaseModel):
    user_account : str
    user_password : str
class LoginResponse(BaseModel):
    req_serial_num: str
    result_code : str
    result_msg: str
    result_data : dict

@app.post("/login", response_model=LoginResponse)
async def sungrow_login(login_data : LoginRequest):
    async with httpx.AsyncClient() as client:
        payload={
                "user_account":"monitoring@gunasolar.com",
                "user_password":'Guna@2023'
        }
        try:
            token_response= await client.post(
                    "https://web3.isolarcloud.com.hk/openapi/login",
                    params=payload
            )
            if token_response.status_code != 200:
                raise HTTPException(status_code=token_response.status_code, detail="Failed to authenticate")
            response_json = token_response.json()
            if response_json.get("result_data", {}).get("login_state") != "1":
                    raise HTTPException(status_code=400, detail="Login Failed")
            return response_json
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request Error: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"HTTP Error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected Error: {e}")


