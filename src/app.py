"""
Streamlit GUI for YouTube Downloader
A web-based interface for downloading YouTube videos with quality and format options.
"""


import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
import streamlit as st
from downloader import YouTubeDownloader, URLValidator, Quality, VideoFormat # Import from downloader.py


# Page config
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 1rem;
    background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
    color: white;
    border-radius: 10px;
    margin-bottom: 2rem;
}
.download-section {
    background-color: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
}
.info-box {
    background-color: #e3f2fd;
    padding: 1rem;
    border-left: 4px solid #2196f3;
    border-radius: 5px;
    margin: 1rem 0;
}
.success-box {
    background-color: #e8f5e8;
    padding: 1rem;
    border-left: 4px solid #4caf50;
    border-radius: 5px;
    margin: 1rem 0;
}
.error-box {
    background-color: #ffebee;
    padding: 1rem;
    border-left: 4px solid #f44336;
    border-radius: 5px;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'video_info' not in st.session_state:
        st.session_state.video_info = None
    if 'download_status' not in st.session_state:
        st.session_state.download_status = None
    if 'is_downloading' not in st.session_state:
        st.session_state.is_downloading = False
    if 'progress' not in st.session_state:
        st.session_state.progress = 0
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = ""


def clean_filename(filename: str) -> str:
    """Clean filename for safe file system usage."""
    # Remove invalid filename characters
    clean_name = re.sub(r'[<>:"/\\|?*]', '', filename)
    clean_name = clean_name.strip()[:100]  # Limit length
    return clean_name


def format_duration(seconds: int) -> str:
    """Format duration in seconds to MM:SS format."""
    if not seconds:
        return "Unknown"
    mins, secs = divmod(seconds, 60)
    return f"{mins:02d}:{secs:02d}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format."""
    if not size_bytes:
        return "Unknown"

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_upload_date(date_str: str) -> str:
    """Format upload date to YYYY-MM-DD format."""
    if not date_str or date_str == "Unknown":
        return "Unknown"

    try:
        # If date_str is in YYYYMMDD format (common from yt-dlp)
        if len(date_str) == 8 and date_str.isdigit():
            year = date_str[:4]
            month = date_str[4:6]
            day = date_str[6:8]
            return f"{year}-{month}-{day}"
        else:
            # Try to parse other formats and convert to YYYY-MM-DD
            # This handles various date formats that might be returned
            return date_str
    except:
        return date_str


class StreamlitProgressHook:
    """Progress hook for Streamlit interface."""

    def __init__(self, progress_bar, status_text):
        self.progress_bar = progress_bar
        self.status_text = status_text
        self.last_percent = 0

    def __call__(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                total_mb = d['total_bytes'] / (1024 * 1024)
            elif 'total_bytes_estimate' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                total_mb = d['total_bytes_estimate'] / (1024 * 1024)
            else:
                return

            # Update progress bar and status
            self.progress_bar.progress(int(percent))
            self.status_text.text(f"Downloading... {percent:.1f}% ({downloaded_mb:.1f}MB / {total_mb:.1f}MB)")

        elif d['status'] == 'finished':
            filename = Path(d['filename']).name
            self.progress_bar.progress(100)
            self.status_text.text(f"✅ Download completed: {filename}")

        elif d['status'] == 'error':
            self.status_text.text(f"❌ Error: {d.get('error', 'Unknown error')}")


def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """Get video information with caching."""
    if not url:
        return None

    # Use session state for caching
    cache_key = f"video_info_{hash(url)}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    with st.spinner("🔍 Getting video information..."):
        info = URLValidator.get_video_info(url)
        if info:
            st.session_state[cache_key] = info
        return info


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎬 YouTube Downloader</h1>
        <p>Download YouTube videos with custom quality and format options</p>
    </div>
    """, unsafe_allow_html=True)

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.subheader("📥 Download Video")

        # URL input
        url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any YouTube video or playlist URL here"
        )

        # Validate URL and get info
        video_info = None
        if url:
            is_valid, processed_url = URLValidator.validate_url(url, interactive=False)
            if is_valid:
                video_info = get_video_info(processed_url)
                url = processed_url  # Use processed URL

                if video_info:
                    # Display video information
                    st.markdown('<div class="info-box">', unsafe_allow_html=True)
                    st.markdown("### 📺 Video Information")

                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.write(f"**Title:** {video_info.get('title', 'Unknown')}")
                        st.write(f"**Uploader:** {video_info.get('uploader', 'Unknown')}")
                        st.write(f"**Duration:** {format_duration(video_info.get('duration', 0))}")

                    with col_info2:
                        # Display views without comma formatting
                        view_count = video_info.get('view_count')
                        if view_count:
                            st.write(f"**Views:** {view_count}")
                        else:
                            st.write("**Views:** Unknown")

                        # Format upload date to YYYY-MM-DD
                        upload_date = format_upload_date(video_info.get('upload_date', 'Unknown'))
                        st.write(f"**Upload Date:** {upload_date}")

                        if video_info.get('description'):
                            with st.expander("📄 Description"):
                                st.write(video_info['description'][:500] + "..." if len(video_info['description']) > 500 else video_info['description'])

                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("❌ Invalid YouTube URL. Please check the URL and try again.")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("⚙️ Download Options")

        # Quality selection
        quality_options = {
            "Best Quality": Quality.BEST,
            "4K (2160p)": Quality.HD_4K,
            "HD (1080p)": Quality.HD_1080,  # Default
            "HD (720p)": Quality.HD_720,
            "Audio Only (MP3)": Quality.AUDIO_ONLY
        }

        selected_quality = st.selectbox(
            "Video Quality",
            options=list(quality_options.keys()),
            index=2,  # Default to HD 1080p
            help="Choose the video quality for download"
        )
        quality = quality_options[selected_quality]

        # Format selection (only for video downloads)
        if quality != Quality.AUDIO_ONLY:
            format_options = {
                "Original (from YouTube)": None,  # Let yt-dlp choose
                "MP4 (Best Compatibility)": VideoFormat.MP4,
                "WebM (Smaller Size)": VideoFormat.WEBM,
                "MKV (High Quality)": VideoFormat.MKV
            }

            selected_format = st.selectbox(
                "Video Format",
                options=list(format_options.keys()),
                index=1,  # Default to MP4
                help="Choose output video format"
            )
            video_format = format_options[selected_format]
            force_convert = selected_format != "Original (from YouTube)"
        else:
            video_format = VideoFormat.MP4  # Not used for audio
            force_convert = False

        # Output directory
        current_dir = os.getcwd()
        output_dir = st.text_input(
            "Output Directory",
            value=current_dir,
            help="Directory where files will be saved"
        )

        # Custom filename
        suggested_filename = ""
        if video_info and video_info.get('title'):
            suggested_filename = clean_filename(video_info['title'])

        custom_filename = st.text_input(
            "Custom Filename (optional)",
            value="",
            placeholder=suggested_filename,
            help="Leave empty to use video title as filename"
        )

        # Playlist option
        is_playlist = False
        if url and ('playlist' in url.lower() or 'list=' in url):
            is_playlist = st.checkbox(
                "Download entire playlist",
                value=True,
                help="Download all videos in the playlist"
            )
        else:
            is_playlist = st.checkbox(
                "Download as playlist",
                value=False,
                help="Attempt to download as playlist if available"
            )

    # Download section
    st.markdown("---")

    if url and video_info:
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

        with col_btn1:
            download_btn = st.button(
                "🚀 Download",
                type="primary",
                disabled=st.session_state.is_downloading,
                help="Start downloading the video"
            )

        with col_btn2:
            if st.button("🔄 Refresh Info", help="Reload video information"):
                # Clear cache and reload
                cache_key = f"video_info_{hash(url)}"
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                st.rerun()

        # Download process
        if download_btn and not st.session_state.is_downloading:
            st.session_state.is_downloading = True

            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Create downloader with custom progress hook
                progress_hook = StreamlitProgressHook(progress_bar, status_text)
                downloader = YouTubeDownloader(
                    output_dir=output_dir,
                    custom_filename=custom_filename if custom_filename else None,
                    preferred_format=video_format if video_format else VideoFormat.MP4
                )

                # Replace the progress hook
                downloader.progress_hook = progress_hook

                # Start download
                status_text.text("🚀 Starting download...")
                success = downloader.download(
                    url=url,
                    quality=quality,
                    is_playlist=is_playlist,
                    video_info=video_info,
                    force_convert=force_convert
                )

                if success:
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>✅ Download Completed Successfully!</h4>
                        <p><strong>📁 Files saved to:</strong> {os.path.abspath(output_dir)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="error-box">
                        <h4>❌ Download Failed</h4>
                        <p>Please check the URL, your internet connection, or try a different quality setting.</p>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error during download: {str(e)}")

            finally:
                st.session_state.is_downloading = False

    elif url and not video_info:
        st.warning("⚠️ Could not retrieve video information. Please check the URL.")


if __name__ == "__main__":
    main()
