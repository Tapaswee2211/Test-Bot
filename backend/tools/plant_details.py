import os
import httpx
from langchain_core.tools import tool
from dotenv import load_dotenv

# Reuse your existing auth helper
try:
    from helper import get_valid_token
except ImportError:
    raise ImportError("Could not import get_valid_token from helper.")

load_dotenv()

SC_APP_KEY = os.getenv("SUNGROW_APP_KEY")
SC_APP_SECRET = os.getenv("SUNGROW_APP_SECRET")
API_BASE = "https://gateway.isolarcloud.com.hk"

@tool
async def get_plant_details(ps_id: str):
    """
    Fetch real-time data for a SPECIFIC solar plant using its ID.
    Useful for getting current power (kW), daily energy (kWh), and CO2 reduction.
    
    Args:
        ps_id (str): The ID of the power station (e.g., "1711005").
    """
    # 1. Auth
    try:
        access_token = await get_valid_token()
    except Exception as e:
        return f"Error retrieving Access Token: {e}"

    # 2. API Endpoint: queryPsDetail (Generic details) or queryRealTimeData
    # Let's use 'queryPsDetail' for general status
    url = f"{API_BASE}/openapi/platform/queryPsDetail"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-access-key": SC_APP_SECRET or ""
    }
    
    payload = {
        "appkey": SC_APP_KEY,
        "ps_id": ps_id
    }

    # 3. Request
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            data = response.json()
    except Exception as e:
        return f"API Connection Failed: {e}"

    if data.get("result_code") != '1':
        return f"iSolarCloud Error: {data.get('result_msg')}"

    # 4. Parse Data
    # The structure usually has 'curr_power' (Real-time kW) and 'daily_energy' (kWh)
    res = data.get("result_data", {})
    
    name = res.get("ps_name", "Unknown")
    # Note: Keys might vary slightly based on your specific API permissions
    # Common keys: 'curr_power', 'day_energy', 'total_energy', 'co2_reduction'
    current_power = res.get("curr_power", 0)  # kW
    daily_yield = res.get("day_energy", 0)    # kWh
    total_yield = res.get("total_energy", 0)  # kWh
    
    # 5. Format for LLM
    report = f"""
    **Plant Status Report: {name}**
    -  Current Output: {current_power} kW
    -  Yield Today: {daily_yield} kWh
    -  Total Yield: {total_yield} kWh
    -  Location: {res.get("ps_location", "N/A")}
    """
    return report
