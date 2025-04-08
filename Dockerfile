FROM python:3.12-slim

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create .streamlit directory if it doesn't exist
RUN mkdir -p .streamlit

# Set environment variables
ENV PYTHONPATH=/code:/code/datapipeline:/code/app
ENV PORT=5000

# Expose the port
EXPOSE 5000

# Command to run the application
CMD ["streamlit", "run", "app/main.py", "--server.port=5000", "--server.address=0.0.0.0"] 