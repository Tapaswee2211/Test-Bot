import requests
import json
import base64
from datetime import datetime, timedelta

class EnergyAPIClient:
    def __init__(self):
        self.client_id = "APP_KEY"
        self.client_secret= "SECRET_KEY"
        self.authorized_url = "http://company.com/auth"
        self.token_url = "https://company.com/oauth/token"
        self.api_base = "https://company.com/api"
        self.redirect_ur = "https://company.com/callback"
        self.access_token = None
        self.expiry = datetime.utcnow()

    def get_access_token (self):
        if self.access_token and datetime.utcnow() < self.expiry:
            return self.access_token
        data = {
            "grant_type" : "client_credentials",
            "client_id" : self.client_id,
            "client_secret" : self.client_secret
        }
        resp = requests.post(self.token_url, data=data)
        token_data = resp.json()
        self.access_token = token_data["access_token"]
        self.expiry = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

        return self.access_token
    def get_energy_summary(self):
        token = self.get_access_token()
        headers = {"Authorization" : f"Bearer {token}"}

        resp = requests.get(f"{self.api_base}/vi/energy/summary", headers=headers)
        return resp.json()




