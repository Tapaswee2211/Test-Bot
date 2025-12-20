from dotenv import load_dotenv 
from typing import Any
import os 
import json
import httpx
from langchain_core.tools import tool

try:
    from helper import get_valid_token
except ImportError:
    print("CRITICAL: Could not import 'get_valid_token' from helper.py")
    exit(1)
from pydantic import BaseModel, Field 

load_dotenv()

# Configuration
SC_APP_KEY = os.getenv("SUNGROW_APP_KEY")
SC_APP_SECRET = os.getenv("SUNGROW_APP_SECRET")
API_BASE = "https://gateway.isolarcloud.com.hk"


# --- 1. Simplified Schema ---
class ListSolarPlantsInput(BaseModel):
    # We use a string here because LLMs call strings 100% reliably.
    # The actual value doesn't matter for your logic, but it fixes the '400' error.
    action: str = Field(
        default="list_all", 
        description="The action to perform. Always use 'list_all'."
    )

# --- 2. The Tool ---
@tool(args_schema=ListSolarPlantsInput)
async def list_solar_plants(action: str = "list_all") -> str:
    """
    REQUIRED: Use this tool to fetch the list of solar power plants from iSolarCloud.
    Returns the Name, ID, Status, and Location for every plant in the user's account.
    """
    try:
        access_token = await get_valid_token()
    except Exception as e:
        return f"Authentication Failed: Could not retrieve token. Error: {e}"

    payload = {
        "appkey": SC_APP_KEY,
        "page": 1, 
        "size": 10, 
        "ps_type": "1,3,4,5", 
        "valid_flag": "1,3",
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-access-key": SC_APP_SECRET or ""
    }
    print(f"Target URL: {API_BASE}/openapi/platform/queryPowerStationList")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/openapi/platform/queryPowerStationList",
                headers=headers,
                json=payload,
                timeout=10.0
            )
            # Raise error for bad HTTP status (4xx/5xx)
            response.raise_for_status()
            data = response.json()
            
    except httpx.HTTPStatusError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Connection Error: {e}"

    if data.get("result_code") != '1':
        return f"iSolarCloud API Error: {data.get('result_msg', 'Unknown Error result code is 1')}"

    result_data = data.get("result_data", {})
    plants = result_data.get("pageList", [])

    output_lines = [f"**Found {len(plants)} Solar Plants:**"]
    
    for p in plants:
        name = p.get("ps_name", "Unknown Name")
        ps_id = p.get("ps_id", "N/A")
        location = p.get("ps_location", "Unknown Location")
        install_date = p.get("install_date", "N/A")
        
        # Status mapping: 1 = Online, everything else = Offline/Fault/Unknown
        # Using simple text markers for clarity
        is_online = p.get("online_status") == 1
        status_str = "ONLINE" if is_online else "OFFLINE"

        line = (
            f"\n- **{name}** (ID: {ps_id})\n"
            f"  Status: {status_str}\n"
            f"  Location: {location}\n"
            f"  Installed: {install_date}"
        )
        output_lines.append(line)

    return "\n".join(output_lines)
