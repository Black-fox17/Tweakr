import apiClient from './axios';

export const verifySubscriptionPayment = async (id: string) => {
    return await apiClient.post(`/api/v1/subscription/verify-payment/${id}`);
}

export const verifyAllPayment = async (id: number) => {
    return await apiClient.get(`/api/v1/subscription/verify-payment-sync/${id}`);
}
export const createSubscription = async (data: any) => {
    return await apiClient.post('/api/v1/subscription/subscriptions', data);
};

export const updateSubscription = async (id: string, data: any) => {
    return await apiClient.patch(`/api/v1/subscription/subscriptions/${id}`, data);
};

export const getSingleSubscription = async (id: string) => {
    return await apiClient.get(`/api/v1/subscription/user_subscribed/${id}`);
};

export const getUserSubscriptions = async () => {
    return await apiClient.get('/api/v1/subscription/subscriptions/user');
};
