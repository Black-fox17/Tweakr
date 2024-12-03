import time

def retry_with_backoff(func, max_retries=3, initial_delay=2, *args, **kwargs):
    """
    Retry a function with exponential backoff.
    
    Parameters:
    - func: The function to retry.
    - max_retries: Maximum number of retry attempts.
    - initial_delay: Initial delay in seconds between retries.
    - args, kwargs: Arguments and keyword arguments to pass to the function.
    
    Returns:
    - The result of the function call if successful.
    
    Raises:
    - Exception if max retries are exceeded.
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(initial_delay * (2 ** attempt))  # Exponential backoff
            else:
                raise Exception("Max retries exceeded") from e
