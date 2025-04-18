import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI
import uvicorn
from datapipeline.core.pipeline_manager import PipelineManager

# Create logs directory if it doesn't exist
os.makedirs('/code/logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/code/logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create FastAPI app
app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'MONGODB_ATLAS_CLUSTER_URI',
        'MONGO_DB_NAME',
        'GOOGLE_GEMINI_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True

def run_pipeline():
    """Run the pipeline in a separate thread."""
    try:
        # Initialize pipeline manager
        manager = PipelineManager()
        
        # Run initial pipeline
        logging.info("Running initial pipeline")
        manager.run_automated_pipeline(force_update=True)
        
        # Schedule regular runs
        logging.info("Starting scheduled pipeline runs")
        manager.schedule_pipeline(interval_hours=24)
    except Exception as e:
        logging.error(f"Error in pipeline: {e}")

def main():
    try:
        # Check environment variables
        if not check_environment():
            sys.exit(1)
            
        logging.info("Starting Pipeline Manager Service")
        logging.info(f"MongoDB URI: {os.getenv('MONGODB_ATLAS_CLUSTER_URI')[:20]}... (truncated)")
        logging.info(f"MongoDB Database: {os.getenv('MONGO_DB_NAME')}")
        
        # Start the pipeline in a separate thread
        import threading
        pipeline_thread = threading.Thread(target=run_pipeline)
        pipeline_thread.daemon = True
        pipeline_thread.start()
        
        # Start the FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8080)
        
    except KeyboardInterrupt:
        logging.info("Pipeline service stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error in pipeline service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 