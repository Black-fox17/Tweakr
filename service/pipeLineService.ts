import axios from 'axios'

export const processPaperPipeline = (data: any) => axios.post('/datapipeline/api/papers/process', data)
export const getJobStatus = (jobId: string) => axios.get(`/datapipeline/api/papers/jobs/${jobId}`)
export const getJobLogs = (jobId: string) => axios.get(`/datapipeline/api/papers/jobs/${jobId}/logs`)
export const getJobStats = (jobId: string) => axios.get(`/datapipeline/api/papers/jobs/${jobId}/stats`)
export const getAvailableSources = () => axios.get('/datapipeline/api/papers/sources')
