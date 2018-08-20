# camera.multisource

A camera platform that generate a camera feed from multiple sources.
  
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
**urls (Optional)** | A list of urls to web hosted images.
**dirs (Optional)** | A list of dirs with images, the path is relative to you HA config dir.
**files (Optional)** | A list of imagefiles, the path is relative to you HA config dir.