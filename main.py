from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import time
import subprocess

app = Flask(__name__)

# --- MODERN UI HTML/CSS ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SonicStream Converter</title>
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Poppins:wght@500;700&display=swap" rel="stylesheet">
    <!-- Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --accent: #ff0033; /* YouTube Red */
            --accent-hover: #cc0000;
            --text-main: #ffffff;
            --text-muted: #a0a0a0;
            --input-bg: #2a2a2a;
            --border: #333;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at top right, #2a1010 0%, transparent 40%), 
                              radial-gradient(circle at bottom left, #10152a 0%, transparent 40%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: var(--card-bg);
            width: 100%;
            max-width: 550px;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            border: 1px solid var(--border);
            animation: slideIn 0.6s ease-out;
            position: relative;
            overflow: hidden;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .header {
            text-align: center;
            margin-bottom: 35px;
        }

        h2 {
            font-family: 'Poppins', sans-serif;
            font-size: 28px;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #fff, #bbb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        p.subtitle {
            color: var(--text-muted);
            font-size: 14px;
        }

        .form-group {
            margin-bottom: 25px;
            text-align: left;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .input-wrapper {
            position: relative;
        }

        .input-wrapper i {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
        }

        input[type="text"] {
            width: 100%;
            padding: 16px 16px 16px 45px;
            background: var(--input-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: white;
            font-size: 15px;
            font-family: 'Inter', sans-serif;
            transition: 0.3s;
        }

        select {
            width: 100%;
            padding: 16px;
            background: var(--input-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: white;
            font-size: 15px;
            font-family: 'Inter', sans-serif;
            appearance: none; /* Remove default arrow */
            cursor: pointer;
            transition: 0.3s;
        }
        
        /* Custom arrow for select */
        .select-wrapper {
            position: relative;
        }
        
        .select-wrapper::after {
            content: '\\f078';
            font-family: "Font Awesome 6 Free";
            font-weight: 900;
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            pointer-events: none;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(255, 0, 51, 0.2);
        }

        button {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, var(--accent), #d9002b);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 20px rgba(255, 0, 51, 0.2);
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px rgba(255, 0, 51, 0.4);
        }

        button:active {
            transform: translateY(1px);
        }

        optgroup {
            color: var(--text-muted);
            font-style: normal;
            font-weight: 600;
        }

        option {
            background: #222;
            color: white;
            padding: 10px;
        }

        /* Loading Overlay */
        #loader {
            display: none;
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(30, 30, 30, 0.95);
            border-radius: 20px;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 10;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255,255,255,0.1);
            border-top: 4px solid var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }

        @keyframes spin { 100% { transform: rotate(360deg); } }

        .loader-text {
            font-weight: 600;
            letter-spacing: 1px;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }

    </style>
</head>
<body>

    <div class="container">
        <!-- Loading Screen (Hidden by default) -->
        <div id="loader">
            <div class="spinner"></div>
            <div class="loader-text">CONVERTING...</div>
            <p style="font-size: 12px; color: #888; margin-top: 10px;">This may take up to 20 seconds</p>
        </div>

        <div class="header">
            <h2><i class="fa-brands fa-youtube" style="color: var(--accent); margin-right: 10px;"></i>SonicStream</h2>
            <p class="subtitle">Premium Cloud Audio Converter</p>
        </div>

        <form action="/convert" method="post" onsubmit="showLoader()">
            
            <div class="form-group">
                <label>YouTube Link</label>
                <div class="input-wrapper">
                    <i class="fa-solid fa-link"></i>
                    <input type="text" name="url" placeholder="https://youtu.be/..." required autocomplete="off">
                </div>
            </div>

            <div class="form-group">
                <label>Output Format</label>
                <div class="select-wrapper">
                    <select name="format">
                        <optgroup label="Popular / High Quality">
                            <option value="m4a" selected>M4A (AAC) - Best for Apple/Mobile</option>
                            <option value="mp3">MP3 (320kbps) - Universal</option>
                            <option value="flac">FLAC - Lossless Quality</option>
                            <option value="wav">WAV - Uncompressed</option>
                            <option value="opus">OPUS - High Efficiency</option>
                        </optgroup>

                        <optgroup label="Professional / Lossless">
                            <option value="alac">ALAC - Apple Lossless</option>
                            <option value="aiff">AIFF - Studio Quality</option>
                            <option value="ape">APE - Monkey's Audio</option>
                            <option value="wv">WV - WavPack</option>
                            <option value="tta">TTA - True Audio</option>
                        </optgroup>

                        <optgroup label="Legacy & Specific">
                            <option value="wma">WMA - Windows Media</option>
                            <option value="ogg">OGG - Vorbis</option>
                            <option value="3gp">3GP - Low Data Mobile</option>
                        </optgroup>

                        <optgroup label="Telephony (Low Quality)">
                            <option value="amr">AMR - Speech Codec</option>
                            <option value="gsm">GSM - Global System</option>
                            <option value="vox">VOX - ADPCM</option>
                            <option value="8svx">8SVX - Amiga 8-bit</option>
                        </optgroup>
                    </select>
                </div>
            </div>

            <button type="submit">START CONVERSION</button>

        </form>
    </div>

    <script>
        function showLoader() {
            document.getElementById('loader').style.display = 'flex';
        }
        
        // Hide loader if user hits back button in browser
        window.onpageshow = function(event) {
            if (event.persisted) {
                document.getElementById('loader').style.display = 'none';
            }
        };
    </script>

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
    
    timestamp = int(time.time())
    # Temporary paths
    temp_wav = f"/tmp/{timestamp}_temp.wav"
    final_output = f"/tmp/{timestamp}.{fmt}"

    # 1. Download source as WAV (Best intermediary)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'/tmp/{timestamp}_temp.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
    }

    try:
        # Step 1: Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'audio_converted')
            # Clean title
            clean_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ' or c in '-_']).strip()

        # Step 2: Convert logic
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', temp_wav]

        # Quality settings
        if fmt == 'mp3':
            ffmpeg_cmd.extend(['-b:a', '320k'])
        elif fmt == 'aac' or fmt == 'm4a':
            ffmpeg_cmd.extend(['-c:a', 'aac', '-b:a', '256k'])
        elif fmt == 'ogg':
            ffmpeg_cmd.extend(['-c:a', 'libvorbis', '-q:a', '10'])
        elif fmt == 'opus':
            ffmpeg_cmd.extend(['-c:a', 'libopus', '-b:a', '192k'])
        elif fmt == 'wma':
            ffmpeg_cmd.extend(['-c:a', 'wmav2', '-b:a', '192k'])
        elif fmt == 'amr':
            ffmpeg_cmd.extend(['-ar', '8000', '-ac', '1', '-c:a', 'libopencore_amrnb'])
        elif fmt == 'gsm':
            ffmpeg_cmd.extend(['-ar', '8000', '-ac', '1', '-c:a', 'gsm'])
        elif fmt == 'vox':
            ffmpeg_cmd.extend(['-f', 'u8', '-c:a', 'pcm_u8', '-ar', '8000', '-ac', '1'])
        elif fmt == 'voc':
            ffmpeg_cmd.extend(['-c:a', 'pcm_u8'])
        elif fmt == '8svx':
            ffmpeg_cmd.extend(['-c:a', 'pcm_s8', '-f', 'iff'])
        elif fmt == 'rf64':
             ffmpeg_cmd.extend(['-f', 'rf64'])
        
        ffmpeg_cmd.append(final_output)

        # Run conversion
        subprocess.run(ffmpeg_cmd, check=True)

        # Step 3: Send file
        return send_file(
            final_output, 
            as_attachment=True, 
            download_name=f"{clean_title}.{fmt}"
        )

    except Exception as e:
        # Styled Error Page
        return f"""
        <body style="background:#121212; color:white; font-family:sans-serif; text-align:center; padding:50px;">
            <div style="background:#1e1e1e; padding:40px; border-radius:15px; border:1px solid #333; display:inline-block; max-width:500px;">
                <h2 style="color:#ff0033;">⚠️ Conversion Error</h2>
                <p style="color:#ccc; margin:20px 0;">{str(e)}</p>
                <p style="font-size:12px; color:#888;">If this is a 429 error, the server IP is temporarily blocked by YouTube.</p>
                <button onclick="history.back()" style="background:#333; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer;">Try Again</button>
            </div>
        </body>
        """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
