FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \ 
    ffmpeg \ 
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py config.py utils.py ./

# Create recordings directory
RUN mkdir -p /app/recordings

# Run the bot
CMD ["python", "bot.py"]