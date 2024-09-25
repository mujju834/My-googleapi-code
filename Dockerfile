# Use an official Python runtime as a base image
FROM python:3.9-slim

# Install necessary system dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire project folder into the container at /app
COPY . /app

# Ensure Google Cloud credentials keyfile.json is accessible (replace with your file's name)
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/shahalkeyfile.json"

# Expose the port on which the app will run
EXPOSE 8080

# Collect static files (optional, depending on how you handle static assets)
# RUN python manage.py collectstatic --noinput

# Run Django migrations
RUN python manage.py migrate

# Use Gunicorn as the WSGI server for production
CMD exec gunicorn --bind :$PORT voice_assistant.wsgi:application --workers 1 --threads 8
