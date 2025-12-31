import os
import io
import wave
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from steg_engine import StegEngine

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB Max upload for MVP

# Ensure strict boolean
def is_safe_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'wav', 'png', 'jpg', 'txt', 'pdf', 'zip'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    try:
        if 'audio_file' not in request.files:
            flash("No audio file uploaded", "error")
            return redirect(url_for('index'))
            
        audio_file = request.files['audio_file']
        password = request.form.get('password')
        payload_type = request.form.get('payload_type') # 'text' or 'file'
        
        if not audio_file or not password:
            flash("Missing audio or password", "error")
            return redirect(url_for('index'))
            
        if not audio_file.filename.lower().endswith('.wav'):
             flash("Only .WAV files are supported", "error")
             return redirect(url_for('index'))

        # Process Audio
        # We read it into memory. 
        try:
            # We need to read frames using wave module, but file storage is stream.
            # Convert to BytesIO
            audio_io = io.BytesIO(audio_file.read())
            with wave.open(audio_io, 'rb') as w:
                 params = w.getparams()
                 frames = w.readframes(w.getnframes())
        except wave.Error:
             flash("Invalid WAV file", "error")
             return redirect(url_for('index'))

        # Prepare Payload
        secret_payload = b""
        filename_str = "None"
        
        if payload_type == 'text':
            text = request.form.get('text_payload', '')
            if not text:
                flash("No text provided", "error")
                return redirect(url_for('index'))
            secret_payload = text.encode('utf-8')
            msg_type = "TEXT"
            
        elif payload_type == 'file':
            if 'file_payload' not in request.files:
                flash("No secret file uploaded", "error")
                return redirect(url_for('index'))
            f_payload = request.files['file_payload']
            if not f_payload.filename:
                 flash("No file selected", "error")
                 return redirect(url_for('index'))
                 
            secret_payload = f_payload.read()
            filename_str = f_payload.filename
            msg_type = "FILE"
        else:
            flash("Invalid payload type", "error")
            return redirect(url_for('index'))
            
        # Combine for protocol
        # Protocol: TYPE|||FILENAME|||DATA
        # We construct this binary blob
        full_secret = msg_type.encode('utf-8') + b'|||' + filename_str.encode('utf-8') + b'|||' + secret_payload
        
        # Embed
        engine = StegEngine()
        try:
            modified_frames = engine.embed(frames, params, full_secret, password)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for('index'))

        # Write to Output WAV
        output_io = io.BytesIO()
        with wave.open(output_io, 'wb') as w_out:
            w_out.setparams(params)
            w_out.writeframes(modified_frames)
            
        output_io.seek(0)
        
        return send_file(
            output_io,
            mimetype="audio/wav",
            as_attachment=True,
            download_name=f"encoded_{audio_file.filename}"
        )

    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/decode', methods=['POST'])
def decode():
    try:
        if 'audio_file' not in request.files:
            flash("No audio file uploaded", "error")
            return redirect(url_for('index'))
            
        audio_file = request.files['audio_file']
        password = request.form.get('password')
        
        if not audio_file or not password:
             flash("Missing audio or password", "error")
             return redirect(url_for('index'))
             
        # Read Frames
        try:
            audio_io = io.BytesIO(audio_file.read())
            with wave.open(audio_io, 'rb') as w:
                 frames = w.readframes(w.getnframes())
        except wave.Error:
             flash("Invalid WAV file", "error")
             return redirect(url_for('index'))
             
        # Extract
        engine = StegEngine()
        try:
            msg_type, filename, data = engine.extract(frames, password)
        except Exception as e:
            # Often encryption errors or basic decoding errors
            flash(f"Extraction failed. Wrong password or corrupted file? Error: {str(e)}", "error")
            return redirect(url_for('index'))
            
        if msg_type == "TEXT":
            # For text, we can render a success page or just flash it?
            # User requirement: "If the result is text, render a 'Success' page showing the text."
            # We'll just render index with a special variable.
            decoded_text = data.decode('utf-8')
            return render_template('index.html', decoded_text=decoded_text)
            
        elif msg_type == "FILE":
            # Return download
            file_io = io.BytesIO(data)
            return send_file(
                file_io,
                as_attachment=True,
                download_name=filename
            )
        else:
             flash("Unknown message type extracted.", "error")
             return redirect(url_for('index'))

    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
