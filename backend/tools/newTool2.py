from dotenv import load_dotenv
import os
import httpx
from langchain_core.tools import tool
from pydantic import BaseModel
from helper import get_valid_token

load_dotenv()

# Configuration
SC_APP_KEY = os.getenv("SUNGROW_APP_KEY")
SC_APP_SECRET = os.getenv("SUNGROW_APP_SECRET")
API_BASE = "https://gateway.isolarcloud.com.hk"

# --- 1. Empty Input Schema ---
# This explicitly tells the LLM: "This tool accepts NO arguments."
class ListSolarPlantsInput(BaseModel):
    pass

# --- 2. The Tool ---
@tool(args_schema=ListSolarPlantsInput)
async def list_solar_plants() -> str:
    """
    Fetches the full list of solar power plants from iSolarCloud.
    Returns the Name, ID, Status, and Location of every plant found.
    Just Summarize whatevery is returned fron this tool 
    """
    
    # 1. Authentication
    try:
        access_token = await get_valid_token()
    except Exception as e:
        return f"SYSTEM ERROR: Authentication failed. {str(e)}"

    # 2. Prepare Payload (Hardcoded to list ALL)
    payload = {
        "appkey": SC_APP_KEY,
        "page": 1, 
        "size": 10, 
        "ps_type": "1,3,4,5", 
        "valid_flag": "1,3",
        "ps_name": ""  # Empty string lists everything
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-access-key": SC_APP_SECRET or ""
    }

    # 3. API Request
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/openapi/platform/queryPowerStationList",
                headers=headers,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
    except httpx.HTTPStatusError as e:
        return f"API ERROR: HTTP {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"CONNECTION ERROR: {str(e)}"

    # 4. Parse Response
    if data.get("result_code") != '1':
        return f"iSolarCloud API Error: {data.get('result_msg', 'Unknown')}"

    # Using 'pageList' as verified by your debug script
    result_data = data.get("result_data", {})
    plants = result_data.get("pageList", [])

    if not plants:
        return "No solar plants found in the account."

    # 5. Format Output
    output_lines = [f"Found {len(plants)} plants:"]
    
    for p in plants:
        name = p.get("ps_name", "Unknown")
        pid = p.get("ps_id", "N/A")
        loc = p.get("ps_location", "Unknown Location")
        
        # Status: 1=Online, Others=Offline
        is_online = p.get("online_status") == 1
        status_str = "ONLINE" if is_online else "OFFLINE"

        line = (
            f"- **{name}** (ID: {pid}) | Status: {status_str} | Location: {loc}"
        )
        output_lines.append(line)

    return "\n".join(output_lines)
