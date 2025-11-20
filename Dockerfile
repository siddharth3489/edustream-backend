# Use Python 3.10
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy everything
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run flask server
CMD ["python", "app.py"]
