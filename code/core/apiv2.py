from ninja import NinjaAPI
from django.shortcuts import get_object_or_404
from django.db.models import Count

from courses.models import Course
from core.schemas import CourseOutV2


apiv2 = NinjaAPI(version='2.0', title="Simple LMS API v2", urls_namespace="apiv2")

@apiv2.get('courses/{id}/', response=CourseOutV2)
def getCourseV2(request, id: int):
    """
    Mengambil detail course versi 2 dengan response yang lebih lengkap.
    """
    course = get_object_or_404(
        Course.objects.select_related('teacher').annotate(
            member_count=Count('coursemember')
        ),
        pk=id
    )
    
    # Manually construct response to match schema
    response_data = {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "price": course.price,
        "teacher": {
            "id": course.teacher.id,
            "username": course.teacher.username,
            "full_name": course.teacher.get_full_name()
        },
        "member_count": course.member_count,
        "created_at": course.created_at
    }
    return response_data
