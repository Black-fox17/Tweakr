import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

type FileUploaderProps = {
    files: File[] | undefined,
    onChange: (files: File[]) => void,
    isPending?: boolean
}



const FileUploader = ({ files, onChange, isPending }: FileUploaderProps) => {
    const onDrop = useCallback((acceptedFiles: File[]) => {
        // Do something with the files
        onChange(acceptedFiles)
    }, [onChange])
    const { getRootProps, getInputProps } = useDropzone({ onDrop })



    return (
        <div {...getRootProps()}>
            <input {...getInputProps()} />
            {files && files?.length > 0 || isPending ? (
                <div className='flex w-auto flex-col items-center justify-center gap-8 sm:w-[798px]'>
                    <h3 className='text-center text-[24px] font-semibold'>Let&apos;s Transform Your Document</h3>
                    <div className='flex size-auto items-center justify-center gap-6 rounded-3xl border border-[#D8D8D8] bg-[#FDFDFD] p-12 sm:h-[309px] sm:w-[508px]'>
                        <img src="/gif/Docs animation gif.gif" alt="aniamtion" className=' object-contain' />
                    </div>
                </div>
            ) : (
                <div className='flex w-full flex-col items-center justify-center gap-8 sm:w-[798px]'>
                    <h3 className='text-center text-[24px] font-semibold'>Let&apos;s Transform Your Document</h3>
                    <div className='flex flex-col items-center gap-6 rounded-3xl border border-[#D8D8D8] bg-[#FDFDFD] p-12 sm:p-4'>
                        <div className='flex w-full flex-col items-center justify-center gap-5 rounded-[16px] border-4 border-dashed border-[#239B88] py-6'>
                            <div className='items-center justify-center rounded-full bg-[#EAFBF9] p-[10px]'>
                                <img src="/assets/document-text.svg" alt="document" />
                            </div>
                            <p className='text-center text-[#8A8A8A]'>
                                Drop Your Document Here
                                <br />
                                (We promise to treat it with respect)
                            </p>
                        </div>
                        <p className='bg-[#F3F3F3] px-2 py-1 text-center font-semibold text-[#8A8A8A]'>We&apos;re friends with .docx, Google Docs, and plain text (No pdf)</p>
                    </div>
                </div>
            )
            }
        </div >
    )
}

export default FileUploader;