import apiClient from "./axios"

// citationService.ts
export const getCategory = (file: File | null) => {
    const formData = new FormData();
    formData.append('input_file', file as Blob);

    return apiClient.post('/api/v1/citations/get-category', formData, {
        headers: {
            accept: 'application/json',
            'Content-Type': 'multipart/form-data',
        },
    });
};

export const getCategories = () => {
    return apiClient.get('/api/v1/citations/categories', {
        headers: {
            accept: 'application/json',
        },
    });
};


export const charCount = (data: any) =>
    apiClient.post('/api/v1/citations/char-count', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });


export const getCitationSuggestions = (data: FormData) =>
    apiClient.post('/api/v1/citations/get-citation', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });


export const extractContent = (data: any) => apiClient.post('/api/v1/citations/extract-content', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
})
