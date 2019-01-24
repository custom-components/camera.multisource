# camera.multisource

A camera platform that generate a camera feed from multiple image sources.

This platform will display a feed that rotates through a list of images at a
set interval.

To get started put `/custom_components/multisource/camera.py` here:
`<config directory>/custom_components/multisource/camera.py`

**Example `configuration.yaml`:**

```yaml
camera:
  - platform: multisource
    name: "Image Gallery"
    interval: 10
    images:
      - https://example.com/image1.jpg
      - https://example.com/image2.png
      - /config/www/images/dir1
      - /config/www/images/dir2
      - /config/www/image1.jpg
      - /config/www/image2.png
```

**Configuration variables:**

key | description
:--- | :---
**platform (Required)** | The camera platform name (`multisource`).
**name (Optional)** | Set the a custom name for the platform entity.
**interval (Optional)** | The interval (in seconds) to display each image, defaults to `300`.
**images (Required)** | A list of image URLs, dirs, and/or files.

## Service

**Service name:** `camera.multisource_reload_images`\
_This services will reload the images in use, useful if you change the content of one of the dirs._
