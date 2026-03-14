import requests

API_KEY = "YOUR_API_KEY"

def get_properties(city):
    url = "https://api.rentcast.io/v1/properties"

    headers = {
        "X-Api-Key": API_KEY
    }

    params = {
        "city": city,
        "limit": 10
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()

    return []