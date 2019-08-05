"""
VarnaTrafik sensor to query events for a specified stop.
"""
import asyncio
import logging
from datetime import timedelta, datetime
import requests
import json
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

REQUIREMENTS = [ ]

_LOGGER = logging.getLogger(__name__)
_RESOURCE = 'https://varnatraffic.com/Ajax/FindStationDevices'

CONF_ATTRIBUTION = "Data provided by Varna Traffic"
CONF_STOP_ID = 'stopId'
CONF_STOP_NAME = 'stopName'
CONF_SHOW_MODE = 'show_mode'
CONF_SCHEDULE_MAX = 'max_schedule'
CONF_INTERVAL = 'interval'
CONF_LINES = 'monitored_lines'

DEFAULT_NAME = "Varna Public Transport"
DEFAULT_ICON = "mdi:bus"

#SCAN_INTERVAL = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_STOP_ID): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_STOP_NAME, default='Bus Stop'): cv.string,
    vol.Optional(CONF_SHOW_MODE, default='all'): cv.string,
    vol.Optional(CONF_SCHEDULE_MAX, default=10): cv.positive_int,
    vol.Optional(CONF_INTERVAL, default=30): cv.positive_int,
    vol.Optional(CONF_LINES, default=None): vol.All(cv.ensure_list, [cv.positive_int]),
})

@asyncio.coroutine
async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    name = config.get(CONF_NAME)
    stopid = config.get(CONF_STOP_ID)
    stopname = config.get(CONF_STOP_NAME)
    show_mode = config.get(CONF_SHOW_MODE)
    max_schedule = config.get(CONF_SCHEDULE_MAX)
    monitored_lines = config.get(CONF_LINES)
    
    session = async_get_clientsession(hass)
    dev = []
    dev.append(VarnaTrafikTransportSensor(name, stopid, stopname, show_mode, max_schedule, hass, monitored_lines))
    async_add_devices(dev,update_before_add=True)
    
    if config.get(CONF_INTERVAL) < 10:
        interval = 10
    else: 
        interval = config.get(CONF_INTERVAL)

    data = VarnaTrafikTransportSensorData(hass, stopid, dev, interval, show_mode, max_schedule)
    # schedule the first update in 1 second from now - initial run:
    await data.schedule_update(1)

class VarnaTrafikTransportSensor(Entity):
    """Implementation of an Varnatrafik sensor."""

    def __init__(self, name, stopid, stopname, show_mode, max_schedule, hass, monitored_lines):
        """Initialize the sensor."""
        self._name = name
        self._stopid = stopid
        self._stopname = stopname
        self._mode = show_mode
        self._schedule_max = max_schedule
        self._state = None
        self._data = None
        self._icon = DEFAULT_ICON
        self._hass = hass
        self._monitored_lines = monitored_lines

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
    
    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attr = {}
        attr["StopName"] = self._stopname
        if self._data is not None:
            if self._mode == 'live' or self._mode == 'all':
                lines_count = len(self._data["liveData"])
                #Grab all bus lines nodes from live data if there are any
                if lines_count != 0:
                    attr['stop_lines'] = {}
                    i = 0
                    k = 0
                    while i < lines_count:
                      if len(self._monitored_lines) != 0:
                          
                          if self._data["liveData"][i]["line"] in self._monitored_lines:
                              attr['stop_lines'].setdefault('line_' + str(k), {})
                              attr['stop_lines']['line_' + str(k)]['LineNumber'] = self._data["liveData"][i]["line"]
                              attr['stop_lines']['line_' + str(k)]['arrivalTime'] = self._data["liveData"][i]["arriveTime"]
                              attr['stop_lines']['line_' + str(k)]['distanceLeft'] = self._data["liveData"][i]["distanceLeft"]
                              if 'arriveIn' in self._data["liveData"][i]:
                                  arriveIn = self._data["liveData"][i]["arriveIn"]
                              else:
                                  arriveIn = ''
                              attr['stop_lines']['line_' + str(k)]['arriveIn'] = arriveIn
                              
                              if 'delay' in self._data["liveData"][i]:
                                  delay = self._data["liveData"][i]["delay"]
                              else:
                                  delay = ''
                              attr['stop_lines']['line_' + str(k)]['delay'] = delay
                              attr['stop_lines']['line_' + str(k)]['vehicleKind'] = self._data["liveData"][i]["deviceKind"]
                              attr['stop_lines']['line_' + str(k)]['vehicleExtras'] = self._data["liveData"][i]["extrasFlags"]
                              k +=1
                          attr['lines'] = len(attr['stop_lines'])
                      else:
                          attr['stop_lines'].setdefault('line_' + str(i), {})
                          attr['stop_lines']['line_' + str(i)]['LineNumber'] = self._data["liveData"][i]["line"]
                          attr['stop_lines']['line_' + str(i)]['arrivalTime'] = self._data["liveData"][i]["arriveTime"]
                          attr['stop_lines']['line_' + str(i)]['distanceLeft'] = self._data["liveData"][i]["distanceLeft"]
                          if 'arriveIn' in self._data["liveData"][i]:
                              arriveIn = self._data["liveData"][i]["arriveIn"]
                          else:
                              arriveIn = ''
                          attr['stop_lines']['line_' + str(i)]['arriveIn'] = arriveIn
                          
                          if 'delay' in self._data["liveData"][i]:
                              delay = self._data["liveData"][i]["delay"]
                          else:
                              delay = ''
                          attr['stop_lines']['line_' + str(i)]['delay'] = delay
                          attr['stop_lines']['line_' + str(i)]['vehicleKind'] = self._data["liveData"][i]["deviceKind"]
                          attr['stop_lines']['line_' + str(i)]['vehicleExtras'] = self._data["liveData"][i]["extrasFlags"]
                          
                          attr['lines'] = lines_count
                      i += 1
                else:
                    attr['stop_lines'] = {}
                    attr['lines'] = 0
            
            if self._mode == 'schedule' or self._mode == 'all':
                
                if 'schedule' in self._data:
                    schedules_lines_count = len(self._data["schedule"])
                   
                    if schedules_lines_count != 0:
                        attr['stop_lines_schedules'] = {}
                        i = 0
                        k = 0
                        while i < schedules_lines_count:
                          if len(self._monitored_lines) != 0:
                              
                              if self._data["schedule"][i]["line"] in self._monitored_lines:
                                  attr['stop_lines_schedules'].setdefault('line_' + str(k), {})['line_number'] = self._data["schedule"][i]["line"]
                                  attr['stop_lines_schedules'].setdefault('line_' + str(k), {})['line_times'] = {}
                                 
                                  #check if max results doesn't exceed available data
                                  max_result = self._schedule_max if len(self._data["schedule"][i]["data"]) >= self._schedule_max else len(self._data["schedule"][i]["data"])  
                                  n = 0
                                  while n < max_result:
                                    attr['stop_lines_schedules']['line_' + str(k)]['line_times'][str(n)] = self._data["schedule"][i]["data"][n]["text"]                              
                                    n += 1
                                  k += 1
                              
                              attr["lines_schedules"] = len(attr['stop_lines_schedules'])
                                
                          else:      
                              attr['stop_lines_schedules'].setdefault('line_' + str(i), {})['line_number'] = self._data["schedule"][i]["line"]
                              attr['stop_lines_schedules'].setdefault('line_' + str(i), {})['line_times'] = {}
                             
                              #check if max results doesn't exceed available data
                              max_result = self._schedule_max if len(self._data["schedule"][i]["data"]) >= self._schedule_max else len(self._data["schedule"][i]["data"])  
                              n = 0
                              while n < max_result:
                                attr['stop_lines_schedules']['line_' + str(i)]['line_times'][str(n)] = self._data["schedule"][i]["data"][n]["text"]                              
                                n += 1
                              
                              attr['lines_schedules'] = schedules_lines_count
                          i += 1
                    else:
                        attr['stop_lines_schedules'] = {}
                        attr['lines_schedules'] = 0
            
            _LOGGER.debug(attr)
            return attr
        _LOGGER.debug("No data")

    def load_data(self, data):
        self._state = 1        
        self._data = data
        return True



class VarnaTrafikTransportSensorData:
    def __init__(self, hass, stopid, dev, interval, show_mode, max_schedule):
        self._data = {}
        self._hass = hass
        self._stopid = stopid
        self._dev = dev
        self.state = None
        self._delay = interval
        self._mode = show_mode
        self._max_results = max_schedule

    async def update_devices(self):
        """Update all devices/sensors."""
        if self._dev:
            tasks = []
            # Update all devices
            for dev in self._dev:
                if dev.load_data(self._data):
                    tasks.append(dev.async_update_ha_state())

            if tasks:
                await asyncio.wait(tasks)

    async def schedule_update(self, second=10):
        """Schedule an update after seconds."""
        """
            If we only getting lines schedule, no need for constant pooling. 
            Some aprox timing calculations based on nubers of results setted for schedule to return.
         
           Also since city of Varna doesn't have public transport trough the night, there is no need to pool at that time
        """
        if dt_util.parse_time('23:59:00') <= dt_util.parse_time(dt_util.now().strftime('%H:%M:%S')) <= dt_util.parse_time('04:59:59'):
            future = datetime.combine(dt_util.parse_datetime(dt_util.now().strftime('%Y-%m-%d %H:%M:%S%z')), dt_util.parse_time('04:59:59')) #future hour - 5:00 in the morning, when the first buses goes from the end stops
            current = datetime.now() #now
            tdelta = future - current #return the hours diffrence between the two times, we do calculation here to set next execute after N - hours
            if tdelta.days < 0: #our interval crosses midnight end time is always earlier than the start time resulting timedalta been negative, lets account for that bellow
                tdelta = timedelta(days=0,
                            seconds=tdelta.seconds, microseconds=tdelta.microseconds)
            nxt = dt_util.utcnow() + tdelta
        else:
            if self._mode == 'schedule':
                if second == 1:
                    nxt = dt_util.utcnow() + timedelta(seconds=1)
                else: 
                    if self._max_results <= 10:
                        nxt = dt_util.utcnow() + timedelta(hours=1)
                    elif self._max_results <= 20:
                        nxt = dt_util.utcnow() + timedelta(hours=2)
                    elif self._max_results <= 40:
                        nxt = dt_util.utcnow() + timedelta(hours=4)
                    else:
                        nxt = dt_util.utcnow() + timedelta(hours=6)
            else:
                nxt = dt_util.utcnow() + timedelta(seconds=second)
        _LOGGER.debug("Scheduling next update at %s. UTC time", nxt.strftime('%H:%M:%S'))
        async_track_point_in_utc_time(self._hass, self.async_update, nxt)
        

    @asyncio.coroutine
    async def async_update(self, *_):
        """Get the latest data from varnatraffic.com"""
        _LOGGER.debug("Bus stop update for stop id:" + self._stopid)
        
        params = {}
        params['stationId'] = self._stopid
        params['format'] = 'json'
        
        response = requests.get(_RESOURCE, params, timeout=20)
     
        # No valid request, throw error
        if response.status_code != 200:
            _LOGGER.error("Bus stop update error! API response " + str(response.status_code))
            self.state = None
            self._data = None
            self._delay = 20
        else:
            # Valid request, return data
            # Parse the result as a JSON object
            result = response.json()
            
            self.state = 1
            self._data = result
        
        await self.update_devices()
        await self.schedule_update(self._delay)

