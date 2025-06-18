'use client'

import React, { useEffect } from 'react'
import { disableScreenCapture } from './disableScreenShot'

const NoScreenshotWrapper = ({ children }: { children: React.ReactNode }) => {
    useEffect(() => {

        disableScreenCapture()

        const preventScreenshot = (e: KeyboardEvent) => {
            if (
                (e.ctrlKey || e.metaKey) &&
                (e.key === 'p' || e.key === 's' || e.key === 'u' || e.key === 'Shift')
            ) {
                e.preventDefault()
                alert('Action not allowed.')
            }
        }

        const blockRightClick = (e: MouseEvent) => e.preventDefault()

        document.addEventListener('contextmenu', blockRightClick)
        document.addEventListener('keydown', preventScreenshot)

        return () => {
            document.removeEventListener('contextmenu', blockRightClick)
            document.removeEventListener('keydown', preventScreenshot)
        }
    }, [])

    return <div>{children}</div>
}

export default NoScreenshotWrapper
