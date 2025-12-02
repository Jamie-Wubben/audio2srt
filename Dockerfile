FROM python:3.9.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download the model
COPY download_model.py .
RUN python download_model.py

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 8080

# Run the application
# bind: listen on PORT (google set's it)
# workers: 1 (Important to prevent Out of Memory with AI models)
# threads: 8 (Allows concurrent request handling)
# timeout: 0 (Prevents Gunicorn from killing long transcriptions)
# app:app -> This assumes your file is named 'app.py' and your Flask instance is named 'app'
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 0 "app:app"
