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
CMD ["python", "-u", "app.py"]

