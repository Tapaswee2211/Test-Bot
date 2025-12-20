from dotenv import load_dotenv 
import os 
import httpx
from langchain_core.tools import tool
from sqlalchemy import except_
from helper import get_valid_token, load_token, save_token


load_dotenv()

scid = os.getenv("SUNGROW_APP_KEY")
scs = os.getenv("SUNGROW_APP_SECRET")
api = "https://gateway.isolarcloud.com.hk"


@tool
async def list_solar_plants(plant_name: str=""):
    """
    Fetches the list of solar power plants from iSolarCloud
    Args:
        plant_name (str) : Optional. Filter by the name of the power station.
            Leave empty to list all the plants
    """
    access_token = await get_valid_token()
    payload = {
        "appkey" : scid,
        "page" : 1, 
        "size" : 10, 
        "ps_type" : "1,3,4,5", 
        "ps_name" : plant_name, 
        "valid_flag" : "1,3"
    }
    headers={
        "Authorization" : f"Bearer {access_token}",
        "Content-Type" : "application/json",
        "x-access-key" : scs or ""
    }
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{api}/openapi/platform/queryPowerStationList",
                headers=headers,
                json = payload
            )
        data = res.json()
    except Exception as e:
        return f"API Connection Failed : {e}"

    if data.get("result_code") != '1':
        return f"iSolarCloud API Error: {data.get('result_msg', "Unknown Error")}"
    result_data = data.get("result_data", {})
    plants = result_data.get("plantList", [])
    if not plants:
        return "No Solar plants found matching criteria"

    output_lines = ["**Solar Plants Found: **"]

    for p in plants:
        name = p.get("ps_name", "Unknown Name")
        location = p.get("ps_location", "Unknown Location")
        install_date = p.get("install_date", "N/A")

        status_code = p.get("online_status")
        if status_code == 1:
            status_str = "Online"
        else:
            status_str="Offline"
        line= (
            f"- {name} -\n"
            f"- Status: {status_str} -\n"
            f"- Location: {location} -\n"
            f"- Installed: {install_date} -\n"
        )
        output_lines.append(line)

    return "\n".join(output_lines)
