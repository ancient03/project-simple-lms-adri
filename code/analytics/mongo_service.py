# analytics/mongo_service.py

from pymongo import MongoClient
from datetime import datetime
from typing import Optional


def get_mongo_db():
    """Mendapatkan koneksi ke database MongoDB lms_analytics."""
    client = MongoClient('mongodb://admin:password123@mongodb:27017/')
    return client['lms_analytics']


def log_activity(user_id: int, action: str, course_name: str = None,
                 metadata: dict = None):
    """
    Mencatat aktivitas user ke MongoDB.

    Args:
        user_id: ID user dari PostgreSQL
        action: Jenis aktivitas (view_course, enroll, post_comment, dll.)
        course_name: Nama course terkait (opsional)
        metadata: Data tambahan (opsional)
    """
    db = get_mongo_db()

    log_entry = {
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.now(),
    }

    if course_name:
        log_entry["course_name"] = course_name

    if metadata:
        log_entry["metadata"] = metadata

    result = db.activity_logs.insert_one(log_entry)
    return str(result.inserted_id)


def get_popular_courses(limit: int = 5):
    """
    Mengambil course terpopuler berdasarkan jumlah views.

    Returns:
        List of dicts: [{course, total_views, unique_user_count}, ...]
    """
    db = get_mongo_db()

    pipeline = [
        {"$match": {"action": "view_course"}},
        {"$group": {
            "_id": "$course_name",
            "total_views": {"$sum": 1},
            "unique_users": {"$addToSet": "$user_id"}
        }},
        {"$addFields": {
            "unique_user_count": {"$size": "$unique_users"}
        }},
        {"$sort": {"total_views": -1}},
        {"$limit": limit},
        {"$project": {
            "course": "$_id",
            "total_views": 1,
            "unique_user_count": 1,
            "_id": 0
        }}
    ]

    return list(db.activity_logs.aggregate(pipeline))


def get_user_activity_summary(user_id: int):
    """
    Mengambil ringkasan aktivitas user tertentu.

    Returns:
        Dict: {total_actions, actions_breakdown, recent_activities}
    """
    db = get_mongo_db()

    # Total aksi dan breakdown
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$action",
            "count": {"$sum": 1}
        }}
    ]
    breakdown = list(db.activity_logs.aggregate(pipeline))

    # 10 aktivitas terbaru
    recent = list(
        db.activity_logs.find(
            {"user_id": user_id},
            {"_id": 0, "action": 1, "course_name": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(10)
    )

    # Konversi datetime ke string untuk serialisasi JSON
    for activity in recent:
        if "timestamp" in activity:
            activity["timestamp"] = activity["timestamp"].isoformat()

    return {
        "user_id": user_id,
        "actions_breakdown": {item["_id"]: item["count"] for item in breakdown},
        "total_actions": sum(item["count"] for item in breakdown),
        "recent_activities": recent
    }


def get_daily_activity_summary(days: int = 7):
    """
    Mengambil ringkasan aktivitas harian.

    Returns:
        List of dicts: [{date, total_actions, unique_user_count}, ...]
    """
    db = get_mongo_db()

    pipeline = [
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "total_actions": {"$sum": 1},
            "unique_users": {"$addToSet": "$user_id"}
        }},
        {"$addFields": {
            "unique_user_count": {"$size": "$unique_users"}
        }},
        {"$sort": {"_id": -1}},
        {"$limit": days},
        {"$project": {
            "date": "$_id",
            "total_actions": 1,
            "unique_user_count": 1,
            "_id": 0
        }}
    ]

    return list(db.activity_logs.aggregate(pipeline))


def get_top_active_users(limit: int = 3):
    """
    Mengambil user paling aktif berdasarkan total aktivitas.
    (Latihan 2: Top 3 active users)
    """
    db = get_mongo_db()
    pipeline = [
        {"$group": {
            "_id": "$user_id",
            "total_activities": {"$sum": 1}
        }},
        {"$sort": {"total_activities": -1}},
        {"$limit": limit},
        {"$project": {
            "user_id": "$_id",
            "total_activities": 1,
            "_id": 0
        }}
    ]
    return list(db.activity_logs.aggregate(pipeline))
