import asyncio
import os
import httpx
import json
from dotenv import load_dotenv

# Import your existing token helper
# Ensure helper.py is in the same directory or adjust import
try:
    from backend.app.helper import get_valid_token
except ImportError:
    print("CRITICAL: Could not import 'get_valid_token' from helper.py")
    exit(1)

load_dotenv()

# Configuration
SC_APP_KEY = os.getenv("SUNGROW_APP_KEY")
SC_APP_SECRET = os.getenv("SUNGROW_APP_SECRET")
API_BASE = "https://gateway.isolarcloud.com.hk"

async def test_post_plants():
    print("--- 1. Testing Authentication ---")
    try:
        access_token = await get_valid_token()
        print(f"✅ Token retrieved: {access_token[:10]}... (truncated)")
    except Exception as e:
        print(f" Failed to get token: {e}")
        return

    print("\n--- 2. Preparing POST Request ---")
    
    # EXACT payload used in your tool
    # Try removing 'ps_type' or 'valid_flag' if you suspect they are too strict
    payload = {
        "appkey": SC_APP_KEY,
        "page": 1,
        "size": 10,
        "ps_type": "1,3,4,5", 
        "valid_flag": "1,3",
        "ps_name": "" 
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-access-key": SC_APP_SECRET or ""
    }

    print(f"Target URL: {API_BASE}/openapi/platform/queryPowerStationList")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    print("\n--- 3. Sending Request ---")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE}/openapi/platform/queryPowerStationList",
                headers=headers,
                json=payload,
                timeout=10.0
            )
            
            print(f"Status Code: {response.status_code}")
            
            # Attempt to parse JSON
            data = response.json()
            print("\n--- 4. Raw API Response ---")
            print(json.dumps(data, indent=2))
            
            # Simple Analysis
            if data.get("result_code") == '1':
                count = data.get("result_data", {}).get("rowCount", 0)
                page_list = data.get("result_data", {}).get("pageList", [])
                print(f"\n✅ SUCCESS: Found {count} plants (List size: {len(page_list)})")
            else:
                print(f"\n API ERROR: {data.get('result_msg')}")

        except httpx.HTTPStatusError as e:
            print(f" HTTP Error: {e.response.text}")
        except Exception as e:
            print(f" Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_post_plants())
