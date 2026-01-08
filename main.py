from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import time
import subprocess

app = Flask(__name__)

# --- THE HTML FRONTEND ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Ultimate Audio Converter</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 40px; background: #1a1a1a; color: #ddd; }
        .container { background: #2d2d2d; padding: 40px; border-radius: 15px; display: inline-block; max-width: 600px; width: 100%; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h2 { color: #fff; margin-bottom: 20px; }
        input { padding: 12px; width: 80%; border-radius: 5px; border: none; background: #444; color: white; margin-bottom: 20px; }
        select { padding: 12px; width: 85%; border-radius: 5px; border: none; background: #444; color: white; margin-bottom: 20px; }
        button { padding: 15px 30px; background: #e62117; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.3s; }
        button:hover { background: #ff3333; }
        .note { font-size: 0.8em; color: #888; margin-top: 15px; }
        optgroup { font-style: normal; font-weight: bold; color: #bbb; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🎵 Ultimate Audio Converter</h2>
        <form action="/convert" method="post">
            <input type="text" name="url" placeholder="Paste YouTube Link Here..." required>
            <br>
            <label>Select Output Format:</label><br>
            <select name="format">
                <optgroup label="Popular / High Quality">
                    <option value="mp3">MP3 - MPEG Layer III (Universal)</option>
                    <option value="m4a">M4A - AAC (Best for Apple/Web)</option>
                    <option value="flac">FLAC - Free Lossless Audio Codec</option>
                    <option value="wav">WAV - Waveform (Uncompressed)</option>
                    <option value="opus">OPUS - (High Efficiency/Streaming)</option>
                </optgroup>

                <optgroup label="Audiophile / Lossless / Professional">
                    <option value="alac">ALAC - Apple Lossless</option>
                    <option value="aiff">AIFF - Apple Uncompressed</option>
                    <option value="ape">APE - Monkey's Audio</option>
                    <option value="wv">WV - WavPack</option>
                    <option value="tta">TTA - True Audio</option>
                    <option value="au">AU - Sun Microsystems</option>
                    <option value="rf64">RF64 - WAV Successor</option>
                </optgroup>

                <optgroup label="Legacy / Specific Use">
                    <option value="wma">WMA - Windows Media Audio</option>
                    <option value="ogg">OGG - Vorbis</option>
                    <option value="mp2">MP2 - MPEG Layer II</option>
                    <option value="mpc">MPC - Musepack</option>
                    <option value="3gp">3GP - Mobile (Low Quality)</option>
                </optgroup>

                <optgroup label="Telephony / Voice (Low Quality)">
                    <option value="amr">AMR - Adaptive Multi-Rate</option>
                    <option value="gsm">GSM - Global System for Mobile</option>
                    <option value="vox">VOX - Dialogic ADPCM</option>
                    <option value="voc">VOC - Creative Voice</option>
                    <option value="8svx">8SVX - Amiga 8-bit</option>
                </optgroup>

                <optgroup label="Raw / Other">
                    <option value="raw">RAW - Raw PCM Data</option>
                    <option value="webm">WEBM - HTML5 Audio</option>
                </optgroup>
            </select>
            <br>
            <button type="submit">Convert & Download</button>
            <p class="note">Note: "Telephony" formats will automatically reduce quality to 8kHz to comply with standards.</p>
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
    
    timestamp = int(time.time())
    # We download as WAV first (Lossless intermediary), then convert to target
    temp_wav = f"/tmp/{timestamp}_temp.wav"
    final_output = f"/tmp/{timestamp}.{fmt}"

    # 1. Download source as WAV (Best intermediary)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'/tmp/{timestamp}_temp.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
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
            # Clean title for filename
            clean_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).strip()

        # Step 2: Convert using FFmpeg with specific flags for formats
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', temp_wav]

        # --- SPECIAL SETTINGS FOR WEIRD FORMATS ---
        if fmt == 'mp3':
            ffmpeg_cmd.extend(['-b:a', '320k']) # Max MP3 quality
        elif fmt == 'aac' or fmt == 'm4a':
            ffmpeg_cmd.extend(['-c:a', 'aac', '-b:a', '256k'])
        elif fmt == 'ogg':
            ffmpeg_cmd.extend(['-c:a', 'libvorbis', '-q:a', '10']) # Max Ogg Quality
        elif fmt == 'opus':
            ffmpeg_cmd.extend(['-c:a', 'libopus', '-b:a', '192k'])
        elif fmt == 'wma':
            ffmpeg_cmd.extend(['-c:a', 'wmav2', '-b:a', '192k'])
        elif fmt == 'amr':
            # AMR requires 8000Hz sample rate
            ffmpeg_cmd.extend(['-ar', '8000', '-ac', '1', '-c:a', 'libopencore_amrnb'])
        elif fmt == 'gsm':
            # GSM requires 8000Hz
            ffmpeg_cmd.extend(['-ar', '8000', '-ac', '1', '-c:a', 'gsm'])
        elif fmt == 'vox':
            # VOX is usually raw adpcm, needs 8000hz
            ffmpeg_cmd.extend(['-f', 'u8', '-c:a', 'pcm_u8', '-ar', '8000', '-ac', '1'])
        elif fmt == 'voc':
            ffmpeg_cmd.extend(['-c:a', 'pcm_u8'])
        elif fmt == '8svx':
            ffmpeg_cmd.extend(['-c:a', 'pcm_s8', '-f', 'iff'])
        elif fmt == 'ape':
            # FFmpeg standard sometimes lacks APE encoder, usually decode only. 
            # We try standard link; if fails, error handler catches it.
            pass 
        elif fmt == 'rf64':
             ffmpeg_cmd.extend(['-f', 'rf64'])
        
        # Add output file
        ffmpeg_cmd.append(final_output)

        # Run conversion
        subprocess.run(ffmpeg_cmd, check=True)

        # Step 3: Send to user
        return send_file(
            final_output, 
            as_attachment=True, 
            download_name=f"{clean_title}.{fmt}"
        )

    except Exception as e:
        return f"""
        <h3>Conversion Failed</h3>
        <p><b>Reason:</b> {str(e)}</p>
        <p>If you selected a very old format (like 8SVX or AMR), the free server might not have the specific library installed. Try MP3, M4A, FLAC, or WAV.</p>
        <button onclick="history.back()">Go Back</button>
        """
