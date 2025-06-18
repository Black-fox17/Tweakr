import React from 'react';


const CitationIsReadyModal = () => {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="relative flex w-[90%] max-w-[811px] flex-col gap-4 rounded-lg bg-white p-6 shadow-lg">
                <div className='h-[87px] w-full'>
                    <img src="/gif/Animation - success.gif" alt="gif" className='size-full' />
                </div>
                <p className='text-center text-[20px] font-medium text-[#545454]'>
                    Your Citations, Ready for Inspection
                </p>
            </div>
        </div>
    );
};

export default CitationIsReadyModal;
