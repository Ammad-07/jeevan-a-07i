# Use an official Python image
FROM python:3.10-slim

# Install required system libraries (including OpenCV dependencies)
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Railway expects this)
EXPOSE 8080

# Start your app with Gunicorn
CMD ["gunicorn", "backend:app", "--bind", "0.0.0.0:8080"]
