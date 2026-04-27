from ninja import Schema, Field
from datetime import datetime
from typing import Optional, List

# ==================== User & Auth Schemas ====================

class UserOut(Schema):
    """Schema untuk data User yang dikembalikan dalam response."""
    id: int
    username: str
    first_name: str
    last_name: str
    email: str

class RegisterIn(Schema):
    """Schema untuk pendaftaran user baru."""
    username: str
    password: str
    email: str
    first_name: str = ""
    last_name: str = ""

class LoginIn(Schema):
    """Schema untuk login."""
    username: str
    password: str

class TokenOut(Schema):
    """Schema untuk response token (JWT Mock)."""
    access: str
    refresh: str

class UserUpdateIn(Schema):
    """Schema untuk update profil user."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

# ==================== Course Schemas ====================

class CourseIn(Schema):
    """Schema untuk input saat membuat/mengupdate Course."""
    name: str
    description: str = '-'
    price: int = 10000

class CourseOut(Schema):
    """Schema untuk output data Course."""
    id: int
    name: str
    description: str
    price: int
    image: Optional[str] = ''
    teacher: UserOut
    created_at: datetime
    updated_at: datetime

class ContentTitleOut(Schema):
    """Schema untuk menampilkan judul konten saja."""
    id: int
    name: str

class DetailCourseOut(CourseOut):
    """Schema untuk detail Course beserta daftar konten."""
    contents: List[ContentTitleOut] = Field(
        ..., alias="coursecontent_set"
    )

# ==================== Enrollment Schemas ====================

class EnrollmentIn(Schema):
    """Schema untuk mendaftar ke course."""
    course_id: int

class EnrollmentOut(Schema):
    """Schema untuk data pendaftaran (CourseMember)."""
    id: int
    user_id: UserOut = Field(..., alias="user_id")
    course_id: CourseOut = Field(..., alias="course_id")
    roles: str

class ProgressIn(Schema):
    """Schema untuk update progres belajar."""
    lesson_id: int
    is_complete: bool = True