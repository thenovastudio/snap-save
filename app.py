#!/usr/bin/env python3
"""EverythingSave - Social Media Video Downloader Backend"""

import os
import re
import json
import uuid
import shutil
import logging
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Flask, render_template, request, jsonify,
    send_file, abort
)
from flask_cors import CORS

try:
    import yt_dlp
except ImportError:
    raise ImportError("yt-dlp is required. Install it with: pip install yt-dlp")

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB request limit
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "everythingsave-dev-key")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Temp download directory (cleaned per-request)
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", tempfile.gettempdir())

# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------
PLATFORMS = [
    {"name": "YouTube",      "icon": "fab fa-youtube",        "color": "#FF0000", "patterns": [r"youtube\.com", r"youtu\.be"]},
    {"name": "TikTok",       "icon": "fab fa-tiktok",         "color": "#00F2EA", "patterns": [r"tiktok\.com"]},
    {"name": "Instagram",    "icon": "fab fa-instagram",      "color": "#E1306C", "patterns": [r"instagram\.com"]},
    {"name": "Twitter / X",  "icon": "fab fa-x-twitter",      "color": "#FFFFFF", "patterns": [r"twitter\.com", r"x\.com"]},
    {"name": "Facebook",     "icon": "fab fa-facebook",       "color": "#1877F2", "patterns": [r"facebook\.com", r"fb\.watch"]},
    {"name": "Reddit",       "icon": "fab fa-reddit-alien",   "color": "#FF4500", "patterns": [r"reddit\.com", r"redd\.it"]},
    {"name": "Snapchat",     "icon": "fab fa-snapchat",       "color": "#FFFC00", "patterns": [r"snapchat\.com"]},
    {"name": "Pinterest",    "icon": "fab fa-pinterest",      "color": "#E60023", "patterns": [r"pinterest\.com", r"pin\.it"]},
    {"name": "Vimeo",        "icon": "fab fa-vimeo-v",        "color": "#1AB7EA", "patterns": [r"vimeo\.com"]},
    {"name": "Twitch",       "icon": "fab fa-twitch",         "color": "#9146FF", "patterns": [r"twitch\.tv"]},
    {"name": "SoundCloud",   "icon": "fab fa-soundcloud",     "color": "#FF5500", "patterns": [r"soundcloud\.com"]},
    {"name": "Dailymotion",  "icon": "fas fa-play-circle",    "color": "#00AAFF", "patterns": [r"dailymotion\.com", r"dai\.ly"]},
]


def detect_platform(url: str) -> dict | None:
    """Return platform info dict or None if unrecognised."""
    for p in PLATFORMS:
        for pat in p["patterns"]:
            if re.search(pat, url, re.IGNORECASE):
                return {"name": p["name"], "icon": p["icon"], "color": p["color"]}
    return None


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


# ---------------------------------------------------------------------------
# yt-dlp helpers
# ---------------------------------------------------------------------------
def _base_ydl_opts() -> dict:
    """Shared yt-dlp options."""
    return {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "socket_timeout": 30,
        "retries": 3,
        "extractor_retries": 3,
        "geo_bypass": True,
        "nocheckcertificate": True,
    }


def extract_info(url: str) -> dict:
    """Extract video metadata without downloading."""
    opts = _base_ydl_opts()
    opts["skip_download"] = True

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info is None:
        raise ValueError("Could not extract video information.")

    # --- Build a simplified format list --------------------------------
    formats_out = []
    seen = set()
    raw_formats = info.get("formats") or []

    for f in raw_formats:
        fid = f.get("format_id", "")
        ext = f.get("ext", "mp4")
        height = f.get("height")
        width = f.get("width")
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")
        filesize = f.get("filesize") or f.get("filesize_approx")
        tbr = f.get("tbr")

        has_video = vcodec and vcodec != "none"
        has_audio = acodec and acodec != "none"

        if has_video and height:
            quality_label = f"{height}p"
        elif has_audio and not has_video:
            quality_label = "Audio only"
        else:
            quality_label = f.get("format_note", fid)

        key = (quality_label, ext)
        if key in seen:
            continue
        seen.add(key)

        formats_out.append({
            "format_id": fid,
            "ext": ext,
            "quality": quality_label,
            "height": height,
            "width": width,
            "has_video": has_video,
            "has_audio": has_audio,
            "filesize": filesize,
            "tbr": tbr,
        })

    # Sort: highest resolution first, then by bitrate
    formats_out.sort(
        key=lambda x: (x.get("height") or 0, x.get("tbr") or 0),
        reverse=True,
    )

    # Duration
    duration_secs = info.get("duration")
    if duration_secs:
        mins, secs = divmod(int(duration_secs), 60)
        hours, mins = divmod(mins, 60)
        duration_str = f"{hours}:{mins:02d}:{secs:02d}" if hours else f"{mins}:{secs:02d}"
    else:
        duration_str = None

    platform = detect_platform(url)

    return {
        "title": info.get("title", "Untitled"),
        "thumbnail": info.get("thumbnail"),
        "duration": duration_str,
        "duration_secs": duration_secs,
        "uploader": info.get("uploader"),
        "view_count": info.get("view_count"),
        "platform": platform,
        "formats": formats_out,
        "url": url,
    }


def download_video(url: str, format_id: str | None = None) -> str:
    """Download video to a temp directory and return the file path."""
    dl_dir = os.path.join(DOWNLOAD_DIR, f"snapsave_{uuid.uuid4().hex[:12]}")
    os.makedirs(dl_dir, exist_ok=True)

    opts = _base_ydl_opts()
    opts["outtmpl"] = os.path.join(dl_dir, "%(title).80s.%(ext)s")
    opts["merge_output_format"] = "mp4"
    opts["postprocessors"] = [{
        "key": "FFmpegVideoConvertor",
        "preferedformat": "mp4",
    }]

    if format_id and format_id != "best":
        opts["format"] = f"{format_id}+bestaudio/best[ext=mp4]/best"
    else:
        opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    # Find the downloaded file
    files = list(Path(dl_dir).glob("*"))
    if not files:
        shutil.rmtree(dl_dir, ignore_errors=True)
        raise FileNotFoundError("Download completed but no file found.")

    return str(files[0])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def api_info():
    """Return video metadata for a given URL."""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Please provide a URL."}), 400
    if not is_valid_url(url):
        return jsonify({"error": "Invalid URL. Please enter a valid video link."}), 400

    try:
        info = extract_info(url)
        return jsonify(info)
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "age" in msg.lower() or "login" in msg.lower():
            return jsonify({"error": "This video is age-restricted or requires login."}), 403
        if "unsupported" in msg.lower():
            return jsonify({"error": "This URL is not supported. Try a different link."}), 400
        logger.error("yt-dlp DownloadError: %s", msg)
        return jsonify({"error": "Could not fetch video info. Please check the URL and try again."}), 400
    except Exception as e:
        logger.exception("Unexpected error in /api/info")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    """Download the video and stream it to the client."""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    format_id = (data.get("format_id") or "").strip() or None

    if not url:
        return jsonify({"error": "Please provide a URL."}), 400
    if not is_valid_url(url):
        return jsonify({"error": "Invalid URL."}), 400

    filepath = None
    try:
        filepath = download_video(url, format_id)
        filename = os.path.basename(filepath)
        safe_name = re.sub(r'[^\w\s.\-]', '', filename).strip() or "video.mp4"

        response = send_file(
            filepath,
            as_attachment=True,
            download_name=safe_name,
            mimetype="video/mp4",
        )

        @response.call_on_close
        def _cleanup():
            try:
                parent = os.path.dirname(filepath)
                if "snapsave_" in parent:
                    shutil.rmtree(parent, ignore_errors=True)
            except Exception:
                pass

        return response

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        logger.error("Download error: %s", msg)
        if filepath:
            parent = os.path.dirname(filepath)
            if "snapsave_" in parent:
                shutil.rmtree(parent, ignore_errors=True)
        return jsonify({"error": "Download failed. The video may be unavailable or restricted."}), 400
    except Exception as e:
        logger.exception("Unexpected error in /api/download")
        return jsonify({"error": "An unexpected error occurred during download."}), 500


@app.route("/api/platforms", methods=["GET"])
def api_platforms():
    """Return list of supported platforms."""
    return jsonify([{"name": p["name"], "icon": p["icon"], "color": p["color"]} for p in PLATFORMS])


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found."}), 404


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Request too large."}), 413


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error."}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    logger.info("Starting EverythingSave on port %d (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
