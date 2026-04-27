from ninja import NinjaAPI, Router
from ninja.errors import HttpError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from typing import List

from courses.models import Course, CourseMember
from core.schemas import (
    CourseIn, CourseOut, DetailCourseOut,
    RegisterIn, LoginIn, TokenOut, UserOut, UserUpdateIn,
    EnrollmentIn, EnrollmentOut, ProgressIn
)

apiv1 = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description="API untuk Simple Learning Management System"
)

# Inisialisasi Router agar rapi di Swagger
auth_router = Router(tags=["Authentication"])
enroll_router = Router(tags=["Enrollments"])

# ==================== Course Endpoints (Public/Main) ====================

@apiv1.get('courses/', response=List[CourseOut])
def listCourses(request):
    """Mengambil daftar semua course."""
    return Course.objects.select_related('teacher').all()

@apiv1.get('courses/{id}', response=DetailCourseOut)
def detailCourse(request, id: int):
    """Mengambil detail course beserta daftar kontennya."""
    try:
        return Course.objects.prefetch_related(
            'coursecontent_set'
        ).select_related('teacher').get(pk=id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course tidak ditemukan")

@apiv1.post('courses/', response={201: CourseOut})
def createCourse(request, data: CourseIn):
    """Membuat course baru."""
    teacher = User.objects.first()
    if not teacher:
        raise HttpError(400, "Belum ada user teacher di database")
    course = Course.objects.create(**data.dict(), teacher=teacher)
    return 201, course

@apiv1.put('courses/{id}', response=CourseOut)
def updateCourse(request, id: int, data: CourseIn):
    """Mengupdate data course secara keseluruhan."""
    course = get_object_or_404(Course, pk=id)
    for attr, value in data.dict().items():
        setattr(course, attr, value)
    course.save()
    return course

@apiv1.delete('courses/{id}', response={204: None})
def deleteCourse(request, id: int):
    """Menghapus course."""
    course = get_object_or_404(Course, pk=id)
    course.delete()
    return 204, None


# ==================== Authentication Endpoints ====================

@auth_router.post("/register", response={201: UserOut})
def register(request, data: RegisterIn):
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username sudah digunakan")
    user = User.objects.create_user(**data.dict())
    return 201, user

@auth_router.post("/login", response=TokenOut)
def login_user(request, data: LoginIn):
    user = authenticate(username=data.username, password=data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")
    return {"access": "fake-jwt-token", "refresh": "fake-refresh-token"}

@auth_router.get("/me", response=UserOut)
def get_me(request):
    if not request.user.is_authenticated:
        raise HttpError(401, "Silakan login terlebih dahulu")
    return request.user


# ==================== Enrollment Endpoints ====================

@enroll_router.post("/", response={201: EnrollmentOut})
def enroll_course(request, data: EnrollmentIn):
    # Gunakan user pertama jika belum ada sistem login (untuk testing)
    current_user = request.user if request.user.is_authenticated else User.objects.first()
    
    if CourseMember.objects.filter(user_id=current_user, course_id_id=data.course_id).exists():
        raise HttpError(400, "Anda sudah terdaftar di matkul ini")

    enrollment = CourseMember.objects.create(
        user_id=current_user,
        course_id_id=data.course_id,
        roles='std'
    )
    return 201, enrollment

@enroll_router.get("/my-courses", response=List[EnrollmentOut])
def my_courses(request):
    current_user = request.user if request.user.is_authenticated else User.objects.first()
    return CourseMember.objects.filter(user_id=current_user).select_related('course_id', 'course_id__teacher')

# Daftarkan Router ke API Utama
apiv1.add_router("/auth/", auth_router)
apiv1.add_router("/enrollments/", enroll_router)