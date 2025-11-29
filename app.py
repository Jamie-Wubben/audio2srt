import os
import whisper
from flask import Flask, render_template, request, send_file, after_this_request
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'flac', 'mp4', 'mkv', 'mov', 'm4a', 'ogg', 'webm'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Load the model globally to avoid reloading it on every request
# Using 'base' model as per plan to ensure it runs on typical hardware
model = whisper.load_model("base")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def transcribe_with_whisper(input_file, output_dir, language):
    # Perform transcription
    result = model.transcribe(
        input_file,
        language=language,
        word_timestamps=True,
    )
    
    # Extract the transcription text and word timestamps
    segments = result["segments"]
    
    # Save to an SRT file
    srt_filename = "output.srt"
    srt_file = os.path.join(output_dir, srt_filename)
    
    with open(srt_file, "w", encoding="utf-8") as f:
        for idx, segment in enumerate(segments):
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"]
            
            # Convert start and end times to SRT time format (HH:MM:SS,MS)
            start_time_srt = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02},{int((start_time * 1000) % 1000):03}"
            end_time_srt = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02},{int((end_time * 1000) % 1000):03}"
            
            # Write the segment to the SRT file
            f.write(f"{idx + 1}\n")
            f.write(f"{start_time_srt} --> {end_time_srt}\n")
            f.write(f"{text}\n\n")
    
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
        file.save(input_path)
        
        try:
            srt_path = transcribe_with_whisper(input_path, app.config['OUTPUT_FOLDER'], language)
            
            @after_this_request
            def remove_files(response):
                try:
                    os.remove(input_path)
                    os.remove(srt_path)
                except Exception as e:
                    app.logger.error(f"Error removing files: {e}")
                return response
                
            return send_file(srt_path, as_attachment=True, download_name=f"{os.path.splitext(filename)[0]}.srt")
            
        except Exception as e:
            return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
