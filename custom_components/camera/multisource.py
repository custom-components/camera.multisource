"""
A camera platform that generate a camera feed from multiple sources.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/camera.multisource
"""
import logging
import os
import base64
import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.camera import (PLATFORM_SCHEMA, Camera)

__version__ = '0.0.1'
_LOGGER = logging.getLogger(__name__)

CONF_NAME = 'name'
CONF_URLS = 'urls'
CONF_IMAGES = 'images'
CONF_DIRS = 'dirs'

PLATFOM_NAME = 'Multisource'
PLATFORM_DATA = str(PLATFOM_NAME).lower() + '_data'
PLATFORM_IMAGES = str(PLATFOM_NAME).lower() + '_images'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=PLATFOM_NAME): cv.string,
    vol.Optional(CONF_URLS, default='None'):
        vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_IMAGES, default='None'):
        vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_DIRS, default='None'):
        vol.All(cv.ensure_list, [cv.string]),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Camera that works with local files."""
    name = config.get(CONF_NAME)
    urls = config.get(CONF_URLS)
    images = config.get(CONF_IMAGES)
    dirs = config.get(CONF_DIRS)
    camera = WebimagesCamera(hass, name, urls, images, dirs)
    add_devices([camera])


class WebimagesCamera(Camera):
    """Representation of the camera."""

    def __init__(self, hass, name, urls, images, dirs):
        """Initialize Webimages Camera component."""
        super().__init__()
        self.hass = hass
        self._name = name
        self._urls = urls
        self._images = images
        self._dirs = dirs
        self.is_streaming = False
        self._config_path = self.hass.config.path()
        self.hass.data[PLATFORM_DATA] = {}
        self.hass.data[PLATFORM_DATA]['count'] = 0
        self.gather_images()


    def camera_image(self):
        """Return image response."""
        return self.update_feed()

    def update_feed(self):
        """Download new image if needed"""
        total = len(self.hass.data[PLATFORM_IMAGES])
        count = self.hass.data[PLATFORM_DATA]['count']
        if count == (total):
            self.hass.data[PLATFORM_DATA]['count'] = 0
        else:
            self.hass.data[PLATFORM_DATA]['count'] = count + 1
        image = self.hass.data[PLATFORM_IMAGES][count]
        return base64.b64decode(image)

    def gather_images(self):
        """Gather images from the different sources"""
        self.hass.data[PLATFORM_IMAGES] = []
        if self._urls[0] == 'None' and self._images[0] == 'None' and self._dirs[0] == 'None':
            _LOGGER.critical('You need to at least define one of urls, dirs, images.')
        else:
            if not self._urls[0] == 'None':
                self.get_urls()
            if not self._images[0] == 'None':
                self.get_images()
            if not self._dirs[0] == 'None':
                self.get_dirs()
    def get_urls(self):
        """Get images from urls"""
        for url in self._urls:
            try:
                file_source = requests.get(url)
                if file_source.status_code == 200:
                    _LOGGER.debug('Adding %s', url)
                    self.hass.data[PLATFORM_IMAGES].append(base64.b64encode(file_source.content))
            except:
                _LOGGER.error('Failed to fetch image from "%s"', url)

    def get_images(self):
        """Get images from images"""
        for image in self._images:
            imagefile = self._config_path + image
            if os.path.isfile(imagefile):
                _LOGGER.debug('Adding %s', imagefile)
                with open(imagefile, 'rb') as image_file:
                    self.hass.data[PLATFORM_IMAGES].append(base64.b64encode(image_file.read()))
                image_file.close()
            else:
                _LOGGER.error('Could not read imagefile: %s', imagefile)

    def get_dirs(self):
        """Get images from dirs"""
        for directory in self._dirs:
            fulldirpath = self._config_path + directory
            if os.path.isdir(fulldirpath):
                for image in os.listdir(fulldirpath):
                    _LOGGER.debug('Adding %s from %s', image, fulldirpath)
                    imagefile = fulldirpath + '/' + image
                    with open(imagefile, 'rb') as image_file:
                        self.hass.data[PLATFORM_IMAGES].append(base64.b64encode(image_file.read()))
                    image_file.close()
            else:
                _LOGGER.error('Could not find directory: %s', fulldirpath)

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name
