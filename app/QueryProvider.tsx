'use client'
import React from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from '@/lib/queyClient'

export default function QueryProvider({
    children,
}: {
    children: React.ReactNode
}) {

    return (
        <QueryClientProvider client={queryClient} >
            {children}
            < ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
    )
}
