import openmeteo_requests
import numpy as np
from langchain_core.tools import tool

openmeteo = openmeteo_requests.Client()

@tool
def get_weather_forecast(latitude: float, longitude: float):
    """
    Fetch Current temp, hum, and hourly forecast from open-meteo
    Args:
        latitude: float (e.g. 12.97)
        longitude: float (e.g. 77.59)
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude" : latitude,
        "longitude" : longitude,
        "hourly" : ["temperature_2m", "precipitation", "wind_speed_10m"],
        "current" : ["temperature_2m", "relative_humidity_2m"],
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
    except Exception as e : 
        return f"Error fetching weather : {e}"
    
    current = response.Current()
    temp_now = current.Variables(0).Value()
    humidity_now = current.Variables(1).Value()

    hourly = response.Hourly()
    temp_series = hourly.Variables(0).ValuesAsNumpy()
    prec_series = hourly.Variables(1).ValuesAsNumpy()
    wind_series = hourly.Variables(2).ValuesAsNumpy()

    forecast = []
    for i in range(3):
        forecast.append(
            f" Temp : {temp_series[i]:.1f} C | "
            f" Wind : {wind_series[i]:.1f} Km/h | "
            f" Rain : {prec_series[i]:.1f} mm"
        )
    report = f"""
    Weather Data Retrieved: 
    Location : {response.Latitude():.2f}, {response.Longitude():.2f}
    Current Time : {current.Time()} 
    Current Temperature : {temp_now:.1f} C
    Humidity : {humidity_now:.1f}%
    
    Next 3 Hours Forecast:
    {chr(10).join(forecast)}
    """
    return report





