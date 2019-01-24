"""
A camera platform that generate a camera feed from multiple sources.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/camera.multisource

@todo Convert to async.
@todo Implement checking files and directories against whitelist_external_dirs.
"""
import asyncio
import logging
from datetime import timedelta
from random import choice

import aiohttp
import async_timeout
import os
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_NAME, ATTR_ENTITY_ID)
from homeassistant.components.camera import (PLATFORM_SCHEMA, DOMAIN, Camera)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service import extract_entity_ids
from homeassistant.util import Throttle


__version__ = '0.3.0'
_LOGGER = logging.getLogger(__name__)

CONF_INTERVAL = 'interval'
CONF_IMAGES = 'images'

PLATFORM_NAME = 'Multisource'

SERVICE_RELOAD = 'multisource_reload_images'

MULTISOURCE_DATA = "multisource"
ENTITIES = "entities"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=PLATFORM_NAME): cv.string,
    vol.Optional(CONF_INTERVAL, default=timedelta(seconds=300)):
        vol.All(cv.time_period, cv.positive_timedelta),
    vol.Required(CONF_IMAGES):
        vol.All(cv.ensure_list, [vol.Any(cv.string, cv.isfile, cv.isdir)]),
})

SERVICE_RELOAD_SCHEMA = vol.Schema({
    ATTR_ENTITY_ID: cv.entity_ids,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up an Multisource Camera."""

    def reload_images_service(service):
        """Handle reload images service call."""
        _LOGGER.debug("Reloading images with service call.")

        all_cameras = hass.data[MULTISOURCE_DATA][ENTITIES]
        entity_ids = extract_entity_ids(hass, service)
        target_cameras = []
        if not entity_ids:
            target_cameras = all_cameras
        else:
            target_cameras = [camera for camera in all_cameras
                              if camera.entity_id in entity_ids]
        for camera in target_cameras:
            camera.reload_images()

    hass.services.async_register(DOMAIN, SERVICE_RELOAD, reload_images_service,
                                 schema=SERVICE_RELOAD_SCHEMA)

    if discovery_info:
        config = PLATFORM_SCHEMA(discovery_info)
    async_add_devices([MultisourceCamera(hass, config)], True)


class MultisourceCamera(Camera):
    """Representation of the camera."""

    def __init__(self, hass, config):
        """Initialize Multisource Camera component."""
        super().__init__()
        self.hass = hass
        self._name = config[CONF_NAME]
        self._images = config[CONF_IMAGES]
        self._image = None
        self._data = []
        self._interval = config[CONF_INTERVAL]
        self.is_streaming = False
        self.update_feed = Throttle(self._interval)(self._update_feed)
        self.reload_images()

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    async def async_added_to_hass(self):
        """Callback when entity is added to hass."""
        if MULTISOURCE_DATA not in self.hass.data:
            self.hass.data[MULTISOURCE_DATA] = {}
            self.hass.data[MULTISOURCE_DATA][ENTITIES] = []
        self.hass.data[MULTISOURCE_DATA][ENTITIES].append(self)

    @asyncio.coroutine
    def async_camera_image(self):
        self.update_feed()
        return self._image

    def reload_images(self):
        """Get images from config."""
        def load_image_dir(image_dir):
            """Get images from dir."""
            image_data = []
            image_dir = image_dir.rstrip('/')
            for image in os.listdir(image_dir):
                image_file = load_image_file(image_dir + '/' + image)
                if image_file:
                    image_data.append(image_file)
            return image_data

        def load_image_file(image_file):
            """Get image from file."""
            with open(image_file, 'rb') as f:
                return f.read()

        @asyncio.coroutine
        def load_image_url(image_url):
            """Get image from URL."""
            try:
                websession = async_get_clientsession(self.hass)
                with async_timeout.timeout(10, loop=self.hass.loop):
                    response = yield from websession.get(image_url)
                image_data = yield from response.read()
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout getting camera image")
                return None
            except aiohttp.ClientError as err:
                _LOGGER.error("Error getting new camera image: %s", err)
                return None

            return image_data

        self._data = []
        for image in self._images:
            if os.path.isdir(image):
                _LOGGER.debug("Adding dir '%s'", image)
                image_data = load_image_dir(image)
            elif os.path.isfile(image):
                _LOGGER.debug("Adding file '%s'", image)
                image_data = [load_image_file(image)]
            else:
                _LOGGER.debug("Adding URL '%s'", image)
                image_data = [load_image_url(image)]

            if image_data:
                self._data.extend(image_data)

    def _update_feed(self):
        """Update image if interval has passed."""
        _LOGGER.debug("Updating camera feed.")
        self._image = choice(self._data)
