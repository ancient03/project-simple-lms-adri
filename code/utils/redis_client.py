import redis
import json
import os

_host = os.environ.get('REDIS_HOST', 'redis')
_port = int(os.environ.get('REDIS_PORT', 6379))
r = redis.Redis(host=_host, port=_port, db=0, decode_responses=True)


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