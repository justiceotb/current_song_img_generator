"""Song tracker for generating unique identifiers for songs"""

import hashlib
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SongTracker:
    """Tracks songs and generates unique identifiers"""

    @staticmethod
    def generate_song_hash(song_info: Dict[str, Any]) -> str:
        """
        Generate a unique hash for a song based on title, artist, and album

        Args:
            song_info: Dictionary containing song information

        Returns:
            Hexadecimal hash string (SHA256)
        """
        # Extract song components
        title = song_info.get('title', '').strip().lower()
        artist = song_info.get('artist', '').strip().lower()
        album = song_info.get('album', '').strip().lower()

        # Create a consistent string representation
        song_string = f"{title}|{artist}|{album}"

        # Generate SHA256 hash
        hash_obj = hashlib.sha256(song_string.encode('utf-8'))
        song_hash = hash_obj.hexdigest()

        logger.debug(f"Generated hash {song_hash[:8]}... for: {song_string}")
        return song_hash

    @staticmethod
    def save_hash(hash_value: str, output_path: str) -> bool:
        """
        Save the hash to a text file

        Args:
            hash_value: The hash string to save
            output_path: Path to the output file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(hash_value)
            logger.info(f"Hash saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving hash: {e}", exc_info=True)
            return False

    @staticmethod
    def read_hash(input_path: str) -> str:
        """
        Read the hash from a text file

        Args:
            input_path: Path to the input file

        Returns:
            The hash string, or empty string if file doesn't exist or error occurs
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.debug(f"Hash file not found: {input_path}")
            return ""
        except Exception as e:
            logger.error(f"Error reading hash: {e}", exc_info=True)
            return ""

    @staticmethod
    def has_song_changed(song_info: Dict[str, Any], hash_file_path: str) -> bool:
        """
        Check if the song has changed compared to the stored hash

        Args:
            song_info: Current song information
            hash_file_path: Path to the hash file

        Returns:
            True if song has changed (or no previous hash exists), False otherwise
        """
        current_hash = SongTracker.generate_song_hash(song_info)
        stored_hash = SongTracker.read_hash(hash_file_path)

        if not stored_hash:
            logger.info("No previous hash found, treating as changed")
            return True

        changed = current_hash != stored_hash
        if changed:
            logger.info(f"Song changed: {stored_hash[:8]}... -> {current_hash[:8]}...")
        else:
            logger.debug("Song unchanged")

        return changed
