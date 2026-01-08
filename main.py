from flask import Flask, request, send_file
import yt_dlp
import os
import time

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h2>Simple Music Converter</h2>
    <form action="/convert">
        <input type="text" name="url" placeholder="Paste Link Here" required style="width: 300px;">
        <select name="fmt">
            <option value="m4a">M4A</option>
            <option value="flac">FLAC</option>
        </select>
        <button type="submit">Convert & Download</button>
    </form>
    '''

@app.route('/convert')
def convert():
    url = request.args.get('url')
    fmt = request.args.get('fmt', 'm4a')
    
    # Random filename to prevent conflicts
    temp_name = f"song_{int(time.time())}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': fmt,
        }],
        'outtmpl': f'/tmp/{temp_name}.%(ext)s',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            file_path = f"/tmp/{temp_name}.{fmt}"
            return send_file(file_path, as_attachment=True, download_name=f"music.{fmt}")
    except Exception as e:
        return f"Error (YouTube likely blocked this server IP): {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
