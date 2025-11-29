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
# Note: Installing torch 1.10.1 specifically for CPU to keep image size reasonable if possible, 
# but standard pip install torch==1.10.1 might pull CUDA version. 
# For simplicity and to match user request exactly, we just run pip install.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]

