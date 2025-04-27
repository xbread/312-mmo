# Use official Python image
FROM python:3.8

# Set working directory inside container
WORKDIR /app

# Copy only necessary files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start the app
CMD ["python", "app.py"]
