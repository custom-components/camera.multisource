# camera.multisource

A camera platform that generate a camera feed from multiple sources.

This platform will rotate the camera feeds, showing a 10 second feed from each camera before displaying the next one.
  
To get started put `/custom_components/camera/multisource.py` here:  
`<config directory>/custom_components/camera/multisource.py`  
  
**Example configuration.yaml:**

```yaml
camera:
  - platform: multisource
    urls:
      - https://example.com/image1.jpg
      - https://example.com/image2.png
    dirs:
      - /www/images/dir1
      - /www/images/dir2/
    files:
      - /www/image1.jpg
      - /www/image2.png
```

**Configuration variables:**  

key | description  
:--- | :---  
**platform (Required)** | The camera platform name.  
**name (Optional)** | Set the a custom name for the platform entity.
**interval (Optional)** | The interval in minutes to fetch new imgages, defaults to `5`.
**urls (Optional)** | A list of urls to web hosted images.
**dirs (Optional)** | A list of dirs with images, the path is relative to you HA config dir.
**files (Optional)** | A list of imagefiles, the path is relative to you HA config dir.

## Service

**Service name:** `camera.multisource_reload_images`\
_This services will reload the images in use, useful if you change the content of one of the dirs._