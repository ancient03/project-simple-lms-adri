# tests/test_models.py

from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from courses.models import Course, CourseMember, ROLE_OPTIONS


class TestCourseModel(TestCase):
    """Test cases untuk model Course."""

    def setUp(self):
        """Setup data yang digunakan di setiap test."""
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='testpass123',
            email='teacher1@example.com'
        )

    def test_create_course(self):
        """Test membuat course baru."""
        course = Course.objects.create(
            name="Django for Beginners",
            description="Belajar Django dari nol",
            price=100000,
            teacher=self.teacher
        )
        self.assertEqual(course.name, "Django for Beginners")
        self.assertEqual(course.price, 100000)
        self.assertEqual(course.teacher, self.teacher)

    def test_course_str(self):
        """Test representasi string course."""
        course = Course.objects.create(
            name="Python Basics",
            teacher=self.teacher
        )
        self.assertEqual(str(course), "Python Basics")

    def test_course_default_price(self):
        """Test default price adalah 0."""
        course = Course.objects.create(
            name="Free Course",
            teacher=self.teacher
        )
        self.assertEqual(course.price, 0)

    def test_course_ordering(self):
        """Test course diurutkan berdasarkan created_at descending."""
        course1 = Course.objects.create(
            name="Course 1",
            teacher=self.teacher
        )
        course2 = Course.objects.create(
            name="Course 2",
            teacher=self.teacher
        )
        courses = Course.objects.all()
        # Course terbaru harus muncul pertama
        self.assertEqual(courses[0], course2)
        self.assertEqual(courses[1], course1)

    def test_course_teacher_relationship(self):
        """Test relasi course dengan teacher."""
        Course.objects.create(
            name="Course A",
            teacher=self.teacher
        )
        Course.objects.create(
            name="Course B",
            teacher=self.teacher
        )
        self.assertEqual(self.teacher.taught_courses.count(), 2)


class TestCourseMemberModel(TestCase):
    """Test cases untuk model CourseMember."""

    def setUp(self):
        """Setup data yang digunakan di setiap test."""
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='testpass123'
        )
        self.student = User.objects.create_user(
            username='student1',
            password='testpass123'
        )
        self.course = Course.objects.create(
            name="Django Course",
            price=150000,
            teacher=self.teacher
        )

    def test_create_course_member(self):
        """Test mendaftarkan member ke course."""
        member = CourseMember.objects.create(
            course=self.course,
            user=self.student,
            role='student'
        )
        self.assertEqual(member.course, self.course)
        self.assertEqual(member.user, self.student)
        self.assertEqual(member.role, 'student')

    def test_course_member_str(self):
        """Test representasi string course member."""
        member = CourseMember.objects.create(
            course=self.course,
            user=self.student,
            role='student'
        )
        expected = f"{self.student.username} - {self.course.name} (student)"
        self.assertEqual(str(member), expected)

    def test_default_role_is_student(self):
        """Test default role adalah student."""
        member = CourseMember.objects.create(
            course=self.course,
            user=self.student
        )
        self.assertEqual(member.role, 'student')

    def test_unique_together_constraint(self):
        """Test user tidak bisa join course yang sama dua kali."""
        CourseMember.objects.create(
            course=self.course,
            user=self.student,
            role='student'
        )
        with self.assertRaises(IntegrityError):
            CourseMember.objects.create(
                course=self.course,
                user=self.student,
                role='student'
            )

    def test_role_options(self):
        """Test role hanya bisa diisi dari pilihan yang tersedia."""
        valid_roles = [role[0] for role in ROLE_OPTIONS]
        self.assertIn('teacher', valid_roles)
        self.assertIn('student', valid_roles)
        self.assertIn('assistant', valid_roles)

    def test_cascade_delete_course(self):
        """Test member dihapus jika course dihapus."""
        CourseMember.objects.create(
            course=self.course,
            user=self.student,
            role='student'
        )
        self.assertEqual(CourseMember.objects.count(), 1)
        self.course.delete()
        self.assertEqual(CourseMember.objects.count(), 0)

    def test_cascade_delete_user(self):
        """Test member dihapus jika user dihapus."""
        CourseMember.objects.create(
            course=self.course,
            user=self.student,
            role='student'
        )
        self.assertEqual(CourseMember.objects.count(), 1)
        self.student.delete()
        self.assertEqual(CourseMember.objects.count(), 0)