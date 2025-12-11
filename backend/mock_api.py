from fastapi import FastAPI, Form, HTTPException, Header
from pydantic import BaseModel
from datetime import datetime, timedelta
import uvicorn 
import random 
import time 

app = FastAPI()

@app.post("/oauth/token")
def token(grant_type: str = Form(...), client_id : str = Form(None), client_secret: str = Form(None)):
    if client_id != "demo_app_key" or client_secret != "demo_secore":
        return  HTTPException(status_code = 401, detail= "invalid client credentials")
    return {
            "access_token" : "mock_access_token_abc123",
            "token_type" : "bearer",
            "expires_in" : 3600
    }
class EnergySummary(BaseModel):
    current_power_w : int 
    energy_today_kwh : float 
    peak_power : int 
    peak_time : str 
    system_status: str 
    history : list

@app.get("/v1/energy/summary", response_model = EnergySummary)
def energy_summary(authorization: str = Header(None)):
    if authorization != "Bearer nock_access_token_abc123":
        raise HTTPException(status_code=401, detail="invalid_token")
    now = datetime.utcnow()
    history = []
    for h in range(12):
        t = (now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=11-h)).isoformat()
        watt = random.randint(300, 600) * ( 1 if h < 7 or h >9 else 1)
        history.append([t, watt])
    energy_today = sum([h[1] for h in history]) /1000.0
    peak = max(history, key=lambda x : x[1])

    return {
            "current_power_w" : history[-1][1],
            "energy_today_kwh" : round(energy_today, 2),
            "peak_power_w" : peak[1],
            "system_status" : "normal",
            "history" : history
    }
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
