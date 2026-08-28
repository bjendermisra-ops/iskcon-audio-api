from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "ISKCON Real Audio API is Live & Running!"})

@app.route('/audio')
def get_audio():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "Video ID missing"}), 400

    yt_url = f"https://www.youtube.com/watch?v={video_id}"

    # --- ENGINE 1: Cobalt Media Stream Resolver (Bypasses Datacenter Bot Protection) ---
    cobalt_nodes = [
        "https://api.cobalt.tools",
        "https://cobalt-api.kwiatek.xyz"
    ]
    for c_node in cobalt_nodes:
        try:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            payload = {
                "url": yt_url,
                "downloadMode": "audio",
                "audioFormat": "mp3"
            }
            c_res = requests.post(c_node, json=payload, headers=headers, timeout=8)
            if c_res.status_code == 200:
                c_data = c_res.json()
                audio_url = c_data.get('url')
                if audio_url:
                    return jsonify({
                        "id": video_id,
                        "title": "Playing Audio Stream",
                        "channel": "ISKCON Real Audio",
                        "thumb": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                        "audioUrl": audio_url
                    })
        except Exception as e_cobalt:
            continue

    # --- ENGINE 2: Invidious Instances with Adaptive Audio Streams ---
    invidious_nodes = [
        "https://yewtu.be",
        "https://invidious.flokinet.to",
        "https://vid.puffyan.us"
    ]
    for node in invidious_nodes:
        try:
            res = requests.get(f"{node}/api/v1/videos/{video_id}", timeout=6)
            if res.status_code == 200:
                vdata = res.json()
                audio_url = None
                if vdata.get('hlsUrl'):
                    audio_url = vdata.get('hlsUrl')
                elif 'adaptiveFormats' in vdata:
                    audios = [f for f in vdata['adaptiveFormats'] if 'audio' in f.get('type', '')]
                    if audios:
                        audio_url = audios[-1].get('url')
                elif 'formatStreams' in vdata and len(vdata['formatStreams']) > 0:
                    audio_url = vdata['formatStreams'][-1].get('url')

                if audio_url:
                    return jsonify({
                        "id": video_id,
                        "title": vdata.get('title'),
                        "channel": vdata.get('author') or "ISKCON",
                        "duration": vdata.get('lengthSeconds'),
                        "thumb": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                        "audioUrl": audio_url
                    })
        except Exception as e_inv:
            continue

    # --- ENGINE 3: yt-dlp Fallback ---
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'skip_download': True,
            'nocheckcertificate': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            audio_url = info.get('url')
            if not audio_url and 'formats' in info:
                audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none']
                if audio_formats:
                    audio_url = audio_formats[-1].get('url')

            if audio_url:
                return jsonify({
                    "id": video_id,
                    "title": info.get('title'),
                    "channel": info.get('uploader') or "ISKCON",
                    "duration": info.get('duration'),
                    "thumb": info.get('thumbnail') or f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                    "audioUrl": audio_url
                })
    except Exception as e_ytdl:
        pass

    return jsonify({"error": "Unable to extract stream link from all engine nodes"}), 500

@app.route('/search')
def search():
    query = request.args.get('q', 'ISKCON Kirtan')
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'skip_download': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch25:{query}", download=False)
            items = []
            for entry in results.get('entries', []):
                items.append({
                    "id": entry.get('id'),
                    "title": entry.get('title'),
                    "channel": entry.get('uploader') or entry.get('channel') or "ISKCON",
                    "thumb": f"https://i.ytimg.com/vi/{entry.get('id')}/mqdefault.jpg",
                    "duration": entry.get('duration')
                })
            return jsonify({"items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
