from contextlib import asynccontextmanager

# import aioredis
import redis
from redis.asyncio import Redis
from fastapi import Depends
import os

from app.core.constants import REDIS_URL


async def get_redis_pool() -> Redis:
    pool = Redis.from_url(REDIS_URL, max_connections=40)
    print("connection redis: ", pool)
    return pool


async def get_redis_connection():
    pool = await get_redis_pool()  # Acquire the connection pool
    async with pool as conn:  # Acquire a connection from the pool
        yield conn


@asynccontextmanager
async def get_redis_session(redis_pool: Redis):
    # Get a connection from the pool
    redis = await redis_pool.acquire()

    try:
        # Yield the connection for use in the with block
        yield redis
    finally:
        # Release the connection back to the pool
        redis_pool.release(redis)
