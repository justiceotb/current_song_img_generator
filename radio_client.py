"""Radio API client for fetching current song information"""

from abc_radio_wrapper import ABCRadio
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# Ensure tzdata is available (especially important on Windows)
# This MUST be imported before zoneinfo to ensure timezone data is available
try:
    import tzdata
    _has_tzdata = True
except ImportError:
    _has_tzdata = False

# Handle timezone imports for cross-platform compatibility
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python < 3.9 fallback
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        # If neither is available, we'll use a fallback
        ZoneInfo = None

logger = logging.getLogger(__name__)


class RadioClient:
    """Client for interacting with ABC Radio API"""

    def __init__(self, station: str = "doublej", preferred_artwork_height: int = 300, display_timezone: str = "Australia/Sydney"):
        """
        Initialize the radio client

        Args:
            station: The radio station identifier (e.g., "doublej")
            preferred_artwork_height: Preferred height for artwork images in pixels
            display_timezone: Timezone for displaying play times (IANA timezone name)
        """
        self.station = station
        self.preferred_artwork_height = preferred_artwork_height
        self.display_timezone = display_timezone
        self.client = ABCRadio()

    def _convert_timezone(self, dt: Any) -> Any:
        """
        Convert datetime to configured timezone

        Args:
            dt: Datetime object or string (assumed to be UTC)

        Returns:
            Datetime converted to display timezone, or original value if conversion fails
        """
        if ZoneInfo is None:
            logger.warning("ZoneInfo not available, returning datetime as-is")
            return dt

        try:
            # Create timezone objects once to avoid repeated lookups
            utc_tz = ZoneInfo('UTC')
            display_tz = ZoneInfo(self.display_timezone)

            # If it's already a datetime object
            if isinstance(dt, datetime):
                # If it doesn't have timezone info, assume UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=utc_tz)
                # Convert to display timezone
                return dt.astimezone(display_tz)

            # If it's a string, try to parse it
            if isinstance(dt, str):
                # Try ISO format first
                try:
                    # Parse the datetime string (handles 'Z' suffix for UTC)
                    parsed_dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                    # If no timezone info, assume UTC
                    if parsed_dt.tzinfo is None:
                        parsed_dt = parsed_dt.replace(tzinfo=utc_tz)
                    # Convert to display timezone
                    return parsed_dt.astimezone(display_tz)
                except Exception as parse_error:
                    # If parsing fails, return as-is
                    logger.debug(f"Could not parse datetime string: {parse_error}")
                    return dt

            # For other types, return as-is
            return dt

        except Exception as e:
            logger.warning(f"Error converting timezone: {e}")
            logger.debug(f"Input type: {type(dt)}, value: {dt}")
            logger.debug(f"Display timezone: {self.display_timezone}")
            logger.debug(f"tzdata available: {_has_tzdata}")
            return dt

    def get_current_song(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the current/most recent song from the radio station

        Returns:
            Dictionary containing song information with keys:
            - title: Song title
            - artist: Artist name
            - album: Album name
            - artwork_url: URL to artwork image
            - play_time: Time the song started playing (datetime or string)
            Returns None if no song data is available
        """
        try:
            # Use the search method with limit=1 to get the most recent song
            search_result = self.client.search(station=self.station, limit=1)

            if not search_result or not hasattr(search_result, 'radio_songs'):
                logger.warning(f"No results returned for station {self.station}")
                return None

            # Get the first (most recent) radio play
            radio_songs = list(search_result.radio_songs)
            if not radio_songs:
                logger.warning(f"No radio songs found for station {self.station}")
                return None

            radio_play = radio_songs[0]
            logger.debug(radio_play)

            # Extract song information
            song = radio_play.song if hasattr(radio_play, 'song') else None
            if not song:
                logger.warning("No song data in radio play")
                return None

            # Extract play time - try different possible attribute names
            play_time = None
            for time_attr in ['played_time', 'play_time', 'time', 'service_played_time']:
                if hasattr(radio_play, time_attr):
                    play_time_raw = getattr(radio_play, time_attr)
                    # Convert to target timezone if it's a datetime object
                    if play_time_raw:
                        play_time = self._convert_timezone(play_time_raw)
                    break

            # Extract title
            title = song.title if hasattr(song, 'title') else ''

            # Extract artist (first artist if multiple)
            artist_name = ''
            if hasattr(song, 'artists') and song.artists:
                artists_list = list(song.artists)
                if artists_list:
                    first_artist = artists_list[0]
                    if hasattr(first_artist, 'name'):
                        artist_name = first_artist.name

            # Extract album/release
            album_title = ''
            album = None
            if hasattr(song, 'album') and song.album:
                album = song.album
                if hasattr(album, 'title'):
                    album_title = album.title

            # Extract artwork URL - find the best sized artwork
            artwork_url = None
            if album and hasattr(album, 'artwork') and album.artwork:
                # Check if artwork is iterable (list) or a single object
                try:
                    # Try to convert to list (handles both iterable and single object)
                    artwork_list = list(album.artwork) if hasattr(album.artwork, '__iter__') and not isinstance(album.artwork, str) else [album.artwork]
                except TypeError:
                    # If it's a single Artwork object, wrap it in a list
                    artwork_list = [album.artwork]

                if artwork_list:
                    # Try to find artwork with specific height (closest to preferred)
                    best_artwork = None
                    best_diff = float('inf')

                    for artwork in artwork_list:
                        if hasattr(artwork, 'height') and hasattr(artwork, 'url'):
                            height = artwork.height
                            if isinstance(height, (int, float)):
                                diff = abs(height - self.preferred_artwork_height)
                                if diff < best_diff:
                                    best_diff = diff
                                    best_artwork = artwork
                                    logger.debug(f"Found artwork: {height}px (diff: {diff})")

                    # If we found a good match, use it
                    if best_artwork and hasattr(best_artwork, 'url'):
                        artwork_url = best_artwork.url
                        logger.debug(f"Selected artwork: {best_artwork.height}px - {artwork_url}")
                    # Otherwise, fall back to first artwork with URL
                    elif artwork_list and hasattr(artwork_list[0], 'url'):
                        artwork_url = artwork_list[0].url
                        logger.debug(f"Fallback to first artwork: {artwork_url}")

            song_info = {
                'title': title,
                'artist': artist_name,
                'album': album_title,
                'artwork_url': artwork_url,
                'play_time': play_time
            }

            logger.info(f"Fetched song: {song_info['title']} by {song_info['artist']} (played: {play_time})")
            return song_info

        except Exception as e:
            logger.error(f"Error fetching current song: {e}", exc_info=True)
            return None
