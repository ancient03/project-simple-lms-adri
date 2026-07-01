# utils/redis_client.py
import redis
import json

r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)


def cache_course_detail(course_id, course_data, ttl=300):
    """Cache detail course sebagai JSON string."""
    key = f'course:{course_id}:detail'
    r.set(key, json.dumps(course_data), ex=ttl)


def get_cached_course_detail(course_id):
    """Ambil detail course dari cache."""
    key = f'course:{course_id}:detail'
    data = r.get(key)
    if data:
        return json.loads(data)
    return None


def increment_course_views(course_id):
    """Increment view counter untuk course."""
    key = f'course:{course_id}:views'
    return r.incr(key)


def update_course_popularity(course_id, score_increment=1):
    """Update popularity score di sorted set."""
    r.zincrby('popular_courses', score_increment, f'course:{course_id}')


def get_top_courses(limit=10):
    """Ambil top N course terpopuler."""
    return r.zrevrange('popular_courses', 0, limit - 1, withscores=True)