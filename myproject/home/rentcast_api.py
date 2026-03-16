import requests
import os

API_KEY = os.getenv("RENTCAST_API_KEY")

def get_properties(location):

    if not API_KEY:
        return []

    url = "https://api.rentcast.io/v1/properties"

    headers = {
        "X-Api-Key": API_KEY
    }

    # Split "Austin, TX"
    parts = location.split(",")

    city = parts[0].strip()
    state = parts[1].strip() if len(parts) > 1 else None

    params = {
        "city": city,
        "state": state,
        "limit": 5
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()

    return []