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
    No user-controlled arguments.
    This tool always fetches all plants.
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

# --- Schema for Tool 2---
class SolarPlantsBasicInfo(BaseModel):
    # We use a string here because LLMs call strings 100% reliably.
    # The actual value doesn't matter for your logic, but it fixes the '400' error.
    ps_ids: str = Field(
        default="list_all", 
        description= (
            "Comma-separated numeric plant IDs obtained from list_solar_plants. "
            "Example: '1711005,1688245'."
        )
    )

# --- 2. The Tool ---
@tool(args_schema=SolarPlantsBasicInfo)
async def solar_plants_basic_info(ps_ids: str)-> str:
    """
     Fetches the list of solar power plants for the authenticated user.

    Returns:
    - Name
    - ID (ps_id)
    - Status
    - Location

    This tool performs data retrieval only.
    The calling agent is responsible for interpreting and formatting the output.
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
    print(f"Target URL: {API_BASE}/openapi/platform/getPowerStationDetail")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/openapi/platform/getPowerStationDetail",
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
    plants = result_data.get("data_list", [])

    output_lines = [f"**Found {len(plants)} Solar Plants:**\n"]
    for p in plants:
        # 1. Gather fields with safe fallbacks
        name = p.get("ps_name") or "Unnamed Plant"
        pid = p.get("ps_id", "N/A")
        loc = p.get("ps_location") or "Location not specified"
        date = p.get("install_date") or "Date not provided"
        # Convert power from Watts to Kilowatts if present
        power_w = p.get("install_power")
        capacity = f"{float(power_w)/1000:.2f} kW" if power_w else "Unknown"
        
        # Pricing handling - prevent "None None"
        price = p.get("ps_feedin_power_price_wh")
        unit = p.get("power_price_unit")
        price_str = f"{price} {unit}" if price and unit else "Price data not available"

        status = "ONLINE" if p.get("online_status") == 1 else "OFFLINE"

        # 2. Build a structured block for the LLM to read
        plant_info = (
            f"DETAILS FOR PLANT: {name}\n"
            f"- Plant ID: {pid}\n"
            f"- Current Status: {status}\n"
            f"- Installed Capacity: {capacity}\n"
            f"- Location: {loc}\n"
            f"- Installation Date: {date}\n"
            f"- Feed-in Tariff: {price_str}\n"
            f"---"
        )
        output_lines.append(plant_info)
    
    return "\n".join(output_lines)
