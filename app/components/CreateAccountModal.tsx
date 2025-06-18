import React, { useState, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { register, login } from '@/service/authService';
import { toast } from 'sonner';
import { Eye, EyeClosed, Loader2 } from 'lucide-react';

type CreateAccountModalProps = {
    setIsRegisterReady: (ready: boolean) => void;
    setIsLogin: (ready: boolean) => void;
    isLogin: boolean;
};

const CreateAccountModal = ({ setIsRegisterReady, setIsLogin, isLogin }: CreateAccountModalProps) => {
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);

    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
                setIsRegisterReady(false); // Close modal
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [setIsRegisterReady]);

    const [errors, setErrors] = useState({
        email: '',
        password: '',
        confirmPassword: ''
    });

    const isValidEmail = (email: string) =>
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    const validateField = (name: string, value: string) => {
        let error = '';

        switch (name) {
            case 'email':
                if (value && !isValidEmail(value)) {
                    error = 'Please enter a valid email address';
                }
                break;
            case 'password':
                if (value && value.length < 6) {
                    error = 'Password must be at least 6 characters';
                }
                break;
            case 'confirmPassword':
                if (!isLogin && value && value !== formData.password) {
                    error = 'Passwords do not match';
                }
                break;
        }

        return error;
    };

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: ''
    });


    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });

        // Real-time validation
        const error = validateField(name, value);
        setErrors({ ...errors, [name]: error });

        // Also validate confirm password when password changes
        if (name === 'password' && !isLogin && formData.confirmPassword) {
            const confirmError = validateField('confirmPassword', formData.confirmPassword);
            setErrors(prev => ({ ...prev, confirmPassword: confirmError }));
        }
    };

    const clearForm = () => {
        setFormData({ email: '', password: '', confirmPassword: '' });
        setErrors({ email: '', password: '', confirmPassword: '' });
    };

    const registerMutation = useMutation({
        mutationFn: register,
        onSuccess: (data) => {
            toast.success('Account created successfully!');
            localStorage.setItem('token', data?.data?.data?.access_token);
            localStorage.setItem("userEmail", data?.data?.data?.user?.email
            )
            localStorage.setItem("id", data?.data?.data?.user?.id)
            setIsRegisterReady(false);
        },
        onError: (err: any) => {
            const detail = err?.response?.data?.detail;
            const msg = Array.isArray(detail) && detail[0]?.msg
                ? detail[0].msg
                : err?.response?.data?.message || 'Registration failed';
            toast.error(msg);
        }
    });

    const loginMutation = useMutation({
        mutationFn: login,
        onSuccess: (data) => {
            toast.success('Login successful!');
            localStorage.setItem('token', data?.data?.data?.access_token);
            localStorage.setItem("userEmail", data?.data?.data?.user?.email
            )
            localStorage.setItem("id", data?.data?.data?.user?.id)
            clearForm()
            setIsRegisterReady(false);
        },
        onError: (err: any) => {
            const detail = err?.response?.data?.detail;
            const msg = Array.isArray(detail) && detail[0]?.msg
                ? detail[0].msg
                : err?.response?.data?.message || 'Login failed';
            toast.error(msg);
        }
    });



    const handleSubmit = () => {
        const { email, password, confirmPassword } = formData;

        // Validate all fields before submission
        const newErrors = {
            email: validateField('email', email),
            password: validateField('password', password),
            confirmPassword: !isLogin ? validateField('confirmPassword', confirmPassword) : ''
        };

        // Check for empty fields
        if (!email) newErrors.email = 'Email is required';
        if (!password) newErrors.password = 'Password is required';
        if (!isLogin && !confirmPassword) newErrors.confirmPassword = 'Please confirm your password';

        setErrors(newErrors);

        // Check if there are any errors
        const hasErrors = Object.values(newErrors).some(error => error !== '');
        if (hasErrors) {
            return;
        }

        const payload = { email, password };

        if (isLogin) {
            loginMutation.mutate(payload);
        } else {
            registerMutation.mutate(payload);
        }
    };

    // Helper function to get input border class
    const getInputBorderClass = (fieldName: keyof typeof errors) => {
        return errors[fieldName]
            ? 'border-red-500 bg-red-50'
            : 'border-[#FAFAFA] bg-[#FAFAFA]';
    };

    const isLoading = registerMutation.isPending || loginMutation.isPending;

    return (
        <div className=" fixed inset-0 z-[9999] flex  justify-center overflow-y-auto bg-black bg-opacity-50 text-[#545454]">
            <div ref={modalRef}
                className="scrollbar-hide mt-10 flex max-h-[90vh] max-w-[811px] flex-col items-center  justify-center gap-2 overflow-y-auto rounded-lg bg-white p-6 shadow-lg">
                <p className=' text-[20px] font-medium sm:pt-28 md:pt-0'>
                    {isLogin ? "Welcome Back!" : "Your Citations Are Ready to Roll!"}
                </p>
                <div className='flex w-full flex-col items-start py-4 text-left'>
                    <h3 className='text-[24px] font-semibold text-black'>
                        {isLogin ? "Login to your Tweakrr account" : "Create your Tweakrr account to unleash them."}
                    </h3>
                    <p className='text-[18px] text-[#8A8A8A]'>
                        (Don&apos;t worry, this takes 30 seconds - way faster than formatting one citation manually)
                    </p>
                </div>
                <div className='my-4 h-[0.5px] w-full bg-[#D8D8D8]'></div>
                <div className='flex w-full flex-col gap-2'>
                    <div className='flex w-full flex-col gap-1'>
                        <label className='text-[18px] font-semibold'>Email</label>
                        <input
                            name="email"
                            type="email"
                            placeholder='Email'
                            value={formData.email}
                            onChange={handleChange}
                            className={`w-full rounded-[10px] border p-4 text-[18px] text-[#9E9E9E] outline-none ${getInputBorderClass('email')}`}
                        />
                        {errors.email && (
                            <p className='mt-1 text-sm text-red-500'>{errors.email}</p>
                        )}
                    </div>
                    <div className='flex flex-col gap-4 sm:flex-row'>
                        <div className='flex w-full flex-col gap-1'>
                            <label className='text-[18px] font-semibold'>Password</label>
                            <div className='relative w-full'>
                                <input
                                    name="password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder='Password'
                                    value={formData.password}
                                    onChange={handleChange}
                                    className={`w-full rounded-[10px] border p-4 text-[18px] text-[#9E9E9E] outline-none ${getInputBorderClass('password')}`}
                                />
                                <div
                                    className='absolute right-4 top-[18px] size-[20px] cursor-pointer'
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? <Eye /> : <EyeClosed />}
                                </div>
                                {errors.password && (
                                    <p className='mt-1 text-sm text-red-500'>{errors.password}</p>
                                )}
                            </div>
                        </div>
                        {!isLogin && (
                            <div className='flex w-full flex-col gap-1'>
                                <label className='text-[18px] font-semibold'>Confirm Password</label>
                                <div className='relative w-full'>
                                    <input
                                        name="confirmPassword"
                                        type={showConfirm ? "text" : "password"}
                                        placeholder='Confirm Password'
                                        value={formData.confirmPassword}
                                        onChange={handleChange}
                                        className='w-full rounded-[10px] border border-[#FAFAFA] bg-[#FAFAFA] p-4 text-[18px] text-[#9E9E9E] outline-none' />
                                    <div
                                        className='absolute right-4 top-[18px] size-[20px] cursor-pointer'
                                        onClick={() => setShowConfirm(!showConfirm)}
                                    >
                                        {showConfirm ? <Eye /> : <EyeClosed />}
                                    </div>
                                    {errors.confirmPassword && (
                                        <p className='mt-1 text-sm text-red-500'>{errors.confirmPassword}</p>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                {/* <div className='flex w-full items-center gap-6'>
                    <p className='text-[18px]'>Or take the express route</p>
                    <div className='hidden h-[0.5px] w-[67%] bg-[#D8D8D8] sm:block'></div>
                </div> */}
                <div className='flex w-full flex-col gap-2'>
                    {/* <button className='flex w-full items-center justify-center gap-4 rounded-full border border-[#EEEEEE] p-4'>
                        <img src="/assets/google.svg" alt="google" />
                        <p className='text-[16px] font-medium'>Continue with Google</p>
                    </button> */}
                    <p>
                        {isLogin ? "Don't have an account?" : "Already registered?"}
                        <span
                            className='ml-1 cursor-pointer font-medium text-[#010F34]'
                            onClick={() => setIsLogin(!isLogin)}
                        >
                            {isLogin ? "Create one!" : "Login!"}
                        </span>
                    </p>
                    <button
                        onClick={handleSubmit}
                        disabled={isLoading}
                        className={`my-4 flex w-full items-center justify-center gap-2 self-start rounded-full px-[20px] py-[14px] text-[14px] font-semibold text-black transition-all duration-200 ${isLoading
                            ? 'cursor-not-allowed bg-[#31DAC0]/70'
                            : 'bg-[#31DAC0] hover:bg-[#2BC5AD]'
                            }`}
                    >
                        {isLoading && <Loader2 className="size-4 animate-spin" />}
                        {isLoading
                            ? (isLogin ? 'Logging in...' : 'Creating account...')
                            : 'Work Your Citation Magic'
                        }
                    </button>
                </div>
                <div>
                    <p className='text-center'>
                        By signing up, you&apos;re joining the citation liberation movement. <br />
                        Also, you agree to <span className='font-medium text-[#010F34]'>our Terms</span> and <span className='font-medium text-[#010F34]'>Privacy Policy</span>.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default CreateAccountModal;
