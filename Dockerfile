FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy only the requirements.txt first to optimize caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/app

# Expose the port for Flask
EXPOSE 5000

# Run the Flask app
CMD ["python", "server/app.py"]
