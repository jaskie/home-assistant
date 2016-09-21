"""
Support for building a Raspberry Pi blind roller motor cover in HA.

"""

import logging
from time import sleep
import voluptuous as vol

from homeassistant.components.cover import CoverDevice
import homeassistant.components.rpi_gpio as rpi_gpio
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_FRIENDLY_NAME)

RELAY_TIME = 'relay_time'
DEFAULT_RELAY_TIME = 30
DEFAULT_INVERT_LOGIC = False
DEPENDENCIES = ['rpi_gpio']

_LOGGER = logging.getLogger(__name__)

_COVERS_SCHEMA = vol.All(
     cv.ensure_list,
     [
         vol.Schema({
             'name': str,
             'relay_pin_up': int,
             'relay_pin_down': int,
         })
     ]
 )
PLATFORM_SCHEMA = vol.Schema({
     'platform': str,
     vol.Required('covers'): _COVERS_SCHEMA,
     vol.Optional(RELAY_TIME, default=DEFAULT_RELAY_TIME): vol.Coerce(int),
     vol.Optional('invert_logic', default=DEFAULT_INVERT_LOGIC): vol.Coerce(bool),
 })


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup the cover platform."""
    relay_time = config.get(RELAY_TIME, DEFAULT_RELAY_TIME)
    invert_logic = config.get('invert_logic', DEFAULT_INVERT_LOGIC)
    covers = []
    covers_conf = config.get('covers')

    for cover in covers_conf:
        covers.append(RPiGPIORoller(cover['name'], cover['relay_pin_up'],
                                   cover['relay_pin_down'],
                                   relay_time,
                                   invert_logic))
    add_devices_callback(covers)


# pylint: disable=abstract-method
class RPiGPIORoller(CoverDevice):
    """Representation of a Raspberry cover."""

    # pylint: disable=too-many-arguments
    def __init__(self, name, relay_pin_up, relay_pin_down, relay_time, invert_logic):
        """Initialize the cover."""
        self._name = name
        self._state = None
        self._relay_pin_up = relay_pin_up
        self._relay_pin_down = relay_pin_down
        self._relay_time = relay_time
        self._invert_logic = invert_logic
        rpi_gpio.setup_output(self._relay_pin_up)
        rpi_gpio.write_output(self._relay_pin_up, 1 if self._invert_logic else 0)
        rpi_gpio.setup_output(self._relay_pin_down)
        rpi_gpio.write_output(self._relay_pin_down, 1 if self._invert_logic else 0)

    @property
    def unique_id(self):
        """Return the ID of this cover."""
        return "{}.{}".format(self.__class__, self._name)

    @property
    def name(self):
        """Return the name of the cover if any."""
        return self._name

    def close_cover(self):
        """Close the cover."""
        rpi_gpio.write_output(self._relay_pin_down, 0 if self._invert_logic else 1)
        rpi_gpio.write_output(self._relay_pin_up, 1 if self._invert_logic else 0)
        sleep(self._relay_time)
        rpi_gpio.write_output(self._relay_pin_down, 1 if self._invert_logic else 0)
        self._state = 0
        self.update_ha_state()

    def open_cover(self):
        """Open the cover."""
        rpi_gpio.write_output(self._relay_pin_up, 0 if self._invert_logic else 1)
        rpi_gpio.write_output(self._relay_pin_down, 1 if self._invert_logic else 0)
        sleep(self._relay_time)
        rpi_gpio.write_output(self._relay_pin_up, 1 if self._invert_logic else 0)
        self._state = 100
        self.update_ha_state()

    def stop_cover(self):
        """Stop the cover."""
        rpi_gpio.write_output(self._relay_pin_up, 1 if self._invert_logic else 0)
        rpi_gpio.write_output(self._relay_pin_down, 1 if self._invert_logic else 0)
        self._state = None
        self.update_ha_state()

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self.current_cover_position is not None:
            if self.current_cover_position > 0:
                return False
            else:
                return True
