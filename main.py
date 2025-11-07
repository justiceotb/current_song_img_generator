"""Main application for Current Song Image Generator"""

import os
import time
import logging
import signal
import sys
from pathlib import Path

import config
from radio_client import RadioClient
from image_generator import ImageGenerator
from song_tracker import SongTracker
from web_server import WebServer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('song_generator.log')
    ]
)

logger = logging.getLogger(__name__)


class CurrentSongApp:
    """Main application for fetching and displaying current song information"""

    def __init__(self):
        """Initialize the application"""
        # Create output directory
        self.output_dir = Path(config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize components
        self.radio_client = RadioClient(
            station=config.STATION,
            preferred_artwork_height=config.PREFERRED_ARTWORK_HEIGHT,
            display_timezone=config.DISPLAY_TIMEZONE
        )
        self.image_generator = ImageGenerator(
            width=config.IMAGE_WIDTH,
            height=config.IMAGE_HEIGHT,
            color_mode=config.COLOR_MODE,
            artwork_size=config.ARTWORK_SIZE,
            text_margin=config.TEXT_MARGIN,
            line_spacing=config.LINE_SPACING,
            font_path=config.FONT_PATH,
            font_size_title=config.FONT_SIZE_TITLE,
            font_size_artist=config.FONT_SIZE_ARTIST,
            font_size_album=config.FONT_SIZE_ALBUM,
        )
        self.song_tracker = SongTracker()
        self.web_server = WebServer(
            host=config.SERVER_HOST,
            port=config.SERVER_PORT,
            directory=str(self.output_dir)
        )

        # File paths
        self.image_path = self.output_dir / config.IMAGE_FILENAME
        self.hash_path = self.output_dir / config.HASH_FILENAME

        # Running flag
        self.running = False

    def update_song(self) -> bool:
        """
        Fetch current song and update image if changed

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Fetch current song
            song_info = self.radio_client.get_current_song()

            if not song_info:
                logger.warning("No song information available")
                return False

            # Check if song has changed
            if not self.song_tracker.has_song_changed(song_info, str(self.hash_path)):
                logger.debug("Song hasn't changed, skipping update")
                return True

            logger.info(f"New song detected: {song_info['title']} by {song_info['artist']}")

            # Generate new image
            if not self.image_generator.generate_image(song_info, str(self.image_path)):
                logger.error("Failed to generate image")
                return False

            # Update hash file
            song_hash = self.song_tracker.generate_song_hash(song_info)
            if not self.song_tracker.save_hash(song_hash, str(self.hash_path)):
                logger.error("Failed to save hash")
                return False

            logger.info("Song information updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating song: {e}", exc_info=True)
            return False

    def run(self):
        """Run the main application loop"""
        logger.info("Starting Current Song Image Generator")
        logger.info(f"Station: {config.STATION}")
        logger.info(f"Poll interval: {config.POLL_INTERVAL} seconds")
        logger.info(f"Image size: {config.IMAGE_WIDTH}x{config.IMAGE_HEIGHT}")
        logger.info(f"Color mode: {config.COLOR_MODE}")
        logger.info(f"Output directory: {self.output_dir.absolute()}")

        # Start web server
        self.web_server.start()
        time.sleep(1)  # Give server time to start

        if not self.web_server.is_running():
            logger.error("Failed to start web server")
            return

        logger.info(f"Image available at: http://{config.SERVER_HOST}:{config.SERVER_PORT}/{config.IMAGE_FILENAME}")
        logger.info(f"Hash available at: http://{config.SERVER_HOST}:{config.SERVER_PORT}/{config.HASH_FILENAME}")

        # Initial update
        logger.info("Performing initial song update...")
        self.update_song()

        # Main loop
        self.running = True
        try:
            while self.running:
                time.sleep(config.POLL_INTERVAL)
                if self.running:  # Check again in case we stopped during sleep
                    self.update_song()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.shutdown()

    def shutdown(self):
        """Shutdown the application"""
        logger.info("Shutting down...")
        self.running = False
        self.web_server.stop()
        logger.info("Shutdown complete")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run application
    app = CurrentSongApp()
    app.run()


if __name__ == "__main__":
    main()
