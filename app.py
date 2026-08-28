from flask import Flask, request, jsonify
from flask_cors import CORS
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

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'skip_download': True,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 1. Direct URL check
            audio_url = info.get('url')
            
            # 2. Formats array fallback (Extract real .m4a / audio stream)
            if not audio_url and 'formats' in info:
                audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none']
                if audio_formats:
                    audio_url = audio_formats[-1].get('url')
                elif len(info['formats']) > 0:
                    audio_url = info['formats'][0].get('url')

            if not audio_url:
                return jsonify({"error": "Audio stream link not found"}), 404

            return jsonify({
                "id": video_id,
                "title": info.get('title'),
                "channel": info.get('uploader') or info.get('channel') or "ISKCON",
                "duration": info.get('duration'),
                "thumb": info.get('thumbnail') or f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                "audioUrl": audio_url
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
