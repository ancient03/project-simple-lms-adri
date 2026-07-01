# tests/test_api_coverage.py
#
# Tujuan: meningkatkan code coverage pada core/apiv1.py
# Endpoint yang dicakup di sini adalah yang belum dicakup di test_lms_api.py

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from courses.models import Course, CourseMember, CourseContent, Comment


class BaseAPITestCase(TestCase):
    """Base setup yang dipakai semua test class di file ini."""

    def setUp(self):
        self.client = Client()

        self.teacher = User.objects.create_user(
            username='teacher_cov',
            password='pass1234',
            email='teacher_cov@example.com'
        )
        self.student = User.objects.create_user(
            username='student_cov',
            password='pass1234',
            email='student_cov@example.com'
        )

        self.course = Course.objects.create(
            name='Coverage Course',
            description='Test coverage',
            price=100000,
            teacher=self.teacher
        )
        CourseMember.objects.create(
            course=self.course,
            user=self.teacher,
            role='teacher'
        )
        self.content = CourseContent.objects.create(
            course_id=self.course,
            name='Coverage Content',
            description='Content for coverage tests',
            video_url='https://youtube.com/watch?v=cov'
        )


# ── Auth endpoints ────────────────────────────────────────────────────────────

class TestRegisterAPI(BaseAPITestCase):
    """Covers: register endpoint (lines 176-179)."""

    def test_register_new_user(self):
        """Berhasil daftar user baru."""
        response = self.client.post(
            '/api/v1/auth/register',
            data=json.dumps({
                'username': 'newuser',
                'password': 'newpass123',
                'email': 'new@example.com',
                'first_name': 'New',
                'last_name': 'User'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['username'], 'newuser')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_duplicate_username(self):
        """Daftar dengan username yang sudah ada → 400."""
        response = self.client.post(
            '/api/v1/auth/register',
            data=json.dumps({
                'username': 'teacher_cov',   # sudah ada
                'password': 'pass1234',
                'email': 'dup@example.com'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class TestLoginAPI(BaseAPITestCase):
    """Covers: login success/failure branches (lines 183-189)."""

    def test_login_wrong_credentials(self):
        """Login dengan password salah → 401."""
        response = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': 'teacher_cov', 'password': 'wrong'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)


class TestGetMeAPI(BaseAPITestCase):
    """Covers: get_me endpoint (lines 193-195)."""

    def test_get_me_authenticated(self):
        """User yang sudah login bisa melihat profil diri sendiri."""
        self.client.force_login(self.teacher)
        response = self.client.get('/api/v1/auth/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'teacher_cov')


# ── Course endpoints — uncovered branches ─────────────────────────────────────

class TestCourseFilterAPI(BaseAPITestCase):
    """Covers: CourseFilter price/search branches (lines 62-69, 86-99)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)
        # Tambah course mahal agar price filter bisa diuji
        Course.objects.create(
            name='Mahal Course', description='Mahal', price=999000,
            teacher=self.teacher
        )

    def test_list_courses_with_search(self):
        """Filter search mencari berdasarkan nama/deskripsi."""
        response = self.client.get('/api/v1/courses/?search=Coverage')
        self.assertEqual(response.status_code, 200)
        items = response.json().get('items', [])
        self.assertTrue(any('Coverage' in c['name'] for c in items))

    def test_list_courses_with_price_filter(self):
        """Filter price mengembalikan course dengan harga > nilai yang diberikan."""
        response = self.client.get('/api/v1/courses/?price=500000')
        self.assertEqual(response.status_code, 200)
        items = response.json().get('items', [])
        for course in items:
            self.assertGreater(course['price'], 500000)

    def test_list_courses_with_valid_ordering(self):
        """Ordering name berjalan tanpa error."""
        response = self.client.get('/api/v1/courses/?ordering=name')
        self.assertEqual(response.status_code, 200)

    def test_list_courses_with_invalid_ordering_falls_back(self):
        """Ordering tidak valid diganti default -created_at."""
        response = self.client.get('/api/v1/courses/?ordering=invalid_field')
        self.assertEqual(response.status_code, 200)


class TestCourseErrorCasesAPI(BaseAPITestCase):
    """Covers: 404 paths pada detail, update, delete (lines 104-109, 124-134, 139-141)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_get_course_detail_not_found(self):
        """Course tidak ada → 404."""
        response = self.client.get('/api/v1/courses/99999')
        self.assertEqual(response.status_code, 404)

    def test_update_course_not_found(self):
        """Update course tidak ada → 404."""
        response = self.client.patch(
            '/api/v1/courses/99999',
            data=json.dumps({'name': 'Ghost'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_course_not_found(self):
        """Delete course tidak ada → 404."""
        response = self.client.delete('/api/v1/courses/99999')
        self.assertEqual(response.status_code, 404)


# ── Enrollment endpoints ──────────────────────────────────────────────────────

class TestMyCoursesAPI(BaseAPITestCase):
    """Covers: my_courses endpoint (lines 216-217)."""

    def test_my_courses_returns_enrolled_list(self):
        """User yang enrolled bisa melihat daftar course-nya."""
        self.client.force_login(self.teacher)
        response = self.client.get('/api/v1/enrollments/my-courses')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)

    def test_enroll_then_check_my_courses(self):
        """Student yang baru enroll muncul di my-courses."""
        self.client.force_login(self.student)
        self.client.post(
            '/api/v1/enrollments/',
            data=json.dumps({'course_id': self.course.id}),
            content_type='application/json'
        )
        response = self.client.get('/api/v1/enrollments/my-courses')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(c['course']['id'] == self.course.id for c in data))


# ── Content endpoints ─────────────────────────────────────────────────────────

class TestContentListAPI(BaseAPITestCase):
    """Covers: listContents + ContentFilter (lines 233-240)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_list_contents(self):
        """Daftar semua content."""
        response = self.client.get('/api/v1/contents/')
        self.assertEqual(response.status_code, 200)
        items = response.json().get('items', response.json())
        self.assertGreaterEqual(len(items), 1)

    def test_list_contents_with_search(self):
        """Filter search pada content."""
        response = self.client.get('/api/v1/contents/?search=Coverage')
        self.assertEqual(response.status_code, 200)

    def test_list_contents_with_course_id_filter(self):
        """Filter berdasarkan course_id."""
        response = self.client.get(
            f'/api/v1/contents/?course_id={self.course.id}'
        )
        self.assertEqual(response.status_code, 200)
        items = response.json().get('items', response.json())
        self.assertGreaterEqual(len(items), 1)

    def test_list_contents_ordering(self):
        """Ordering name berjalan tanpa error."""
        response = self.client.get('/api/v1/contents/?ordering=-name')
        self.assertEqual(response.status_code, 200)

    def test_list_contents_invalid_ordering_falls_back(self):
        """Ordering tidak valid diganti ke default."""
        response = self.client.get('/api/v1/contents/?ordering=invalid')
        self.assertEqual(response.status_code, 200)


class TestContentUpdateAPI(BaseAPITestCase):
    """Covers: updateContent endpoint (lines 247-257)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_update_content_name(self):
        """Partial update nama content berhasil."""
        response = self.client.patch(
            f'/api/v1/contents/{self.content.id}/',
            data=json.dumps({'name': 'Updated Name'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.content.refresh_from_db()
        self.assertEqual(self.content.name, 'Updated Name')

    def test_update_content_not_found(self):
        """Update content tidak ada → 404."""
        response = self.client.patch(
            '/api/v1/contents/99999/',
            data=json.dumps({'name': 'Ghost'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_update_content_video_url(self):
        """Update video_url berhasil."""
        response = self.client.patch(
            f'/api/v1/contents/{self.content.id}/',
            data=json.dumps({'video_url': 'https://youtube.com/new'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['video_url'], 'https://youtube.com/new')


class TestContentDownloadAPI(BaseAPITestCase):
    """Covers: downloadAttachment no-file path (lines 265-279)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_download_content_without_attachment_returns_404(self):
        """Download content yang tidak punya file → 404."""
        response = self.client.get(
            f'/api/v1/contents/{self.content.id}/download/'
        )
        self.assertEqual(response.status_code, 404)

    def test_download_content_not_found(self):
        """Download content yang tidak ada → 404."""
        response = self.client.get('/api/v1/contents/99999/download/')
        self.assertEqual(response.status_code, 404)


class TestGetMeUnauthAPI(TestCase):
    """Covers: get_me unauthenticated branch (line 194)."""

    def test_get_me_unauthenticated_returns_401(self):
        """Akses /me tanpa login → 401."""
        response = Client().get('/api/v1/auth/me')
        self.assertEqual(response.status_code, 401)


class TestCreatedAtFilterAPI(BaseAPITestCase):
    """Covers: filter_created_at branch saat value ada (line 68)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_list_courses_with_created_at_filter(self):
        """Filter created_at mengembalikan course setelah tanggal tersebut."""
        response = self.client.get('/api/v1/courses/?created_at=2020-01-01T00:00:00Z')
        self.assertEqual(response.status_code, 200)
        items = response.json().get('items', [])
        # Semua course dibuat sesudah 2020, jadi semua muncul
        self.assertGreaterEqual(len(items), 1)


class TestUploadCourseImageAPI(BaseAPITestCase):
    """Covers: uploadCourseImage endpoint (lines 150-169)."""

    # Byte minimal JPEG yang valid (SOI + APP0 + EOI)
    VALID_JPEG = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xd9'
    )

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_upload_course_image_valid_jpeg(self):
        """Upload JPEG valid → 200, image_url ada di response."""
        img = SimpleUploadedFile('thumb.jpg', self.VALID_JPEG, content_type='image/jpeg')
        response = self.client.post(
            f'/api/v1/courses/{self.course.id}/upload-image/',
            {'file': img}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('image_url', response.json())

    def test_upload_course_image_valid_png(self):
        """Upload PNG valid → 200."""
        # Minimal PNG signature
        png_bytes = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx'
            b'\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        img = SimpleUploadedFile('thumb.png', png_bytes, content_type='image/png')
        response = self.client.post(
            f'/api/v1/courses/{self.course.id}/upload-image/',
            {'file': img}
        )
        self.assertEqual(response.status_code, 200)

    def test_upload_course_image_invalid_type_returns_400(self):
        """Upload file bukan gambar → 400."""
        txt = SimpleUploadedFile('doc.txt', b'hello world', content_type='text/plain')
        response = self.client.post(
            f'/api/v1/courses/{self.course.id}/upload-image/',
            {'file': txt}
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_course_image_too_large_returns_400(self):
        """Upload file > 2MB → 400."""
        large = SimpleUploadedFile(
            'big.jpg',
            b'x' * (2 * 1024 * 1024 + 1),   # 2MB + 1 byte
            content_type='image/jpeg'
        )
        response = self.client.post(
            f'/api/v1/courses/{self.course.id}/upload-image/',
            {'file': large}
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_course_image_course_not_found(self):
        """Upload gambar ke course yang tidak ada → 404."""
        img = SimpleUploadedFile('thumb.jpg', self.VALID_JPEG, content_type='image/jpeg')
        response = self.client.post(
            '/api/v1/courses/99999/upload-image/',
            {'file': img}
        )
        self.assertEqual(response.status_code, 404)


class TestUploadContentAttachmentAPI(BaseAPITestCase):
    """Covers: uploadContentAttachment endpoint (lines 290-314)."""

    VALID_PDF = b'%PDF-1.4\n%%EOF'
    VALID_ZIP = b'PK\x05\x06' + b'\x00' * 18   # minimal ZIP end-of-central-directory

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_upload_pdf_attachment_success(self):
        """Upload PDF valid → 200, file_url ada di response."""
        pdf = SimpleUploadedFile('notes.pdf', self.VALID_PDF, content_type='application/pdf')
        response = self.client.post(
            f'/api/v1/contents/{self.content.id}/upload-attachment/',
            {'file': pdf}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('file_url', response.json())

    def test_upload_zip_attachment_success(self):
        """Upload ZIP valid → 200."""
        zf = SimpleUploadedFile('files.zip', self.VALID_ZIP, content_type='application/zip')
        response = self.client.post(
            f'/api/v1/contents/{self.content.id}/upload-attachment/',
            {'file': zf}
        )
        self.assertEqual(response.status_code, 200)

    def test_upload_attachment_invalid_type_returns_400(self):
        """Upload tipe file tidak diizinkan → 400."""
        img = SimpleUploadedFile('photo.jpg', b'fake-image', content_type='image/jpeg')
        response = self.client.post(
            f'/api/v1/contents/{self.content.id}/upload-attachment/',
            {'file': img}
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_attachment_content_not_found(self):
        """Upload attachment ke content yang tidak ada → 404."""
        pdf = SimpleUploadedFile('notes.pdf', self.VALID_PDF, content_type='application/pdf')
        response = self.client.post(
            '/api/v1/contents/99999/upload-attachment/',
            {'file': pdf}
        )
        self.assertEqual(response.status_code, 404)


class TestDownloadWithAttachmentAPI(BaseAPITestCase):
    """Covers: FileResponse return path di downloadAttachment (line 279)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)
        # Upload PDF dulu agar content punya file_attachment
        pdf = SimpleUploadedFile('course_notes.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf')
        self.client.post(
            f'/api/v1/contents/{self.content.id}/upload-attachment/',
            {'file': pdf}
        )
        self.content.refresh_from_db()

    def test_download_content_with_attachment_returns_200(self):
        """Download content yang punya file → response file (200)."""
        if not self.content.file_attachment:
            self.skipTest('Upload attachment gagal di setUp, skip test download')
        response = self.client.get(
            f'/api/v1/contents/{self.content.id}/download/'
        )
        self.assertEqual(response.status_code, 200)
