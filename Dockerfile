# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set system environments to prevent output buffering and cache generation
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Set the working directory in the container
WORKDIR /app

# Install basic compiler build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependencies file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the workspace code
COPY . .

# Expose the Streamlit default port
EXPOSE 8501

# Run the streamlit application on deployment
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
