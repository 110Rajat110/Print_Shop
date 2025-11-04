# Use official Python 3.10 slim image
FROM python:3.10-slim

# Install system dependencies needed for pikepdf and building extensions
RUN apt-get update && apt-get install -y \
    libpoppler-cpp-dev \
    pkg-config \
    python3-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the entire app to the container
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose the port your Flask app will run on
EXPOSE 5000

# Start Gunicorn server, binding to all interfaces on port 5000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000"]
