# Use official Python image as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends sqlite3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for webhook
EXPOSE 8080

# Create directory for SQLite file
RUN mkdir -p /app/data

# Set environment variables
ENV DB_PATH=/app/data/db.sqlite3

# Command to run the bot
CMD ["python3", "-m", "app.main"]
