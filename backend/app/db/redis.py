"""Upstash Redis client"""
import redis
import os

_redis = None


def init_redis():
    global _redis
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if url and token:
        _redis = redis.from_url(url, password=token, decode_responses=True)
    return _redis


def get_redis():
    global _redis
    if _redis is None:
        init_redis()
    return _redis