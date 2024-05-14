from homeassistant.helpers.entity import Entity
from . import DOMAIN

class GpsLiveSensor(Entity):
    def __init__(self, api):
        self._api = api
        self._state = None

    @property
    def name(self):
        return "GPSLive"

    @property
    def state(self):
        return self._state

    async def async_update(self):
        # Call API and update the state
        data = await self._api.get_location()
        self._state = data['location']