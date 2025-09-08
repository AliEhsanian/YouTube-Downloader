"""
Enhanced YouTube Downloader (Streamlit Optimized)
A clean, fast YouTube downloader optimized for GUI integration.
"""

import os
import sys
import argparse
import re
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Callable
import yt_dlp


class Quality(Enum):
    """Video quality options with format preferences."""
    BEST = "best[ext=mp4]/best"
    HD_4K = "best[height<=2160][ext=mp4]/bestvideo[height<=2160]+bestaudio[ext=m4a]/best[height<=2160]"
    HD_1080 = "best[height<=1080][ext=mp4]/bestvideo[height<=1080]+bestaudio[ext=m4a]/best[height<=1080]"
    HD_720 = "best[height<=720][ext=mp4]/bestvideo[height<=720]+bestaudio[ext=m4a]/best[height<=720]"
    AUDIO_ONLY = "bestaudio"


class VideoFormat(Enum):
    """Output video format options."""
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv"
    AVI = "avi"


class DefaultProgressHook:
    """Default console progress display for downloads."""

    def __init__(self):
        self.last_printed_percent = -1
        self.current_stage = "Downloading"

    def __call__(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                return

            # Only update every 2% to reduce terminal spam
            current_percent = int(percent)
            if current_percent != self.last_printed_percent and current_percent % 2 == 0:
                self.last_printed_percent = current_percent
                bar_length = 30
                filled_length = int(bar_length * percent / 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                print(f"\r{self.current_stage}: [{bar}] {percent:.1f}%", end='', flush=True)

        elif d['status'] == 'finished':
            print(f"\n✓ Downloaded: {Path(d['filename']).name}")

        elif d['status'] == 'error':
            print(f"\n❌ Error during download: {d.get('error', 'Unknown error')}")


class URLValidator:
    """Validate and extract video information from URLs with flexible handling."""

    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'(?:https?://)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/c/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/channel/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/@[\w-]+',
        r'(?:https?://)?(?:music\.)?youtube\.com/[\w/?=&-]+',
        r'(?:https?://)?(?:m\.)?youtube\.com/[\w/?=&-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
    ]

    @classmethod
    def validate_url(cls, url: str, interactive: bool = True) -> Tuple[bool, str]:
        """
        Validate URL with flexible handling.
        Returns (is_valid, processed_url)
        """
        url = url.strip()

        # First, check standard YouTube patterns
        if cls._matches_youtube_pattern(url):
            return True, url

        # If no pattern matches, test with yt-dlp directly
        if cls._test_url_with_ydlp(url):
            return True, url

        # If interactive mode, ask user for confirmation
        if interactive:
            print(f"❓ URL format not recognized: {url}")
            print("This might still be a valid YouTube link or supported video platform.")

            while True:
                choice = input("Try to download anyway? (y/n): ").strip().lower()
                if choice in ['y', 'yes']:
                    print("⚠️  Attempting download with unverified URL...")
                    return True, url
                elif choice in ['n', 'no']:
                    return False, url
                print("Please enter 'y' or 'n'")

        return False, url

    @classmethod
    def _matches_youtube_pattern(cls, url: str) -> bool:
        """Check if URL matches known YouTube patterns."""
        return any(re.match(pattern, url, re.IGNORECASE) for pattern in cls.YOUTUBE_PATTERNS)

    @classmethod
    def _test_url_with_ydlp(cls, url: str) -> bool:
        """Test URL with yt-dlp to see if it's supported."""
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Don't extract full info, just test
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info is not None
        except Exception:
            return False

    @classmethod
    def get_video_info(cls, url: str, extract_flat: bool = False) -> Optional[Dict[str, Any]]:
        """Extract video information without downloading. Optimized for speed."""
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': extract_flat,  # Fast extraction for GUI
                #'noplaylist': False if is_playlist else True,  # Force single-video extraction
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            if not extract_flat:  # Don't print errors for GUI usage
                print(f"❌ Failed to get video info: {e}")
            return None

    @classmethod
    def get_video_info_fast(cls, url: str) -> Optional[Dict[str, Any]]:
        """Fast video info extraction for GUI - gets basic info only."""
        return cls.get_video_info(url, extract_flat=False)


class YouTubeDownloader:
    """Main downloader class optimized for GUI integration."""

    def __init__(self, output_dir: str = '.', custom_filename: Optional[str] = None,
                 preferred_format: Optional[VideoFormat] = None,
                 progress_callback: Optional[Callable] = None):
        self.output_dir = Path(output_dir)
        self.custom_filename = custom_filename
        self.preferred_format = preferred_format or VideoFormat.MP4
        self.progress_hook = progress_callback or DefaultProgressHook()

    def _get_ydl_opts(self, quality: Quality, is_playlist: bool = False,
                      video_info: Optional[Dict] = None, force_convert: bool = False) -> dict:
        """Build yt-dlp options with format preferences and conversion."""
        opts = {
            'outtmpl': self._get_output_template(is_playlist, video_info),
            'progress_hooks': [self.progress_hook],
            'no_warnings': True,
            'ignoreerrors': False,
            'extract_flat': False,  # We need full info for progress
            'merge_output_format': 'mp4',
        }

        # Handle audio-only downloads
        if quality == Quality.AUDIO_ONLY:
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
            return opts

        # Video format selection
        format_string = self._build_format_string(quality, force_convert)
        opts['format'] = format_string

        # Add post-processors for format conversion if needed
        postprocessors = []

        if force_convert and self.preferred_format:
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': self.preferred_format.value,
            })

        # Add metadata processor (optional for speed)
        postprocessors.append({
            'key': 'FFmpegMetadata',
        })

        if postprocessors:
            opts['postprocessors'] = postprocessors

        return opts

    def _build_format_string(self, quality: Quality, force_convert: bool = False) -> str:
        """Build format selection string prioritizing compatibility."""
        if force_convert:
            # If forcing conversion, we can accept any format since we'll convert
            base_formats = {
                Quality.BEST: "best",
                Quality.HD_4K: "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
                Quality.HD_1080: "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                Quality.HD_720: "bestvideo[height<=720]+bestaudio/best[height<=720]",
            }
            return base_formats.get(quality, "best")

        # Default: prefer MP4, fallback to other formats for speed
        format_preferences = {
            Quality.BEST: (
                "best[ext=mp4]/"
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
                "best"
            ),
            Quality.HD_4K: (
                "best[height<=2160][ext=mp4]/"
                "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/"
                "best[height<=2160]"
            ),
            Quality.HD_1080: (
                "best[height<=1080][ext=mp4]/"
                "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
                "best[height<=1080]"
            ),
            Quality.HD_720: (
                "best[height<=720][ext=mp4]/"
                "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
                "best[height<=720]"
            )
        }

        return format_preferences.get(quality, "best[ext=mp4]/best")

    def _get_output_template(self, is_playlist: bool = False, video_info: Optional[Dict] = None) -> str:
        """Generate output filename template."""
        base_dir = str(self.output_dir)

        if self.custom_filename and not is_playlist:
            # Custom filename for single video
            name_without_ext = Path(self.custom_filename).stem
            return f"{base_dir}/{name_without_ext}.%(ext)s"

        if is_playlist:
            # Organized playlist structure
            return f"{base_dir}/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s"

        # Default: use video title
        return f"{base_dir}/%(title)s.%(ext)s"

    def download(self, url: str, quality: Quality, is_playlist: bool = False,
                 video_info: Optional[Dict] = None, force_convert: bool = False,
                 silent: bool = False) -> bool:
        """Download video(s) with specified quality and format conversion."""
        try:
            opts = self._get_ydl_opts(quality, is_playlist, video_info, force_convert)

            if not silent:
                print(f"\nStarting download{'s' if is_playlist else ''}...")

                if force_convert and self.preferred_format:
                    print(f"🔄 Will convert to {self.preferred_format.value.upper()} format")
                elif self.preferred_format == VideoFormat.MP4:
                    print("📹 Preferring MP4 format for better compatibility")

                if video_info and not is_playlist:
                    title = video_info.get('title', 'Unknown')
                    duration = video_info.get('duration', 0)
                    uploader = video_info.get('uploader', 'Unknown')

                    print(f"Title: {title}")
                    print(f"Uploader: {uploader}")
                    if duration:
                        mins, secs = divmod(duration, 60)
                        print(f"Duration: {mins:02d}:{secs:02d}")

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                return True

        except Exception as e:
            if not silent:
                print(f"❌ Download failed: {e}")
                print("💡 Tips:")
                print("   - Try a different quality setting")
                print("   - Use --force-convert to ensure specific output format")
                print("   - Check if the video is available in your region")
            return False

    def set_progress_hook(self, hook: Callable):
        """Set custom progress hook for GUI integration."""
        self.progress_hook = hook


class UserInterface:
    """Handle user input and interaction (for CLI mode)."""

    QUALITY_CHOICES = {
        '1': Quality.BEST,
        '2': Quality.HD_4K,
        '3': Quality.HD_1080,
        '4': Quality.HD_720,
        '5': Quality.AUDIO_ONLY
    }

    FORMAT_CHOICES = {
        '1': VideoFormat.MP4,
        '2': VideoFormat.WEBM,
        '3': VideoFormat.MKV,
        '4': VideoFormat.AVI
    }

    def get_url(self) -> str:
        """Get and validate URL from user with flexible handling."""
        while True:
            url = input("\nEnter video URL (YouTube or other supported platforms): ").strip()
            if not url:
                print("URL cannot be empty. Please try again.")
                continue

            # Validate URL with flexible handling
            is_valid, processed_url = URLValidator.validate_url(url, interactive=True)

            if not is_valid:
                print("❌ Skipping this URL. Please try another one.")
                continue

            # Try to get video info for confirmation
            print("🔍 Getting video information...")
            info = URLValidator.get_video_info(processed_url)

            if info:
                title = info.get('title', 'Unknown title')
                uploader = info.get('uploader', 'Unknown uploader')
                print(f"✅ Found: {title}")
                print(f"   By: {uploader}")

                # Confirm with user
                while True:
                    choice = input("Proceed with this video? (y/n): ").strip().lower()
                    if choice in ['y', 'yes', '']:
                        return processed_url
                    elif choice in ['n', 'no']:
                        break
                    print("Please enter 'y' or 'n'")
            else:
                print("⚠️  Could not retrieve video information, but URL might still work.")
                while True:
                    choice = input("Try to download anyway? (y/n): ").strip().lower()
                    if choice in ['y', 'yes']:
                        return processed_url
                    elif choice in ['n', 'no']:
                        break
                    print("Please enter 'y' or 'n'")

    def get_quality_choice(self) -> Quality:
        """Present quality options and get user choice."""
        print("\nSelect download quality:")
        print("1. Best available quality (MP4 preferred)")
        print("2. 4K (2160p)")
        print("3. 1080p")
        print("4. 720p")
        print("5. Audio only (MP3)")

        while True:
            choice = input("\nEnter choice (1-5) [default: 1]: ").strip()
            if not choice:  # Default to best quality
                return Quality.BEST
            if choice in self.QUALITY_CHOICES:
                return self.QUALITY_CHOICES[choice]
            print("Invalid choice. Please enter 1-5.")

    def get_format_preference(self) -> Tuple[VideoFormat, bool]:
        """Get preferred output format and conversion preference."""
        print("\nVideo format preference:")
        print("1. MP4 (recommended - best compatibility)")
        print("2. WebM (smaller file size)")
        print("3. MKV (high quality)")
        print("4. AVI (legacy compatibility)")

        while True:
            choice = input("\nEnter choice (1-4) [default: 1]: ").strip()
            if not choice:
                format_choice = VideoFormat.MP4
                break
            if choice in self.FORMAT_CHOICES:
                format_choice = self.FORMAT_CHOICES[choice]
                break
            print("Invalid choice. Please enter 1-4.")

        # Ask about force conversion
        if format_choice == VideoFormat.MP4:
            print("\n🔄 Format conversion options:")
            print("YouTube often provides high-quality videos in WebM format.")
            while True:
                choice = input("Force conversion to MP4 even if it means re-encoding? (y/n) [default: n]: ").strip().lower()
                if not choice or choice in ['n', 'no']:
                    force_convert = False
                    break
                elif choice in ['y', 'yes']:
                    force_convert = True
                    print("⚠️  Note: This may take longer and slightly reduce quality")
                    break
                print("Please enter 'y' or 'n'")
        else:
            force_convert = True  # Always convert for non-MP4 formats

        return format_choice, force_convert

    def get_output_settings(self, video_info: Optional[Dict] = None) -> Tuple[str, Optional[str]]:
        """Get output directory and optional custom filename."""
        current_dir = os.getcwd()

        output_dir = input(f"\nOutput directory [current: {os.path.basename(current_dir)}]: ").strip()
        if not output_dir:
            output_dir = current_dir

        # Suggest filename based on video title if available
        suggested_filename = ""
        if video_info and video_info.get('title'):
            # Clean up title for filename
            title = video_info['title']
            # Remove invalid filename characters
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
            clean_title = clean_title.strip()[:50]  # Limit length
            suggested_filename = f" [suggested: {clean_title}]"

        custom_filename = input(f"Custom filename (optional){suggested_filename}: ").strip()
        return output_dir, custom_filename if custom_filename else None

    def is_playlist_download(self, url: str, video_info: Optional[Dict] = None) -> bool:
        """Check if URL is playlist and ask user preference."""
        # Auto-detect playlist URLs
        if 'playlist' in url.lower() or 'list=' in url:
            print("🎵 Playlist detected!")
            choice = input("Download entire playlist? (y/n) [default: n]: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            return False

        # Check if video_info indicates a playlist
        if video_info and video_info.get('_type') == 'playlist':
            print("🎵 This URL contains a playlist!")
            choice = input("Download entire playlist? (y/n) [default: n]: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            return False

        # For non-playlist URLs, ask if they want to check for playlist
        choice = input("\nDownload as playlist? (y/n) [default: n]: ").strip().lower()
        if choice in ['y', 'yes']:
            return True
        return False


def main():
    """Main application entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Enhanced YouTube Downloader with format conversion support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                          # Interactive mode
  %(prog)s "https://youtube.com/watch?v=dQw4w9WgXcQ" --quality 720p
  %(prog)s "youtu.be/dQw4w9WgXcQ" --format mp4 --force-convert
  %(prog)s "suspicious-url" --force                 # Try anyway
        """
    )

    parser.add_argument("url", nargs='?', help="Video URL (YouTube or other supported platforms)")
    parser.add_argument("--output", "-o", help="Output directory", default=".")
    parser.add_argument("--filename", "-f", help="Custom filename (for single videos)")
    parser.add_argument("--quality", "-q", choices=['best', '4k', '1080p', '720p', 'audio'],
                       help="Video quality", default='best')
    parser.add_argument("--format", choices=['mp4', 'webm', 'mkv', 'avi'],
                       help="Preferred output format", default='mp4')
    parser.add_argument("--force-convert", action="store_true",
                       help="Force conversion to specified format (may re-encode)")
    parser.add_argument("--playlist", "-p", action="store_true", help="Download entire playlist")
    parser.add_argument("--no-interactive", action="store_true", help="Skip interactive prompts")
    parser.add_argument("--force", action="store_true", help="Skip URL validation")
    parser.add_argument("--silent", action="store_true", help="Minimal output")

    args = parser.parse_args()

    if not args.silent:
        print("🎬 Enhanced YouTube Downloader with Format Conversion")
        print("=" * 55)
        print("Supports YouTube and other video platforms")
        print("Automatically prefers MP4 for better compatibility")

    # Initialize components
    ui = UserInterface()

    # Get format preferences
    format_map = {
        'mp4': VideoFormat.MP4,
        'webm': VideoFormat.WEBM,
        'mkv': VideoFormat.MKV,
        'avi': VideoFormat.AVI
    }
    preferred_format = format_map[args.format]

    # Get URL (from args or user input)
    if args.url:
        url = args.url

        if args.force:
            if not args.silent:
                print("⚠️  Forcing download without URL validation...")
            is_valid, processed_url = True, url
        else:
            is_valid, processed_url = URLValidator.validate_url(url, interactive=not args.no_interactive)

        if not is_valid:
            print("❌ Invalid or unsupported URL.")
            sys.exit(1)

        if not args.silent:
            print(f"🔍 Getting video information...")
        video_info = URLValidator.get_video_info(processed_url)

        if video_info and not args.silent:
            title = video_info.get('title', 'Unknown title')
            uploader = video_info.get('uploader', 'Unknown uploader')
            print(f"✅ Found: {title}")
            print(f"   By: {uploader}")
        elif not video_info and not args.silent:
            print("⚠️  Could not retrieve video information")
            if not args.force and not args.no_interactive:
                choice = input("Continue anyway? (y/n): ").strip().lower()
                if choice not in ['y', 'yes']:
                    sys.exit(1)

        url = processed_url
    else:
        url = ui.get_url()
        video_info = URLValidator.get_video_info(url)

    # Get user preferences
    quality_map = {
        'best': Quality.BEST,
        '4k': Quality.HD_4K,
        '1080p': Quality.HD_1080,
        '720p': Quality.HD_720,
        'audio': Quality.AUDIO_ONLY
    }

    if args.no_interactive:
        # Non-interactive mode
        quality = quality_map[args.quality]
        is_playlist = args.playlist
        output_dir = args.output
        custom_filename = args.filename
        force_convert = args.force_convert

        if not args.silent:
            print(f"Using quality: {args.quality}")
            print(f"Output format: {args.format.upper()}")
            if force_convert:
                print("Force conversion: enabled")
            if is_playlist:
                print("Downloading as playlist")
    else:
        # Interactive mode
        if args.quality != 'best':
            quality = quality_map[args.quality]
            print(f"Using quality: {args.quality}")
        else:
            quality = ui.get_quality_choice()

        if quality != Quality.AUDIO_ONLY:
            preferred_format, force_convert = ui.get_format_preference()
        else:
            force_convert = False

        is_playlist = args.playlist or ui.is_playlist_download(url, video_info)

        if not args.filename and not is_playlist:
            output_dir, custom_filename = ui.get_output_settings(video_info)
        else:
            output_dir = args.output
            custom_filename = args.filename

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Download with format conversion
    downloader = YouTubeDownloader(output_dir, custom_filename, preferred_format)
    success = downloader.download(url, quality, is_playlist, video_info, force_convert, args.silent)

    if success and not args.silent:
        print(f"\n✅ Download completed successfully!")
        print(f"📁 Files saved to: {os.path.abspath(output_dir)}")
        if preferred_format == VideoFormat.MP4:
            print("🎯 Videos optimized for maximum player compatibility")
    elif not success:
        sys.exit(1)


if __name__ == "__main__":
    main()