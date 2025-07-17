# Use an official Python runtime as the base image
FROM python:3-slim

# Set the working directory in the container
WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY .env .env

# Copy the rest of the application code
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production

# Expose the port your app runs on
EXPOSE 5000

# Command to run the app (use gunicorn for production)
CMD [ "flask", "run", "--host=0.0.0.0", "--port=5000" ]
# For production, consider using gunicorn:
# CMD [ "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.app:app" ]

# Recommendation: create a .dockerignore file to exclude files like __pycache__, .git, etc.    