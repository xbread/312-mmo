# Use official Python image
FROM python:alpine

# Set working directory inside container
WORKDIR /app

# Copy only necessary files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose Flask default port
EXPOSE 8080

# Start the app
CMD ["python", "app.py"]
