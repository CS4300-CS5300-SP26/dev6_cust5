import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RENTCAST_API_KEY")

def get_properties(location, property_type=None, min_price=None, max_price=None):
    if not API_KEY:
        print("WARNING: RENTCAST_API_KEY is not set.")
        return []

    url = "https://api.rentcast.io/v1/listings/rental/long-term" 

    headers = {"X-Api-Key": API_KEY}

    parts = location.split(",")
    city = parts[0].strip()
    state = parts[1].strip() if len(parts) > 1 else "CO"

    params = {
        "city": city,
        "state": state,
        "limit": 10,
        "status": "Active",
    }

    if property_type and property_type.lower() not in ("", "any type"):
        params["propertyType"] = property_type.capitalize()
    if min_price:
        params["minPrice"] = min_price
    if max_price and max_price != 999999:
        params["maxPrice"] = max_price

    response = requests.get(url, headers=headers, params=params)

    # For Debugging
    print("Rentcast status:", response.status_code) 
    print("Rentcast response:", response.text[:300])

    if response.status_code == 200:
        data = response.json()
        return data if isinstance(data, list) else data.get("data", [])

    return []