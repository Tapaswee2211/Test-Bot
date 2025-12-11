# backend/tools.py
from tavily import TavilyClient
from pydantic import BaseModel, Field
import openmeteo_requests
import numpy as np
from langchain_core.messages import AIMessage
from dotenv import load_dotenv
load_dotenv()


# Initialize Open-Meteo client once
openmeteo = openmeteo_requests.Client()
tavily = TavilyClient()

class SearchArgs(BaseModel):
    query : str = Field(..., description="Search query Text")

class WeatherArgs(BaseModel):
    latitude: float = Field(12.97, description="Latitude of the location")
    longitude: float = Field(12.97, description="longitude of the location")
    pass

def search_web(query : str):
    """ Perfrom a real internet search using Tavily"""
    try:
        result = tavily.search(query=query, max_results = 5)
        summaries = []
        for r in result.get("results", []):
            title = r.get("title", "No title")
            link = r.get("url", "No link")
            snippet = r.get("content", "")
            summaries.append(f"**{title}** \n{snippet} \n {link}")
        return "\n\n".join(summaries)
    except Exception as e:
        return AIMessage(content=f"Tavily search Failed: {e}")
    

def get_weather_forecast(latitude: float, longitude: float):
    """Fetch current temp, humidity, and hourly forecast from Open-Meteo."""
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "precipitation", "wind_speed_10m"],
        "current": ["temperature_2m", "relative_humidity_2m"],
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
    except Exception as e:
        return AIMessage(content=f" Error fetching weather: {e}")

    # ---- Current Values ----
    current = response.Current()
    temp_now = current.Variables(0).Value()
    humidity_now = current.Variables(1).Value()

    # ---- Hourly Forecast ----
    hourly = response.Hourly()
    temp_series = hourly.Variables(0).ValuesAsNumpy()
    prec_series = hourly.Variables(1).ValuesAsNumpy()
    wind_series = hourly.Variables(2).ValuesAsNumpy()

    # Get next 3 values
    forecast = []
    for i in range(3):
        forecast.append(
            f"• Temp: {temp_series[i]:.1f}°C | "
            f"Wind: {wind_series[i]:.1f} km/h | "
            f"Rain: {prec_series[i]:.1f} mm"
        )

    report = f"""
 **Weather Report**

 Location: {response.Latitude():.2f}, {response.Longitude():.2f}
 Current Time: {current.Time()}

 Current Temperature: **{temp_now:.1f}°C**
 Humidity: **{humidity_now:.1f}%**

 **Next 3 Hours Forecast**
{chr(10).join(forecast)}
"""

    return AIMessage(content=report)


# Register tools here
TOOLS = {
    "get_weather_forecast": (get_weather_forecast, WeatherArgs),
    "brave_search" : (search_web, SearchArgs),
}

