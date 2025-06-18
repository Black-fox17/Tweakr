import axios from 'axios'

export const getAllFaqs = () => axios.get('/api/v1/faq')
export const createFaq = (data: any) => axios.post('/api/v1/faq', data)
