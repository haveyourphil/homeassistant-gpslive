import requests

class GpsLiveAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.gpslive.app/api/v1"

    async def get_location(self):
        response = requests.get(f"{self.base_url}/location", params={"api_key": self.api_key})
        return response.json()