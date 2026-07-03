import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from courses.models import Course, CourseMember, Quiz, Question, Choice, QuizAttempt, Certificate

class TestQuizAPI(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.teacher = User.objects.create_user(
            username='teacher2',
            password='password123',
            email='teacher2@example.com'
        )
        self.student = User.objects.create_user(
            username='student2',
            password='password123',
            email='student2@example.com'
        )

        # Course
        self.course = Course.objects.create(
            name='Test Course for Quiz',
            description='Desc',
            price=0,
            teacher=self.teacher
        )

        # Enrollment
        CourseMember.objects.create(
            course=self.course,
            user=self.teacher,
            role='teacher'
        )
        CourseMember.objects.create(
            course=self.course,
            user=self.student,
            role='student'
        )

    def get_auth_headers(self, username, password):
        res = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': username, 'password': password}),
            content_type='application/json'
        )
        token = res.json().get('access')
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    def test_create_quiz(self):
        # Teacher creates quiz
        headers = self.get_auth_headers('teacher2', 'password123')
        payload = {
            "course_id": self.course.id,
            "title": "Ujian Akhir",
            "passing_grade": 70,
            "attempt_limit": 3
        }
        res = self.client.post('/api/v1/quizzes/', data=json.dumps(payload), content_type='application/json', **headers)
        self.assertEqual(res.status_code, 201)
        
        # Student trying to create quiz should fail (403)
        student_headers = self.get_auth_headers('student2', 'password123')
        res = self.client.post('/api/v1/quizzes/', data=json.dumps(payload), content_type='application/json', **student_headers)
        self.assertEqual(res.status_code, 403)

    def test_quiz_flow(self):
        # Setup Quiz manually for faster flow
        quiz = Quiz.objects.create(course=self.course, title="Kuis 1", passing_grade=50, attempt_limit=2)
        q1 = Question.objects.create(quiz=quiz, text="Q1", marks=10)
        c1 = Choice.objects.create(question=q1, text="A", is_correct=True)
        c2 = Choice.objects.create(question=q1, text="B", is_correct=False)
        
        student_headers = self.get_auth_headers('student2', 'password123')

        # 1. Student get quiz -> should not contain is_correct
        res = self.client.get(f'/api/v1/quizzes/{quiz.id}/', **student_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn('is_correct', data['questions'][0]['choices'][0])

        # 2. Student submit correct answer
        payload = {
            "answers": [
                {"question_id": q1.id, "choice_id": c1.id}
            ]
        }
        res = self.client.post(f'/api/v1/quizzes/{quiz.id}/submit/', data=json.dumps(payload), content_type='application/json', **student_headers)
        self.assertEqual(res.status_code, 200)
        submit_data = res.json()
        self.assertEqual(submit_data['score'], 100.0)
        self.assertTrue(submit_data['passed'])
        self.assertEqual(submit_data['attempt_number'], 1)

        # 3. Generate Certificate
        res = self.client.post(f'/api/v1/certificates/generate/{self.course.id}/', **student_headers)
        self.assertEqual(res.status_code, 201)
        self.assertIn('uuid', res.json())

        # 4. Student attempt 2 (fail this time)
        payload2 = {
            "answers": [
                {"question_id": q1.id, "choice_id": c2.id}
            ]
        }
        res = self.client.post(f'/api/v1/quizzes/{quiz.id}/submit/', data=json.dumps(payload2), content_type='application/json', **student_headers)
        self.assertEqual(res.status_code, 200)
        submit_data2 = res.json()
        self.assertEqual(submit_data2['score'], 0.0)
        self.assertFalse(submit_data2['passed'])
        self.assertEqual(submit_data2['attempt_number'], 2)

        # 5. Student attempt 3 (should block because attempt limit is 2)
        res = self.client.post(f'/api/v1/quizzes/{quiz.id}/submit/', data=json.dumps(payload), content_type='application/json', **student_headers)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['detail'], f"Anda sudah mencapai batas maksimal percobaan ({quiz.attempt_limit} kali).")
