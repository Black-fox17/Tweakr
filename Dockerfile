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

# Create .streamlit directory
RUN mkdir -p .streamlit

# Copy Streamlit config first
COPY .streamlit/config.toml .streamlit/

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/code:/code/datapipeline:/code/app
ENV PORT=5000
ENV STREAMLIT_SERVER_PORT=5000
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Expose the port
EXPOSE 5000

# Command to run the application
CMD ["python", "health_check.py"] 