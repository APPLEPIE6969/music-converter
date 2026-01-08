from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import time

app = Flask(__name__)

# The Website HTML design
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>YT Music Converter</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; background: #222; color: #fff; }
        input { padding: 10px; width: 300px; border-radius: 5px; border: none; }
        select { padding: 10px; border-radius: 5px; border: none; }
        button { padding: 10px 20px; background: #e62117; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #cc1d14; }
        .container { background: #333; padding: 40px; border-radius: 10px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🎵 YT Music Converter</h2>
        <form action="/convert" method="post">
            <input type="text" name="url" placeholder="Paste YouTube/Music Link..." required>
            <br><br>
            <label>Format:</label>
            <select name="format">
                <option value="m4a">M4A (Best Quality)</option>
                <option value="flac">FLAC (Lossless)</option>
                <option value="mp3">MP3 (Standard)</option>
            </select>
            <br><br>
            <button type="submit">Convert & Download</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/convert', methods=['POST'])
def convert():
    url = request.form.get('url')
    fmt = request.form.get('format')
    
    # Create a unique filename based on time to avoid errors
    timestamp = int(time.time())
    output_path = f"/tmp/{timestamp}"

    # Configuration for yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path + '.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        # Fake a browser User-Agent to try and avoid 429 blocks
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': fmt,
            'preferredquality': '192',
        }],
    }

    try:
        # Run the download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'music')
            
            # Find the file that was created
            final_filename = f"{output_path}.{fmt}"
            
            # Send file to user
            return send_file(
                final_filename, 
                as_attachment=True, 
                download_name=f"{title}.{fmt}"
            )

    except Exception as e:
        error_message = str(e)
        if "429" in error_message:
            return "<h3>Error: Server IP Blocked by YouTube (Error 429).</h3><p>This happens with free cloud hosting. Try again later.</p>"
        return f"<h3>Error:</h3> <p>{error_message}</p>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
