# analytics/api.py

from ninja import Schema, Router
from typing import Optional
from core.apiv1 import FlexibleAuth
from .mongo_service import (
    log_activity,
    get_popular_courses,
    get_user_activity_summary,
    get_daily_activity_summary,
    get_top_active_users
)

analytics_router = Router(tags=["Analytics"])
apiAuth = FlexibleAuth()

# --- Schemas ---

class ActivityLogIn(Schema):
    action: str
    course_name: Optional[str] = None
    metadata: Optional[dict] = None


class ActivityLogOut(Schema):
    status: str
    log_id: str


# --- Endpoints ---

@analytics_router.post('log/', auth=apiAuth, response=ActivityLogOut)
def logActivity(request, data: ActivityLogIn):
    """Mencatat aktivitas user ke MongoDB."""
    log_id = log_activity(
        user_id=request.user.id,
        action=data.action,
        course_name=data.course_name,
        metadata=data.metadata
    )
    return {"status": "logged", "log_id": log_id}


@analytics_router.get('popular-courses/')
def popularCourses(request, limit: int = 5):
    """Mengambil daftar course terpopuler berdasarkan views."""
    return get_popular_courses(limit=limit)


@analytics_router.get('my-activity/', auth=apiAuth)
def myActivity(request):
    """Mengambil ringkasan aktivitas user yang sedang login."""
    return get_user_activity_summary(user_id=request.user.id)


@analytics_router.get('daily-summary/')
def dailySummary(request, days: int = 7):
    """Mengambil ringkasan aktivitas harian."""
    return get_daily_activity_summary(days=days)


@analytics_router.get('top-users/')
def topUsers(request, limit: int = 3):
    """Mengambil user paling aktif."""
    return get_top_active_users(limit=limit)
