# analytics/seed_data.py

from pymongo import MongoClient
from datetime import datetime, timedelta
import random

client = MongoClient('mongodb://admin:password123@mongodb:27017/')
db = client['lms_analytics']

# Hapus data lama
db.activity_logs.drop()

# Data dummy
courses = ["Django Basics", "Python Advanced", "Docker Fundamentals",
           "REST API Design", "Database Optimization", "Redis Caching",
           "Authentication & Security", "Automated Testing"]

actions = ["view_course", "enroll", "post_comment", "view_content",
           "submit_quiz", "download_material"]

browsers = ["Chrome", "Firefox", "Safari", "Edge"]

# Generate 500 activity logs
logs = []
for i in range(500):
    user_id = random.randint(1, 50)
    action = random.choice(actions)
    course = random.choice(courses)
    days_ago = random.randint(0, 30)
    timestamp = datetime.now() - timedelta(
        days=days_ago,
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    log = {
        "user_id": user_id,
        "action": action,
        "course_name": course,
        "timestamp": timestamp,
        "metadata": {
            "ip": f"192.168.1.{random.randint(1, 255)}",
            "browser": random.choice(browsers)
        }
    }
    logs.append(log)

result = db.activity_logs.insert_many(logs)
print(f"Inserted {len(result.inserted_ids)} activity logs")

# Verifikasi
print(f"Total documents: {db.activity_logs.count_documents({})}")
