from dotenv import load_dotenv 
from typing import Any
import os 
import json
import httpx
from langchain_core.tools import tool

try:
    from backend.app.helper import get_valid_token
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
class SolarPlantsBasicInfo(BaseModel):
    # We use a string here because LLMs call strings 100% reliably.
    # The actual value doesn't matter for your logic, but it fixes the '400' error.
    ps_ids: str = Field(
        default="list_all", 
        description="this is a string variable with ps_ids of the solar plants which you want the basic information about. Get the ps_ids using the list_solar_plants tool. From the output of that tool create the ps_ids WHICH MUST BE COMMA SEPERATED AND SHOULD NOT HAVE SPACE BETWEEN THEM"
    )

# --- 2. The Tool ---
@tool(args_schema=SolarPlantsBasicInfo)
async def solar_plants_basic_info(ps_ids: str)-> str:
    """
    REQUIRED: Use this tool to fetch the information of a particular group of solar power plants from iSolarCloud using their plant IDs.
    This tool will require an argument which is a string variable named ps_ids which contains the IDs of the solar plants which you want the basic information of.Get the ps_ids using the list_solar_plants tool. From the output of list_solar_plants tool create the ps_ids variable WHICH MUST BE COMMA SEPERATED STRING AND SHOULD NOT HAVE SPACE BETWEEN THEM THE IDs OF PLANTS.
    The user asks the information about a particular plant or group of plants by name so be sure that after using the list_solar_plants you take the IDs of specific power plants asked by user.
    Return the Name, ID, Status, Location and summarize the general information for every plant asked by user. 
    """
    try:
        access_token = await get_valid_token()
    except Exception as e:
        return f"Authentication Failed: Could not retrieve token. Error: {e}"

    payload = {
        "appkey": SC_APP_KEY,
        "ps_ids": ps_ids, 
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
