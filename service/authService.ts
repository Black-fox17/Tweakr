import apiClient from "./axios";

export const register = (data: any) =>
    apiClient.post("/api/v1/auth/register", data, {
        headers: {
            'Content-Type': ' application/json',
        },
    });

export const login = (data: any) =>
    apiClient.post("/api/v1/auth/login", data);

export const logout = () =>
    apiClient.post("/api/v1/auth/logout");

export const loginWithGoogle = (data: any) =>
    apiClient.post("/api/v1/auth/google", data);

export const googleCallback = () =>
    apiClient.get("/api/v1/auth/callback/google");
