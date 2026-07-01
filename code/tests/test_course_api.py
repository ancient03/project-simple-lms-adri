# tests/test_course_api.py

from django.test import TestCase
from django.contrib.auth.models import User
from ninja.testing import TestClient
from courses.models import Course
from core.apiv1 import apiv1


class TestCourseAPI(TestCase):
    """Integration test: menguji API endpoint Course
    yang melibatkan HTTP request, serialization, dan database.
    """

    def setUp(self):
        self.client = TestClient(apiv1)
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='testpass123'
        )

    def test_create_course_via_api(self):
        """Test membuat course melalui API endpoint."""
        data = {
            'name': 'Django Testing',
            'description': 'Belajar automated testing',
            'price': 200000
        }
        # With TestClient, auth is passed as a parameter and data is passed as `json`
        response = self.client.post('/courses/', json=data, auth=self.teacher)

        # Verifikasi response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['name'], 'Django Testing')

        # Verifikasi data tersimpan di database
        self.assertEqual(Course.objects.count(), 1)
        course = Course.objects.first()
        self.assertEqual(course.name, 'Django Testing')
        self.assertEqual(course.teacher, self.teacher)