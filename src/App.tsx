import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Database, 
  Search, 
  Settings, 
  Clock, 
  CheckCircle,
  AlertCircle,
  Archive,
  FileText,
  Server
} from 'lucide-react';
import axios from 'axios';
import academic from '../academic.svg';

// API base URL - update this to your FastAPI server address
const API_BASE_URL = 'https://tweakr.onrender.com/datapipeline';

// Types
interface Log {
  timestamp: string;
  message: string;
  type: 'error' | 'processing' | 'existing' | 'success' | 'info';
}

interface ProcessingStats {
  papersProcessed: number;
  totalSources: number;
  progress: number;
  batchSize: number;
  elapsedTime: number;
  isProcessing: boolean;
}

interface SearchDetails {
  query: string;
  category: string;
  downloadDir: string;
}

function App() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState<Log[]>([]);
  const [stats, setStats] = useState<ProcessingStats>({
    papersProcessed: 0,
    totalSources: 0,
    progress: 0,
    batchSize: 20,
    elapsedTime: 0,
    isProcessing: false
  });
  const [searchDetails, setSearchDetails] = useState<SearchDetails>({
    query: '',
    category: '',
    downloadDir: './store'
  });
  const [selectedSources, setSelectedSources] = useState(['arxiv', 'elsevier', 'springer']);
  const [availableSources, setAvailableSources] = useState<string[]>([]);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load available sources when component mounts
  useEffect(() => {
    fetchAvailableSources();
  }, []);

  // Fetch available sources from the API
  const fetchAvailableSources = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/papers/sources`);
      setAvailableSources(response.data);
      setSelectedSources(response.data);
    } catch (err) {
      console.error('Error fetching available sources:', err);
      setError('Failed to connect to API server. Please check if the server is running.');
    }
  };

  // Start processing papers
  const startProcessing = async () => {
    if (!searchDetails.query || !searchDetails.category) {
      setError('Query and category are required');
      return;
    }

    try {
      setIsProcessing(true);
      setError(null);
      setLogs([]);
      setStats(prev => ({ 
        ...prev, 
        progress: 0, 
        papersProcessed: 0, 
        elapsedTime: 0,
        isProcessing: true 
      }));

      // Make API request to start processing
      const response = await axios.post(`${API_BASE_URL}/api/papers/process`, {
        query: searchDetails.query,
        category: searchDetails.category,
        batch_size: stats.batchSize,
        download_dir: searchDetails.downloadDir,
        sources: selectedSources
      });

      const jobId = response.data.job_id;
      setCurrentJobId(jobId);

      // Start polling for updates
      pollJobUpdates(jobId);
    } catch (err) {
      console.error('Error starting processing:', err);
      setIsProcessing(false);
      setError('Failed to start processing. Please check the server logs.');
    }
  };

  // Poll for job updates
  const pollJobUpdates = (jobId: string) => {
    const statsInterval = setInterval(async () => {
      try {
        // Get job status
        const statusResponse = await axios.get(`${API_BASE_URL}/api/papers/jobs/${jobId}`);
        const { status } = statusResponse.data;

        // Get job stats
        const statsResponse = await axios.get(`${API_BASE_URL}/api/papers/jobs/${jobId}/stats`);
        setStats(statsResponse.data);

        // Get job logs
        const logsResponse = await axios.get(`${API_BASE_URL}/api/papers/jobs/${jobId}/logs`);
        setLogs(logsResponse.data);

        // If job is completed or failed, stop polling
        if (status === 'completed' || status === 'failed') {
          clearInterval(statsInterval);
          setIsProcessing(false);
        }
      } catch (err) {
        console.error('Error polling job updates:', err);
        clearInterval(statsInterval);
        setIsProcessing(false);
        setError('Lost connection to the job. Please check server logs.');
      }
    }, 1000);

    // Clean up interval on component unmount
    return () => clearInterval(statsInterval);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img src={academic} alt="Academic" className="h-8 w-8" />
            <h1 className="text-2xl font-bold text-gray-900">Academic Paper Processing Pipeline</h1>
          </div>
          <div className="text-sm text-gray-500">© 2025</div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        <div className="grid grid-cols-12 gap-6">
          {/* Sidebar */}
          <div className="col-span-3">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center space-x-2 mb-6">
                <Settings className="h-5 w-5 text-gray-500" />
                <h2 className="text-lg font-semibold">Configuration</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Search Query</label>
                  <input
                    type="text"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    value={searchDetails.query}
                    onChange={(e) => setSearchDetails(prev => ({ ...prev, query: e.target.value }))}
                    placeholder="artificial intelligence AND healthcare"
                    disabled={isProcessing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Category</label>
                  <input
                    type="text"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    value={searchDetails.category}
                    onChange={(e) => setSearchDetails(prev => ({ ...prev, category: e.target.value }))}
                    placeholder="healthcare_ai"
                    disabled={isProcessing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Batch Size</label>
                  <input
                    type="number"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    value={stats.batchSize}
                    onChange={(e) => setStats(prev => ({ ...prev, batchSize: parseInt(e.target.value) || 20 }))}
                    min="1"
                    max="100"
                    disabled={isProcessing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Sources</label>
                  <div className="mt-2 space-y-2">
                    {availableSources.map(source => (
                      <label key={source} className="flex items-center">
                        <input
                          type="checkbox"
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          checked={selectedSources.includes(source)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedSources(prev => [...prev, source]);
                            } else {
                              setSelectedSources(prev => prev.filter(s => s !== source));
                            }
                          }}
                          disabled={isProcessing}
                        />
                        <span className="ml-2 text-sm text-gray-600 capitalize">{source}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <button
                  onClick={startProcessing}
                  disabled={isProcessing || !searchDetails.query || !searchDetails.category}
                  className={`w-full py-2 px-4 rounded-md text-white font-medium ${
                    isProcessing || !searchDetails.query || !searchDetails.category
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                >
                  {isProcessing ? 'Processing...' : 'Start Processing'}
                </button>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="col-span-9 space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-gray-500">Papers Processed</div>
                  <FileText className="h-5 w-5 text-blue-500" />
                </div>
                <div className="mt-2 text-3xl font-semibold text-gray-900">{stats.papersProcessed}</div>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-gray-500">Sources</div>
                  <Server className="h-5 w-5 text-green-500" />
                </div>
                <div className="mt-2 text-3xl font-semibold text-gray-900">{selectedSources.length}</div>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-gray-500">Progress</div>
                  <Archive className="h-5 w-5 text-purple-500" />
                </div>
                <div className="mt-2 text-3xl font-semibold text-gray-900">
                  {Math.round(stats.progress * 100)}%
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-gray-500">Elapsed Time</div>
                  <Clock className="h-5 w-5 text-orange-500" />
                </div>
                <div className="mt-2 text-3xl font-semibold text-gray-900">{stats.elapsedTime}s</div>
              </div>
            </div>

            {/* Progress Bar */}
            {isProcessing && (
              <div className="bg-white rounded-lg shadow p-4">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                    style={{ width: `${stats.progress * 100}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Logs */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Processing Logs</h2>
              </div>
              <div className="p-4 h-[400px] overflow-y-auto font-mono text-sm">
                {logs.map((log, index) => (
                  <div
                    key={index}
                    className={`py-1 flex items-start space-x-2 ${
                      log.type === 'error' ? 'text-red-600' :
                      log.type === 'processing' ? 'text-green-600' :
                      log.type === 'existing' ? 'text-orange-600' :
                      log.type === 'success' ? 'text-blue-600' :
                      'text-gray-600'
                    }`}
                  >
                    <span className="text-gray-400">[{log.timestamp}]</span>
                    <span>{log.message}</span>
                  </div>
                ))}
                {logs.length === 0 && (
                  <div className="text-gray-500 italic">No logs available. Start processing to see updates.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;