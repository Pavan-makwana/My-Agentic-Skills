---
name: youtube-media-extractor
description: >-
  Extracts high-fidelity audio (48kHz stereo MP3/AAC) and vertical/horizontal video
  from YouTube URLs or song search queries in a single automated step using yt-dlp and FFmpeg.
---

# YouTube Media Extractor

One-step media downloader and transcoder optimized for studio-quality audio extraction for music videos and Instagram Reels.

```mermaid
flowchart LR
    A[YouTube URL or Song Query] --> B[yt-dlp Best Audio / Video Stream]
    B --> C[FFmpeg 48kHz Stereo Re-sampling]
    C --> D[Standardized MP3/WAV Audio File]
```

## When to Use
- You need high-bitrate audio from an official music video, cover, or acoustic session.
- You want to extract an exact segment of audio without manual browser downloads.

## Single Command Execution
```bash
# Download and transcode best audio stream to 48kHz stereo MP3
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  --postprocessor-args "-ar 48000 -ac 2" \
  -o "song.mp3" "<YOUTUBE_URL>"
```

## Python Automation Wrapper
```python
import subprocess

def download_youtube_audio(youtube_url, output_path="song.mp3"):
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--postprocessor-args", "ffmpeg:-ar 48000 -ac 2",
        "-o", output_path,
        youtube_url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {res.stderr}")
    return output_path
```

## Finding Songs by Query
```bash
yt-dlp "ytsearch1:Sachin Siby Kanmani Anbodu" -x --audio-format mp3 -o "kanmani_song.mp3"
```
