FROM python:3.10-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install WebSocket support for uvicorn
RUN pip install --no-cache-dir 'uvicorn[standard]' websockets

# Copy the backend code
COPY backend/ /app/backend/

# Make sure Python can find modules in the app directory
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
