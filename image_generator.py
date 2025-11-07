"""Image generator for creating song display images"""

from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generates images displaying current song information"""

    def __init__(
        self,
        width: int = 250,
        height: int = 122,
        color_mode: str = "monochrome",
        artwork_size: int = 122,
        text_margin: int = 10,
        line_spacing: int = 5,
        font_path: Optional[str] = None,
        font_size_title: int = 16,
        font_size_artist: int = 14,
        font_size_album: int = 12,
    ):
        """
        Initialize the image generator

        Args:
            width: Image width in pixels
            height: Image height in pixels
            color_mode: Color mode - "monochrome", "grayscale", or "7color"
            artwork_size: Size of the square artwork area
            text_margin: Pixels between artwork and text
            line_spacing: Pixels between text lines
            font_path: Path to TTF font file (None for default)
            font_size_title: Font size for song title
            font_size_artist: Font size for artist name
            font_size_album: Font size for album name
        """
        self.width = width
        self.height = height
        self.color_mode = color_mode
        self.artwork_size = artwork_size
        self.text_margin = text_margin
        self.line_spacing = line_spacing

        # Load fonts
        try:
            if font_path:
                self.font_title = ImageFont.truetype(font_path, font_size_title)
                self.font_artist = ImageFont.truetype(font_path, font_size_artist)
                self.font_album = ImageFont.truetype(font_path, font_size_album)
            else:
                # Use default font
                self.font_title = ImageFont.load_default()
                self.font_artist = ImageFont.load_default()
                self.font_album = ImageFont.load_default()
        except Exception as e:
            logger.warning(f"Error loading fonts: {e}. Using default font.")
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_album = ImageFont.load_default()

    def _fetch_artwork(self, url: Optional[str]) -> Optional[Image.Image]:
        """
        Fetch artwork from URL

        Args:
            url: URL to artwork image

        Returns:
            PIL Image object or None if fetch fails
        """
        if not url:
            logger.warning("No artwork URL provided")
            return None

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            return img
        except Exception as e:
            logger.error(f"Error fetching artwork: {e}")
            return None

    def _create_placeholder_artwork(self) -> Image.Image:
        """
        Create a placeholder image when artwork is not available

        Returns:
            PIL Image object with placeholder
        """
        img = Image.new('RGB', (self.artwork_size, self.artwork_size), color='gray')
        draw = ImageDraw.Draw(img)

        # Draw a simple music note symbol
        draw.text(
            (self.artwork_size // 2, self.artwork_size // 2),
            "♪",
            fill='white',
            anchor='mm',
            font=self.font_title
        )

        return img

    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> list:
        """
        Wrap text to fit within max_width

        Args:
            text: Text to wrap
            font: Font to use for measurement
            max_width: Maximum width in pixels

        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]

    def _apply_color_mode(self, img: Image.Image) -> Image.Image:
        """
        Apply color mode conversion to the image

        Args:
            img: Input PIL Image

        Returns:
            Converted PIL Image
        """
        if self.color_mode == "monochrome":
            # Convert to grayscale first, then to 1-bit (black and white)
            img = img.convert('L')
            img = img.convert('1', dither=Image.FLOYDSTEINBERG)
        elif self.color_mode == "grayscale":
            # Convert to 4-level grayscale (2-bit)
            img = img.convert('L')
            # Reduce to 4 levels
            img = img.point(lambda x: (x // 64) * 85)  # Maps to 0, 85, 170, 255
            img = img.convert('L', dither=Image.FLOYDSTEINBERG)
        elif self.color_mode == "7color":
            # Convert to palette mode with 7 colors + white (8 colors total)
            # This uses adaptive palette and dithering
            img = img.convert('P', palette=Image.ADAPTIVE, colors=7, dither=Image.FLOYDSTEINBERG)

        return img

    def _format_play_time(self, play_time: Any) -> str:
        """
        Format the play time for display

        Args:
            play_time: Play time (could be datetime, string, or None)

        Returns:
            Formatted time string
        """
        if not play_time:
            return ''

        try:
            # If it's already a datetime object
            if isinstance(play_time, datetime):
                return play_time.strftime('%I:%M %p')

            # If it's a string, try to parse it
            if isinstance(play_time, str):
                # Try ISO format first
                try:
                    dt = datetime.fromisoformat(play_time.replace('Z', '+00:00'))
                    return dt.strftime('%I:%M %p')
                except:
                    # If parsing fails, return as-is
                    return play_time

            # For other types, convert to string
            return str(play_time)

        except Exception as e:
            logger.warning(f"Error formatting play time: {e}")
            return str(play_time) if play_time else ''

    def generate_image(self, song_info: Dict[str, Any], output_path: str) -> bool:
        """
        Generate and save the song display image

        Args:
            song_info: Dictionary with keys: title, artist, album, artwork_url, play_time
            output_path: Path where the image should be saved

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create base image (white background)
            img = Image.new('RGB', (self.width, self.height), color='white')

            # Fetch and process artwork
            artwork = self._fetch_artwork(song_info.get('artwork_url'))
            if artwork is None:
                artwork = self._create_placeholder_artwork()

            # Resize artwork to fit
            artwork = artwork.resize((self.artwork_size, self.artwork_size), Image.LANCZOS)

            # Paste artwork on the left side
            img.paste(artwork, (0, 0))

            # Draw text on the right side
            draw = ImageDraw.Draw(img)

            # Calculate text area
            text_x = self.artwork_size + self.text_margin
            text_width = self.width - text_x - self.text_margin
            current_y = self.text_margin

            # Draw play time with "DoubleJ" prefix at the top (if available)
            play_time_str = self._format_play_time(song_info.get('play_time'))
            if play_time_str:
                # Add "DoubleJ" prefix
                time_text = f"DoubleJ   {play_time_str}"

                # # Get text dimensions
                bbox = self.font_album.getbbox(time_text)
                text_height = bbox[3] - bbox[1]
                text_width_actual = bbox[2] - bbox[0]

                # # Add padding around the text
                padding = 3

                # # Draw black background rectangle
                # bg_x1 = text_x - padding
                # bg_y1 = current_y - padding
                # bg_x2 = text_x + text_width_actual + padding
                # bg_y2 = current_y + text_height + padding
                # draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill='black')
                draw.rectangle([self.artwork_size, 0, self.width, 18], fill='black')
                # current_y

                # Draw white text on black background
                draw.text((text_x, 2), time_text, fill='white', font=self.font_album)

                # Update y position
                current_y += text_height + padding * 2 + self.line_spacing

            # Draw title
            title_lines = self._wrap_text(
                song_info.get('title', 'Unknown'),
                self.font_title,
                text_width
            )
            for line in title_lines:
                draw.text((text_x, current_y), line, fill='black', font=self.font_title)
                bbox = self.font_title.getbbox(line)
                current_y += (bbox[3] - bbox[1]) + self.line_spacing

            current_y += self.line_spacing  # Extra space after title

            # Draw artist
            artist_lines = self._wrap_text(
                song_info.get('artist', 'Unknown'),
                self.font_artist,
                text_width
            )
            for line in artist_lines:
                draw.text((text_x, current_y), line, fill='black', font=self.font_artist)
                bbox = self.font_artist.getbbox(line)
                current_y += (bbox[3] - bbox[1]) + self.line_spacing

            current_y += self.line_spacing  # Extra space after artist

            # Draw album
            album_lines = self._wrap_text(
                song_info.get('album', 'Unknown'),
                self.font_album,
                text_width
            )
            for line in album_lines:
                # Check if we're running out of space
                if current_y + 20 > self.height:
                    break
                draw.text((text_x, current_y), line, fill='black', font=self.font_album)
                bbox = self.font_album.getbbox(line)
                current_y += (bbox[3] - bbox[1]) + self.line_spacing

            # Apply color mode conversion
            img = self._apply_color_mode(img)

            # Save the image
            img.save(output_path)
            logger.info(f"Image saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
            return False
