# Use official Python image
FROM python:3.10-slim

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all your project files
COPY . .

# Expose port
EXPOSE 8080

# Start your app using gunicorn
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8080", "backend:app"]
