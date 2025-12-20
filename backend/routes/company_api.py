import requests
import json
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os 

load_dotenv()

USE_MOCK = os.getenv("USE_MOCK_API", "true").lower() in ("1", "true", "yes")
MOCK_API_URL = os.getenv("MOCK_API_URL","http://localhost:9000")

class CompanyAPIClient:
    def __init__(self):
        self.client_id = os.getenv("APP_KEY", "demo_app_key")
        self.client_secret = os.getenv("APP_SECRET", "demo_secret")

        token_env = os.getenv("TOKEN_URL")
        api_env = os.getenv("API_BASE")
        if USE_MOCK:
            self.token_url  = token_env or f"{MOCK_API_URL}/oauth/token" 
            self.api_base = api_env or MOCK_API_URL 
        else:
            if not token_env or not  api_env:
                raise ValueError("TOKEN URL AND API BASE MUST BE SET WHEN USE MOCK IS FALSE")
            self.token_url  = token_env 
            self.api_base = api_env 

        self.access_token = None
        self._expiry_at = datetime.utcnow()
    def _get_token_client_credentials(self):
        if self._access_token and datetime.utcnow() < self._expiry_at: 
            return self._access_token
        data = {
            "grant_type" : "client_credentials",
            "client_id" : self.client_id,
            "client_secret" : self.client_secret,
        }
        resp = requests.post(self.token_url, data=data, timeout=10)
        resp.raise_for_status()
        tok = resp.json()
        self._access_token = tok["access_token"]
        self._expiry_at = datetime.utcnow() + timedelta(seconds=tok.get("expires_in", 3600))
        return self._access_token 
    def get_energy_summary(self):
        token = self._get_token_client_credentials()
        headers = {"Authorization" : f"Bearer {token}"}
        resp = requests.get(f"{self.api_base}/v1/energy/summary", headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

company_client = CompanyAPIClient()



