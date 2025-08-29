# YouTube Downloader

A powerful and user-friendly YouTube video downloader with both command-line interface (CLI) and web-based GUI. Download videos in various qualities and formats with support for playlists, custom filenames, and format conversion.

## Features

### Core Functionality
- **Multiple Quality Options**: Best, 4K, 1080p, 720p, and audio-only downloads
- **Format Conversion**: Support for MP4, WebM, MKV, and AVI output formats
- **Playlist Support**: Download entire playlists or individual videos
- **Custom Filenames**: Set custom output filenames for downloads
- **Smart Format Selection**: Automatically prefers MP4 for better compatibility

### Interface Options
- **Command Line Interface**: Full-featured CLI with interactive and batch modes
- **Web GUI**: Modern Streamlit-based web interface for easy use
- **Flexible URL Support**: Handles various YouTube URL formats including shorts, playlists, and channels

### Advanced Features
- **Progress Tracking**: Real-time download progress with file size information
- **Error Handling**: Robust error handling with helpful suggestions
- **Directory Management**: Automatic output directory creation
- **URL Validation**: Smart URL validation with fallback support

## Installation

### Prerequisites
- Python 3.7 or higher
- FFmpeg (for format conversion)

### Quick Setup

#### Using uv (recommended)
```bash
git clone https://github.com/username/youtube-downloader.git
cd youtube-downloader
uv install
```

#### Using pip
```bash
git clone https://github.com/username/youtube-downloader.git
cd youtube-downloader
pip install -r requirements.txt
```

### Install FFmpeg
- **Windows**: Download from [FFmpeg official site](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`

## Usage

### Command Line Interface

#### Interactive Mode
```bash
python src/downloader.py
```

#### Direct Download
```bash
python src/downloader.py "https://youtube.com/watch?v=VIDEO_ID"
```

#### Advanced Options
```bash
python src/downloader.py "VIDEO_URL" --quality 1080p --format mp4 --output ./downloads
```

#### Command Line Arguments
- `--output, -o`: Output directory (default: current directory)
- `--filename, -f`: Custom filename for single videos
- `--quality, -q`: Video quality (`best`, `4k`, `1080p`, `720p`, `audio`)
- `--format`: Output format (`mp4`, `webm`, `mkv`, `avi`)
- `--force-convert`: Force conversion to specified format
- `--playlist, -p`: Download entire playlist
- `--no-interactive`: Skip interactive prompts
- `--silent`: Minimal output mode

### Web Interface

#### Start the GUI
```bash
streamlit run src/app.py
```

Then open your browser to `http://localhost:8501`

#### Features
- **Video Information Display**: Shows title, duration, uploader, and description
- **Quality Selection**: Choose from multiple quality options
- **Format Conversion**: Select output format with conversion options
- **Real-time Progress**: Live download progress with file size tracking
- **Custom Settings**: Set output directory and filenames

## Examples

### CLI Examples
```bash
# Download best quality video
python src/downloader.py "https://youtu.be/dQw4w9WgXcQ"

# Download 720p video as MP4
python src/downloader.py "VIDEO_URL" --quality 720p --format mp4

# Download entire playlist
python src/downloader.py "PLAYLIST_URL" --playlist

# Audio-only download
python src/downloader.py "VIDEO_URL" --quality audio

# Batch mode with custom settings
python src/downloader.py "VIDEO_URL" --quality 1080p --format mp4 --output ./downloads --no-interactive
```

### Supported URL Formats
- `https://youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/playlist?list=PLAYLIST_ID`
- `https://youtube.com/shorts/VIDEO_ID`
- `https://youtube.com/@CHANNEL_NAME`
- And many more YouTube URL variations

## Configuration

### Quality Options
- **Best**: Highest available quality (MP4 preferred)
- **4K**: Up to 2160p resolution
- **1080p**: Full HD quality
- **720p**: HD quality
- **Audio**: MP3 audio extraction

### Format Options
- **MP4**: Best compatibility across devices
- **WebM**: Smaller file sizes
- **MKV**: High quality with metadata support
- **AVI**: Legacy compatibility

## File Structure

```
youtube-downloader/
├── src/
│   ├── downloader.py          # Core downloader with CLI
│   └── app.py                 # Web interface
├── downloads/                 # Default output directory
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## Dependencies

Core dependencies (see `requirements.txt`):
- `yt-dlp`: YouTube downloading engine
- `streamlit`: Web interface framework
- Standard library: `pathlib`, `argparse`, `enum`

## Troubleshooting

### Common Issues

**"Command not found" errors:**
- Ensure Python and pip are installed and in PATH
- Try `python3` instead of `python`

**Download fails:**
- Check internet connection
- Verify the URL is accessible
- Try a different quality setting
- Use `--force-convert` for format issues

**FFmpeg not found:**
- Install FFmpeg and ensure it's in your system PATH
- Restart your terminal after installation

**Permission errors:**
- Check write permissions for output directory
- Try running with administrator privileges if needed

### Advanced Troubleshooting
- Use `--force` flag to bypass URL validation
- Enable `--silent` mode to reduce output for debugging
- Check yt-dlp updates: `pip install -U yt-dlp`
- If your video player can't play the downloaded MP4 file, try playing it with VLC media player, or re-encode for better compatibility using FFmpeg (this may take several minutes):
```bash
# Replace paths with your actual file locations
ffmpeg -i "downloads/myfile.mp4" -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 192k "downloads/myfile_compatible.mp4"
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is for personal use only. Please respect YouTube's Terms of Service and copyright laws. Only download content you have permission to download.
