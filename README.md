# Current Song Image Generator

A Python application that periodically fetches the current song playing on ABC Radio Double J, generates an e-paper friendly image, and hosts it via HTTP for display on microcontroller-based e-paper displays.

## Features

- Fetches current song information from ABC Radio Double J using the official API
- Generates 250x122 pixel images optimized for e-paper displays
- Displays album artwork alongside song title, artist, and album name
- Supports multiple color modes:
  - Monochrome (1-bit black and white)
  - 4-level grayscale
  - 7-color with dithering
- Hosts images via a built-in HTTP server
- Generates unique hash for each song to allow clients to detect updates
- Configurable update intervals and display settings

## Requirements

- Python 3.7 or higher
- Internet connection for API access

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd current_song_img_generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit [config.py](config.py) to customize the application settings:

### Image Settings
- `IMAGE_WIDTH`: Image width in pixels (default: 250)
- `IMAGE_HEIGHT`: Image height in pixels (default: 122)
- `COLOR_MODE`: Color mode - "monochrome", "grayscale", or "7color" (default: "monochrome")

### Radio Settings
- `STATION`: Radio station identifier (default: "doublej")
- `POLL_INTERVAL`: Seconds between API checks (default: 30)

### Server Settings
- `SERVER_HOST`: Host address for HTTP server (default: "0.0.0.0")
- `SERVER_PORT`: Port for HTTP server (default: 8080)
- `OUTPUT_DIR`: Directory for generated files (default: "output")

### Layout Settings
- `ARTWORK_SIZE`: Size of square artwork area (default: 122)
- `TEXT_MARGIN`: Pixels between artwork and text (default: 10)
- `LINE_SPACING`: Pixels between text lines (default: 5)

### Font Settings
- `FONT_PATH`: Path to TTF font file (None uses default)
- `FONT_SIZE_TITLE`: Font size for song title (default: 16)
- `FONT_SIZE_ARTIST`: Font size for artist name (default: 14)
- `FONT_SIZE_ALBUM`: Font size for album name (default: 12)

## Usage

Run the application:

```bash
python main.py
```

The application will:
1. Start an HTTP server on the configured port
2. Fetch the current song information
3. Generate an image and save it to the output directory
4. Check for updates at the configured interval
5. Update the image when a new song is detected

### Accessing the Generated Files

Once running, you can access:
- **Image**: `http://<server-ip>:8080/current_song.png`
- **Hash**: `http://<server-ip>:8080/current_song_hash.txt`

Replace `<server-ip>` with your server's IP address (use `localhost` if accessing locally).

### Microcontroller Integration

Your microcontroller can:
1. Periodically fetch `current_song_hash.txt`
2. Compare with previously stored hash
3. If different, fetch `current_song.png` and update the display

Example ESP32/ESP8266 logic:
```cpp
String currentHash = httpGET("http://server:8080/current_song_hash.txt");
if (currentHash != storedHash) {
    downloadImage("http://server:8080/current_song.png");
    updateDisplay();
    storedHash = currentHash;
}
```

## Changing Color Modes

To switch between color modes, edit [config.py](config.py):

### Monochrome (1-bit, best for most e-paper displays)
```python
COLOR_MODE = "monochrome"
```

### 4-level Grayscale
```python
COLOR_MODE = "grayscale"
```

### 7-color with Dithering
```python
COLOR_MODE = "7color"
```

## Project Structure

- [main.py](main.py) - Main application entry point
- [config.py](config.py) - Configuration settings
- [radio_client.py](radio_client.py) - ABC Radio API client
- [image_generator.py](image_generator.py) - Image generation logic
- [song_tracker.py](song_tracker.py) - Song tracking and hash generation
- [web_server.py](web_server.py) - HTTP server for hosting files
- [requirements.txt](requirements.txt) - Python dependencies
- `output/` - Generated images and hash file (created on first run)
- `song_generator.log` - Application log file

## Logging

Logs are written to both console and `song_generator.log` file. You can monitor the log in real-time:

```bash
tail -f song_generator.log
```

## Troubleshooting

### No artwork displayed
If artwork fails to download, a placeholder will be used. Check internet connectivity and API availability.

### Image not updating
- Check the log file for errors
- Verify the API is returning data: check if `abc-radio-wrapper` is working
- Ensure sufficient disk space in the output directory

### Server not accessible
- Check firewall settings allow connections on the configured port
- Verify `SERVER_HOST` is set correctly (use "0.0.0.0" to listen on all interfaces)
- Ensure the port is not already in use by another application

## License

See [LICENSE](LICENSE) file for details.

## API Credits

This application uses the [abc-radio-wrapper](https://pypi.org/project/abc-radio-wrapper/) library to access ABC Radio's public API.
