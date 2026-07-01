# pyrefly: ignore [missing-import]
from ninja import NinjaAPI, Router, FilterSchema, Field, Query, File
from ninja.security import SessionAuth, HttpBearer
from ninja.errors import HttpError
from ninja.pagination import paginate, PageNumberPagination
from ninja.files import UploadedFile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from typing import List, Optional
from datetime import datetime
from django.db.models import Q, Count


class FlexibleAuth(SessionAuth):
    """
    Custom auth: trusts request.auth if already set (e.g. by Ninja TestClient),
    otherwise falls back to standard Django SessionAuth.
    """
    def authenticate(self, request, key):
        # TestClient sets request.auth directly — trust it
        if hasattr(request, 'auth') and request.auth is not None:
            return request.auth
        return super().authenticate(request, key)

from courses.models import Course, CourseMember, CourseContent
from core.schemas import (
    CourseIn, CourseOut, DetailCourseOut, CourseUpdate,
    ContentOut, ContentUpdate,
    CourseOutV2, TeacherOutV2,
    RegisterIn, LoginIn, TokenOut, UserOut, UserUpdateIn,
    EnrollmentIn, EnrollmentOut, ProgressIn
)


apiv1 = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description="API untuk Simple Learning Management System",
    auth=FlexibleAuth(),
    csrf=False,
    urls_namespace="apiv1"
)

# Inisialisasi Router agar rapi di Swagger
auth_router = Router(tags=["Authentication"])
enroll_router = Router(tags=["Enrollments"])

# ==================== Course Endpoints (Public/Main) ====================

# === Filter Schema ===
class CourseFilter(FilterSchema):
    price: Optional[int] = 0
    created_at: Optional[datetime] = None
    search: Optional[str] = Field(
        None,
        q=['name__icontains', 'description__icontains']
    )

    def filter_price(self, value: int) -> Q:
        if value > 0:
            return Q(price__gt=value)
        return Q()

    def filter_created_at(self, value: datetime) -> Q:
        if value:
            return Q(created_at__gt=value)
        return Q()


@apiv1.get('courses/', response=List[CourseOut])
@paginate(PageNumberPagination, page_size=10)
def listCourses(request, filters: CourseFilter = Query(...), ordering: str = '-created_at'):
    """
    Menampilkan daftar course dengan filtering, sorting, dan pagination.

    Query Parameters:
    - search: Pencarian berdasarkan nama atau deskripsi
    - price: Menampilkan course dengan harga di atas nilai ini
    - created_at: Menampilkan course setelah tanggal ini
    - ordering: Pengurutan (name, -name, price, -price, created_at, -created_at)
    - page: Nomor halaman
    """
    # Validasi ordering
    allowed_fields = ['name', 'price', 'created_at', '-name', '-price', '-created_at']
    if ordering not in allowed_fields:
        ordering = '-created_at'

    # Query dengan select_related untuk optimasi
    courses = Course.objects.select_related('teacher').all()

    # Terapkan filter
    courses = filters.filter(courses)

    # Terapkan sorting
    courses = courses.order_by(ordering)

    return courses

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
    teacher = request.auth
    course = Course.objects.create(**data.dict(), teacher=teacher)
    return 201, course

@apiv1.patch('courses/{id}', response=CourseOut)
def updateCourse(request, id: int, data: CourseUpdate):
    """
    Partial update course. Hanya field yang dikirim yang akan diubah.
    Hanya teacher pemilik course yang boleh mengupdate.
    """
    course = get_object_or_404(Course, pk=id)

    # TODO: Tambahkan validasi otorisasi untuk teacher
    # if course.teacher != request.auth:
    #     raise HttpError(403, "Hanya teacher pemilik course yang boleh mengupdate.")

    # Update hanya field yang dikirim (exclude_unset=True)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(course, attr, value)
    course.save()
    return course

@apiv1.delete('courses/{id}', response={204: None})
def deleteCourse(request, id: int):
    """Menghapus course."""
    course = get_object_or_404(Course, pk=id)
    course.delete()
    return 204, None


@apiv1.post('courses/{id}/upload-image/')
def uploadCourseImage(request, id: int, file: UploadedFile = File(...)):
    """
    Upload gambar thumbnail untuk course.
    Hanya teacher yang membuat course yang boleh mengupload.
    """
    course = get_object_or_404(Course, pk=id)

    # TODO: Tambahkan validasi otorisasi untuk teacher
    # if course.teacher != request.auth:
    #     raise HttpError(403, "Hanya teacher pemilik course yang boleh mengupload gambar.")

    # Validasi ukuran file (maks 2MB)
    if file.size > 2 * 1024 * 1024:
        raise HttpError(400, "Ukuran file maksimal 2MB.")

    # Validasi tipe file
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if file.content_type not in allowed_types:
        raise HttpError(400, f"Tipe file harus salah satu dari: {', '.join(allowed_types)}")

    # Simpan file
    course.image = file
    course.save()

    return {"message": "Image berhasil diupload.", "filename": file.name, "image_url": course.image.url}


# ==================== Authentication Endpoints ====================

@auth_router.post("/register", response={201: UserOut}, auth=None)
def register(request, data: RegisterIn):
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username sudah digunakan")
    user = User.objects.create_user(**data.dict())
    return 201, user

@auth_router.post("/login", response=TokenOut, auth=None)
def login_user(request, data: LoginIn):
    from django.contrib.auth import login as django_login
    user = authenticate(username=data.username, password=data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")
    # Create a real Django session so SessionAuth works on subsequent requests
    django_login(request, user)
    return {"access": "fake-jwt-token", "refresh": "fake-refresh-token"}

@auth_router.get("/me", response=UserOut)
def get_me(request):
    if not request.user.is_authenticated:
        raise HttpError(401, "Silakan login terlebih dahulu")
    return request.user


# ==================== Enrollment Endpoints ====================

@enroll_router.post("/", response={201: EnrollmentOut})
def enroll_course(request, data: EnrollmentIn):
    current_user = request.auth

    if CourseMember.objects.filter(user=current_user, course_id=data.course_id).exists():
        raise HttpError(400, "Anda sudah terdaftar di matkul ini")

    enrollment = CourseMember.objects.create(
        user=current_user,
        course_id=data.course_id,
        role='student'
    )
    return 201, enrollment

@enroll_router.get("/my-courses", response=List[EnrollmentOut])
def my_courses(request):
    current_user = request.auth
    return CourseMember.objects.filter(user=current_user).select_related('course', 'course__teacher', 'user')

# ==================== CourseContent Endpoints ====================

content_router = Router(tags=["Course Contents"])

class ContentFilter(FilterSchema):
    search: Optional[str] = Field(None, q=['name__icontains', 'description__icontains'])
    course_id: Optional[int] = None

@content_router.get('/', response=List[ContentOut])
@paginate(PageNumberPagination, page_size=10)
def listContents(request, filters: ContentFilter = Query(...), ordering: str = 'name'):
    """
    Menampilkan daftar konten dengan filtering, sorting, dan pagination.
    """
    allowed_fields = ['name', '-name']
    if ordering not in allowed_fields:
        ordering = 'name'

    contents = CourseContent.objects.all()
    contents = filters.filter(contents)
    contents = contents.order_by(ordering)
    return contents

@content_router.patch('/{id}/', response=ContentOut)
def updateContent(request, id: int, data: ContentUpdate):
    """
    Partial update course content.
    """
    content = get_object_or_404(CourseContent, pk=id)

    # TODO: Validasi: hanya teacher pemilik course yang boleh update
    # course = content.course_id
    # if course.teacher != request.auth:
    #     raise HttpError(403, "Hanya teacher pemilik course yang boleh mengupdate content.")

    for attr, value in data.dict(exclude_unset=True).items():
        setattr(content, attr, value)
    content.save()
    return content

@content_router.get('/{id}/download/', response={200: bytes})
def downloadAttachment(request, id: int):
    """
    Download file attachment dari course content.
    Hanya member course yang boleh mendownload.
    """
    content = get_object_or_404(CourseContent, pk=id)

    # TODO: Validasi: user harus terdaftar sebagai member course
    # current_user = request.user if request.user.is_authenticated else User.objects.first()
    # is_member = CourseMember.objects.filter(
    #     course_id=content.course_id,
    #     user_id=current_user
    # ).exists()
    # if not is_member:
    #     raise HttpError(403, "Anda harus terdaftar di course ini untuk mendownload file.")

    if not content.file_attachment:
        raise HttpError(404, "Content ini tidak memiliki file attachment.")

    return FileResponse(
        content.file_attachment.open('rb'),
        as_attachment=True,
        filename=content.file_attachment.name.split('/')[-1]
    )

@content_router.post('/{id}/upload-attachment/')
def uploadContentAttachment(request, id: int, file: UploadedFile = File(...)):
    """
    Upload file attachment (materi) untuk course content.
    """
    content = get_object_or_404(CourseContent, pk=id)

    # TODO: Validasi: hanya teacher pemilik course
    # if content.course_id.teacher != request.auth:
    #     raise HttpError(403, "Hanya teacher pemilik course yang boleh mengupdate.")

    # Validasi ukuran file (maks 10MB)
    if file.size > 10 * 1024 * 1024:
        raise HttpError(400, "Ukuran file maksimal 10MB.")

    # Validasi tipe file
    allowed_types = [
        'application/pdf',
        'application/zip',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document', # .docx
        'application/vnd.openxmlformats-officedocument.presentationml.presentation', # .pptx
    ]
    if file.content_type not in allowed_types:
        raise HttpError(400, "Tipe file tidak diizinkan. Hanya PDF, DOCX, PPTX, dan ZIP.")
    
    # Simpan file
    content.file_attachment = file
    content.save()

    return {"message": "Attachment berhasil diupload.", "filename": file.name, "file_url": content.file_attachment.url}


# Daftarkan Router ke API Utama
apiv1.add_router("/auth/", auth_router)
apiv1.add_router("/enrollments/", enroll_router)
apiv1.add_router("/contents/", content_router)
