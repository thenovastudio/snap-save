```
 _____                      _   _     _             ____                  
| ____|_   _____ _ __ _   _| |_| |__ (_)_ __   __ _/ ___|  __ ___   _____ 
|  _| \ \ / / _ \ '__| | | | __| '_ \| | '_ \ / _` \___ \ / _` \ \ / / _ \
| |___ \ V /  __/ |  | |_| | |_| | | | | | | | (_| |___) | (_| |\ V /  __/
|_____| \_/ \___|_|   \__, |\__|_| |_|_|_| |_|\__, |____/ \__,_| \_/ \___|
                      |___/                   |___/
```

# EverythingSave

**A sleek, modern social media video downloader.** Paste any share link and download videos instantly.

Built with a premium dark glassmorphism UI, EverythingSave supports all major social media platforms with a single, beautiful interface.

---

## Screenshots

> _Screenshots coming soon -- run the app locally to see the UI!_

---

## Supported Platforms

| Platform     | Status |
|-------------|--------|
| YouTube      | Supported |
| TikTok       | Supported |
| Instagram    | Supported |
| Twitter / X  | Supported |
| Facebook     | Supported |
| Reddit       | Supported |
| Snapchat     | Supported |
| Pinterest    | Supported |
| Vimeo        | Supported |
| Twitch       | Supported |
| SoundCloud   | Supported |
| Dailymotion  | Supported |
| _...and 1000+ more via yt-dlp_ | Supported |

---

## Features

- **Universal Downloads** -- Supports YouTube, TikTok, Instagram, Twitter/X, Facebook, Reddit, Snapchat, and many more
- **Quality Selection** -- Choose from all available resolutions and formats
- **Platform Detection** -- Automatically identifies the source platform with branded icons
- **Modern UI** -- Premium dark glassmorphism design with smooth animations
- **Responsive** -- Fully mobile-friendly, works on any device
- **No Registration** -- No accounts, no sign-ups, completely free
- **Paste & Go** -- Just paste a link and hit Enter
- **Clipboard Support** -- One-click paste from clipboard
- **Error Handling** -- Clear, user-friendly error messages
- **Docker Ready** -- Deploy anywhere with Docker

---

## Quick Start

### Prerequisites

- Python 3.10+
- ffmpeg (required for merging video+audio streams)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/snap-save.git
cd snap-save

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open your browser and navigate to **http://localhost:5000**

### Install ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# Windows (via Chocolatey)
choco install ffmpeg
```

---

## Docker

### Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Using Docker directly

```bash
# Build the image
docker build -t snapsave .

# Run the container
docker run -d -p 5000:5000 --name snapsave snapsave
```

Access the app at **http://localhost:5000**

---

## Tech Stack

| Component  | Technology |
|-----------|------------|
| Backend    | Flask 3.1 (Python) |
| Downloader | yt-dlp |
| Frontend   | HTML5, CSS3, Vanilla JavaScript |
| Fonts      | Inter (Google Fonts) |
| Icons      | Font Awesome 6 |
| Container  | Docker + Gunicorn |

---

## API Endpoints

### `GET /`

Serves the main web interface.

### `POST /api/info`

Fetch video metadata.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "title": "Video Title",
  "thumbnail": "https://...",
  "duration": "3:32",
  "uploader": "Channel Name",
  "platform": {
    "name": "YouTube",
    "icon": "fab fa-youtube",
    "color": "#FF0000"
  },
  "formats": [
    {
      "format_id": "137",
      "ext": "mp4",
      "quality": "1080p",
      "height": 1080,
      "has_video": true,
      "has_audio": false,
      "filesize": 52428800
    }
  ]
}
```

### `POST /api/download`

Download the video file.

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": "137"
}
```

**Response:** Binary file stream with `Content-Disposition` header.

### `GET /api/platforms`

Returns list of supported platforms with icons and colors.

---

## Environment Variables

| Variable       | Default          | Description                    |
|---------------|-----------------|--------------------------------|
| `PORT`         | `5000`           | Server port                    |
| `FLASK_DEBUG`  | `0`              | Enable debug mode (`1` / `0`)  |
| `SECRET_KEY`   | `snapsave-dev-key` | Flask secret key             |
| `DOWNLOAD_DIR` | System temp dir  | Temporary download directory   |

---

## Project Structure

```
snap-save/
|-- app.py                  # Flask backend
|-- requirements.txt        # Python dependencies
|-- Dockerfile              # Docker image definition
|-- docker-compose.yml      # Docker Compose config
|-- .gitignore
|-- README.md
|-- templates/
|   |-- index.html          # Main HTML template
|-- static/
    |-- css/
    |   |-- style.css        # Glassmorphism styles
    |-- js/
        |-- script.js        # Frontend logic
```

---

## Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure to update tests as appropriate and follow the existing code style.

---

## License

This project is licensed under the **MIT License** -- see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

EverythingSave is intended for **personal use only**. Please respect the terms of service of each platform and the copyright of content creators.

- Do not use this tool to download copyrighted content without permission.
- Do not redistribute downloaded content without the creator's consent.
- This tool is provided as-is with no warranty.
- The developers are not responsible for any misuse of this software.

Always support content creators by engaging with their content on the original platforms.
