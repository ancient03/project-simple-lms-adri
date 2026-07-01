# tests/test_lms_api.py

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from courses.models import Course, CourseMember, CourseContent, Comment


class BaseLMSTestCase(TestCase):
    """Base test class dengan setup data yang umum digunakan."""

    def setUp(self):
        self.client = Client()

        # Buat users
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='teacherpass123',
            email='teacher@example.com'
        )
        self.student = User.objects.create_user(
            username='student1',
            password='studentpass123',
            email='student@example.com'
        )
        self.other_user = User.objects.create_user(
            username='other_user',
            password='otherpass123',
            email='other@example.com'
        )

        # Buat course
        self.course = Course.objects.create(
            name='Django Testing Course',
            description='Belajar testing di Django',
            price=200000,
            teacher=self.teacher
        )

        # Daftarkan teacher sebagai member
        CourseMember.objects.create(
            course=self.course,
            user=self.teacher,
            role='teacher'
        )


class TestAuthenticationAPI(BaseLMSTestCase):
    """Test autentikasi API."""

    def test_login_success(self):
        """Test login dengan kredensial yang benar."""
        response = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': 'teacher1', 'password': 'teacherpass123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access', data)

    def test_login_wrong_password(self):
        """Test login dengan password yang salah."""
        response = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': 'teacher1', 'password': 'wrongpassword'}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 401])

    def test_access_protected_endpoint_without_auth(self):
        """Test akses endpoint tanpa autentikasi harus ditolak (403)."""
        response = self.client.get('/api/v1/courses/')
        # Django Ninja SessionAuth returns 403 Forbidden for unauthenticated requests
        self.assertIn(response.status_code, [401, 403])


class TestCourseAPI(BaseLMSTestCase):
    """Test CRUD operations untuk Course."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_list_courses(self):
        """Test mendapatkan daftar course."""
        response = self.client.get('/api/v1/courses/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Paginated response has 'items' key
        items = data.get('items', data)
        self.assertGreaterEqual(len(items), 1)

    def test_create_course(self):
        """Test membuat course baru."""
        data = {
            'name': 'Python Advanced',
            'description': 'Materi Python lanjutan',
            'price': 300000
        }
        response = self.client.post(
            '/api/v1/courses/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['name'], 'Python Advanced')
        self.assertEqual(Course.objects.count(), 2)

    def test_get_course_detail(self):
        """Test mendapatkan detail course."""
        response = self.client.get(f'/api/v1/courses/{self.course.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Django Testing Course')

    def test_update_course(self):
        """Test update course."""
        data = {'name': 'Updated Course Name'}
        response = self.client.patch(
            f'/api/v1/courses/{self.course.id}',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, 'Updated Course Name')

    def test_delete_course(self):
        """Test hapus course."""
        response = self.client.delete(f'/api/v1/courses/{self.course.id}')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Course.objects.count(), 0)


class TestEnrollmentAPI(BaseLMSTestCase):
    """Test enrollment (pendaftaran) ke course."""

    def test_student_enroll_to_course(self):
        """Test student mendaftar ke course."""
        self.client.force_login(self.student)
        response = self.client.post(
            '/api/v1/enrollments/',
            data=json.dumps({'course_id': self.course.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Verifikasi member terdaftar
        self.assertTrue(
            CourseMember.objects.filter(
                course=self.course,
                user=self.student,
            ).exists()
        )

    def test_student_cannot_enroll_twice(self):
        """Test student tidak bisa mendaftar dua kali ke course yang sama."""
        self.client.force_login(self.student)

        # Enroll pertama kali
        self.client.post(
            '/api/v1/enrollments/',
            data=json.dumps({'course_id': self.course.id}),
            content_type='application/json'
        )

        # Enroll kedua kali - harus gagal
        response = self.client.post(
            '/api/v1/enrollments/',
            data=json.dumps({'course_id': self.course.id}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 409])


class TestCourseContentAPI(BaseLMSTestCase):
    """Test course content endpoints."""

    def setUp(self):
        super().setUp()

        # Daftarkan student ke course
        self.student_member = CourseMember.objects.create(
            course=self.course,
            user=self.student,
            role='student'
        )

        # Buat content dengan field name yang benar: course_id (ForeignKey)
        self.content = CourseContent.objects.create(
            course_id=self.course,
            name='Introduction to Testing',
            description='Pengenalan automated testing',
            video_url='https://youtube.com/watch?v=example'
        )

    def test_list_contents(self):
        """Test mendapatkan daftar course content."""
        self.client.force_login(self.teacher)
        response = self.client.get('/api/v1/contents/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        items = data.get('items', data)
        self.assertGreaterEqual(len(items), 1)

    def test_update_content(self):
        """Test partial update course content."""
        self.client.force_login(self.teacher)
        data = {'name': 'Updated Content Name'}
        response = self.client.patch(
            f'/api/v1/contents/{self.content.id}/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.content.refresh_from_db()
        self.assertEqual(self.content.name, 'Updated Content Name')