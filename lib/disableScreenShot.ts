export const disableScreenCapture = () => {
    if (
        'mediaDevices' in navigator &&
        'getDisplayMedia' in navigator.mediaDevices
    ) {
        navigator.mediaDevices.getDisplayMedia = () => {
            alert("Screen capture is not permitted.");
            return Promise.reject("Screen capture is disabled.");
        };
    }
};
