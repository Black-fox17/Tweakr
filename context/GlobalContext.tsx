"use client"

import React, { createContext, useState, useContext, ReactNode } from "react";

type GlobalStateType = {
    subscriptionType: string;
    amount: number;
    email: string;
    password: string;
    setEmail: (type: string) => void;
    setPassword: (type: string) => void;
    setSubscriptionType: (type: string) => void;
    setAmount: (amount: number) => void;
};

const defaultState: GlobalStateType = {
    subscriptionType: "",
    amount: 0,
    email: "",
    password: "",
    setEmail: () => { },
    setPassword: () => { },
    setSubscriptionType: () => { },
    setAmount: () => { },
};

const GlobalContext = createContext<GlobalStateType>(defaultState);

export const GlobalProvider = ({ children }: { children: ReactNode }) => {
    const [subscriptionType, setSubscriptionType] = useState<string>("");
    const [email, setEmail] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [amount, setAmount] = useState<number>(0);

    return (
        <GlobalContext.Provider
            value={{
                subscriptionType,
                amount,
                email,
                password,
                setEmail,
                setPassword,
                setSubscriptionType,
                setAmount,
            }}
        >
            {children}
        </GlobalContext.Provider>
    );
};

export const useGlobalContext = () => useContext(GlobalContext);

