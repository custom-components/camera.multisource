"""
A camera platform that generate a camera feed from multiple sources.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/camera.multisource

@todo Convert to async.
@todo Implement checking files and directories against whitelist_external_dirs.
"""
import logging
import os
import time
import random
import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.camera import (PLATFORM_SCHEMA, DOMAIN, Camera)

__version__ = '0.2.0'
_LOGGER = logging.getLogger(__name__)

CONF_NAME = 'name'
CONF_INTERVAL = 'interval'
CONF_IMAGES = 'images'

PLATFORM_NAME = 'Multisource'

DEFAULT_INTERVAL = 300

SERVICE_RELOAD = 'multisource_reload_images'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=PLATFORM_NAME): cv.string,
    vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): cv.positive_int,
    vol.Required(CONF_IMAGES):
        vol.All(cv.ensure_list, [vol.Any(cv.string, cv.isfile, cv.isdir)]),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Camera that works with local files."""
    name = config.get(CONF_NAME)
    interval = config.get(CONF_INTERVAL)
    images = config.get(CONF_IMAGES)

    camera = MultisourceCamera(hass, name, interval, images)

    def reload_images_service(call):
        """Reload images."""
        _LOGGER.debug("Reloading images with service call.")
        camera.load_images()
        return True

    hass.services.register(DOMAIN, SERVICE_RELOAD, reload_images_service)
    add_devices([camera])

class MultisourceCamera(Camera):
    """Representation of the camera."""

    def __init__(self, hass, name, interval, images):
        """Initialize Multisource Camera component."""
        super().__init__()
        self.hass = hass
        self._name = name
        self._images = images
        self._image = None
        self._data = []
        self._lastchanged = 0
        self._interval = int(interval)
        self.is_streaming = False
        self._config_path = self.hass.config.path()
        self.load_images()
        self.update_feed()

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    def camera_image(self):
        """Return image response."""
        self.update_feed()
        return self._image

    def update_feed(self):
        """Update image if interval has passed."""
        if time.time() - self._lastchanged >= self._interval:
            _LOGGER.debug("Updating camera feed.")
            self._lastchanged = time.time()
            self._image = random.choice(self._data)

    def load_images(self):
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

        def load_image_url(image_url):
            """Get image from URL."""
            try:
                file_source = requests.get(image_url)
                if file_source.status_code == 200:
                    return file_source.content
            except requests.exceptions.ConnectionError:
                _LOGGER.error("Could not download image from '%s'", image_url)
            return None

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
