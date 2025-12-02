import os
import time
from faster_whisper import WhisperModel
import logging
from flask import Flask, render_template, request, send_file, after_this_request
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'flac', 'mp4', 'mkv', 'mov', 'm4a', 'ogg', 'webm'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Point to the folder we created in the Dockerfile
model_path = "/app/whisper_model" 

model = WhisperModel(model_path, device="cpu", compute_type="int8")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def transcribe_with_whisper(input_file, output_dir, language):
    # Perform transcription
    transcribe_start = time.time()
    # faster-whisper returns a generator of segments and info
    segments, info = model.transcribe(
        input_file,
        language=language,
        word_timestamps=True
    )
    # Convert generator to list to allow iteration
    segments = list(segments)
    transcribe_duration = time.time() - transcribe_start
    app.logger.info(f"[PROFILING] Transcribing file took: {transcribe_duration:.2f} seconds")
    app.logger.info(f"[PROFILING] Detected language: {info.language} with probability {info.language_probability:.2f}")
    
    # Save to an SRT file
    srt_filename = "output.srt"
    srt_file = os.path.join(output_dir, srt_filename)
    
    srt_save_start = time.time()
    with open(srt_file, "w", encoding="utf-8") as f:
        for idx, segment in enumerate(segments):
            # faster-whisper uses attributes instead of dictionary keys
            start_time = segment.start
            end_time = segment.end
            text = segment.text
            
            # Convert start and end times to SRT time format (HH:MM:SS,MS)
            start_time_srt = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02},{int((start_time * 1000) % 1000):03}"
            end_time_srt = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02},{int((end_time * 1000) % 1000):03}"
            
            # Write the segment to the SRT file
            f.write(f"{idx + 1}\n")
            f.write(f"{start_time_srt} --> {end_time_srt}\n")
            f.write(f"{text}\n\n")
    srt_save_duration = time.time() - srt_save_start
    app.logger.info(f"[PROFILING] Saving to SRT file took: {srt_save_duration:.2f} seconds")
    
    return srt_file

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    if not allowed_file(file.filename):
        return 'Invalid file type. Allowed types: ' + ', '.join(app.config['ALLOWED_EXTENSIONS']), 400
        
    language = request.form.get('language', 'en')
    
    if file:
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save uploaded file
        save_start = time.time()
        file.save(input_path)
        save_duration = time.time() - save_start
        app.logger.info(f"[PROFILING] Saving uploaded file took: {save_duration:.2f} seconds")
        
        try:
            srt_path = transcribe_with_whisper(input_path, app.config['OUTPUT_FOLDER'], language)
            
            @after_this_request
            def remove_files(response):
                try:
                    remove_start = time.time()
                    os.remove(input_path)
                    os.remove(srt_path)
                    remove_duration = time.time() - remove_start
                    app.logger.info(f"[PROFILING] Removing files took: {remove_duration:.2f} seconds")
                except Exception as e:
                    app.logger.error(f"Error removing files: {e}")
                return response
                
            return send_file(srt_path, as_attachment=True, download_name=f"{os.path.splitext(filename)[0]}.srt")
            
        except Exception as e:
            return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
