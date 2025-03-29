import streamlit as st
import pandas as pd
import time
from datetime import datetime
import os
import threading
import queue
import random   
from datapipeline.main import PapersPipeline
from streamlit_autorefresh import st_autorefresh
from datapipeline.core.constants import MONGO_DB_NAME, MONGODB_ATLAS_CLUSTER_URI
from dotenv import load_dotenv
import sys
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a mock class for testing if needed
# class MockPapersPipeline:
#     def __init__(self, mongo_uri, mongo_db_name):
#         self.mongo_uri = mongo_uri
#         self.mongo_db_name = mongo_db_name
        
#     def process_papers(self, query, category, batch_size=100, download_dir='./store', sources=None):
#         if sources is None:
#             sources = ["arxiv", "elsevier", "springer"]
        
#         # This is just for demonstration, replace with actual implementation when integrated
#         for source in sources:
#             time.sleep(1)  # Simulate processing time
#             st.session_state.log_queue.put(f"Processing papers for query: {query} from source: {source}")
            
#             # Simulate processing multiple papers
#             for i in range(3):
#                 paper_title = f"Sample {source.capitalize()} Paper {i+1} about {query}"
#                 time.sleep(0.5)
#                 st.session_state.log_queue.put(f"Processing paper: {paper_title}")
#                 time.sleep(0.5)
#                 st.session_state.log_queue.put(f"Extracting keywords for: {paper_title}")
#                 time.sleep(0.8)
                
#                 # Randomly decide if paper exists
#                 if random.choice([True, False]):
#                     st.session_state.log_queue.put(f"Paper '{paper_title}' already exists in MongoDB. Updating metadata...")
#                 else:
#                     st.session_state.log_queue.put(f"Paper '{paper_title}' does not exist in MongoDB. Storing new document...")
#                     st.session_state.log_queue.put(f"Document stored in MongoDB collection '{category}'.")
                
#                 # Update progress
#                 st.session_state.papers_processed += 1
#                 if st.session_state.total_papers > 0:
#                     st.session_state.progress = st.session_state.papers_processed / st.session_state.total_papers
                
#         st.session_state.log_queue.put("Processing completed!")
#         st.session_state.is_processing = False


def init_session_state():
    """Initialize session state variables"""
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'log_queue' not in st.session_state:
        st.session_state.log_queue = queue.Queue()
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    if 'progress' not in st.session_state:
        st.session_state.progress = 0.0
    if 'papers_processed' not in st.session_state:
        st.session_state.papers_processed = 0
    if 'total_papers' not in st.session_state:
        st.session_state.total_papers = 0
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None


def process_papers_thread(pipeline, query, category, batch_size, download_dir, sources):
    """Run the paper processing in a separate thread"""
    try:
        st.session_state.start_time = time.time()
        st.session_state.is_processing = True
        st.session_state.papers_processed = 0
        
        # Estimate total papers (this would be more accurate in real implementation)
        st.session_state.total_papers = batch_size * len(sources) * 3
        
        # Run the actual processing
        pipeline.process_papers(
            query=query,
            category=category,
            batch_size=batch_size,
            download_dir=download_dir,
            sources=sources
        )
    except Exception as e:
        st.session_state.log_queue.put(f"Error during processing: {str(e)}")
    finally:
        st.session_state.is_processing = False


def main():
    # Initialize session state
    init_session_state()
    
    # Set up autorefresh to update logs (only when processing)
    if st.session_state.is_processing:
        st_autorefresh(interval=1000, key="autorefresh")
    
    # Check for new log messages
    while not st.session_state.log_queue.empty():
        log_message = st.session_state.log_queue.get()
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.logs.append(f"[{timestamp}] {log_message}")
    
    # Set page config and title
    st.set_page_config(
        page_title="Academic Paper Processor",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-bottom: 1rem;
    }
    .log-container {
        background-color: #F5F5F5;
        border-radius: 10px;
        padding: 15px;
        height: 400px;
        overflow-y: auto;
        font-family: monospace;
        margin-top: 10px;
    }
    .log-entry {
        margin: 3px 0;
        padding: 3px 0;
        border-bottom: 1px solid #EEEEEE;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        color: #757575;
    }
    .paper-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .metrics-container {
        display: flex;
        justify-content: space-between;
        margin: 20px 0;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        flex: 1;
        margin: 0 10px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .metric-label {
        color: #757575;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display header
    st.markdown('<h1 class="main-header">📚 Academic Paper Processing Pipeline</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Search, download, and process academic papers from various sources</p>', 
                unsafe_allow_html=True)
    
    # Create sidebar for inputs
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=Papers+API", width=150)
        st.markdown("### ⚙️ Configuration")
        
        # MongoDB configuration (in real app, you might want to hide these)
        # mongo_uri = st.text_input("MongoDB URI", value="mongodb://localhost:27017", type="password")
        # mongo_db_name = st.text_input("MongoDB Database Name", value="papers_db")
        
        st.markdown("### 🔍 Search Parameters")
        query = st.text_input("Search Query", value="artificial intelligence AND healthcare")
        category = st.text_input("Category", value="healthcare_ai")
        
        batch_size = st.slider("Batch Size", min_value=5, max_value=200, value=20, step=5)
        download_dir = st.text_input("Download Directory", value="./store")
        
        source_options = ["arxiv", "elsevier", "springer"]
        selected_sources = st.multiselect("Select Sources", source_options, default=source_options)
        
        st.markdown("### 🚀 Actions")
        start_button = st.button("Start Processing", type="primary", disabled=st.session_state.is_processing)
        
        if start_button:
            # Create pipeline
            try:
                # In production, use your actual pipeline:
                pipeline = PapersPipeline(
                    mongo_uri=MONGODB_ATLAS_CLUSTER_URI,
                    mongo_db_name=MONGO_DB_NAME,
                )
                
                # Clear previous logs
                st.session_state.logs = []
                
                # Start processing in a separate thread
                processing_thread = threading.Thread(
                    target=process_papers_thread,
                    args=(pipeline, query, category, batch_size, download_dir, selected_sources)
                )
                processing_thread.daemon = True
                processing_thread.start()
                
                st.session_state.log_queue.put(f"Starting paper processing for query: {query}")
                st.session_state.log_queue.put(f"Using sources: {', '.join(selected_sources)}")
                
            except Exception as e:
                st.error(f"Failed to start processing: {str(e)}")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h2 class="subheader">📋 Processing Log</h2>', unsafe_allow_html=True)
        
        # Progress indicator
        if st.session_state.is_processing:
            st.progress(st.session_state.progress)
            elapsed = time.time() - (st.session_state.start_time or time.time())
            st.write(f"⏱️ Processing... (Elapsed time: {elapsed:.1f} seconds)")
        elif st.session_state.papers_processed > 0:
            st.success(f"✅ Processing completed! Processed {st.session_state.papers_processed} papers.")
        
        # Display logs in a scrollable container
        log_html = '<div class="log-container">'
        for log in st.session_state.logs:
            # Highlight specific log types with different colors
            if "Error" in log:
                color = "#F44336"  # Red for errors
            elif "Processing paper" in log:
                color = "#4CAF50"  # Green for processing papers
            elif "already exists" in log:
                color = "#FF9800"  # Orange for existing papers
            elif "stored in MongoDB" in log:
                color = "#2196F3"  # Blue for successful storage
            else:
                color = "#000000"  # Default black
                
            log_html += f'<div class="log-entry" style="color: {color}">{log}</div>'
        log_html += '</div>'
        
        st.markdown(log_html, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<h2 class="subheader">📊 Processing Stats</h2>', unsafe_allow_html=True)
        
        # Display metrics
        html_metrics = """
        <div class="metrics-container">
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Papers Processed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Sources</div>
            </div>
        </div>
        <div class="metrics-container">
            <div class="metric-card">
                <div class="metric-value">{:.1f}%</div>
                <div class="metric-label">Progress</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Batch Size</div>
            </div>
        </div>
        """.format(
            st.session_state.papers_processed,
            len(selected_sources) if 'selected_sources' in locals() else 0,
            st.session_state.progress * 100,
            batch_size if 'batch_size' in locals() else 0
        )
        
        st.markdown(html_metrics, unsafe_allow_html=True)
        
        # Display search details
        if 'query' in locals() and query:
            st.markdown('<h3 style="margin-top: 20px;">🔍 Search Details</h3>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="paper-card">
                    <strong>Query:</strong> {query}<br>
                    <strong>Category:</strong> {category if 'category' in locals() else ''}<br>
                    <strong>Download Directory:</strong> {download_dir if 'download_dir' in locals() else './store'}<br>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Footer
    st.markdown(
        '<div class="footer">Academic Paper Processing Pipeline © 2025</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()