from faster_whisper import download_model
import shutil
import os

print("Downloading model...")
# Download the model to a temporary path
downloaded_path = download_model("Systran/faster-whisper-base")

# Define where we want the model to live permanently in the image
final_model_path = "/app/whisper_model"

# Move the specific model snapshot to our fixed path
# This removes the complex "models--Systran..." folder structure
if os.path.exists(final_model_path):
    shutil.rmtree(final_model_path)
    
shutil.copytree(downloaded_path, final_model_path)

print(f"Model successfully moved to: {final_model_path}")