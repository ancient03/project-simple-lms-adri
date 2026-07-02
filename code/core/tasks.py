from celery import shared_task
import time
from datetime import datetime, timedelta

@shared_task
def add(x, y):
    """Task sederhana untuk demonstrasi."""
    time.sleep(5)
    return x + y

@shared_task
def send_enrollment_notification(user_id, course_id):
    """Kirim email notifikasi enrollment."""
    from courses.models import Course
    from django.contrib.auth.models import User

    user = User.objects.get(pk=user_id)
    course = Course.objects.get(pk=course_id)

    print(f"[{datetime.now()}] Sending email to {user.email}")
    print(f"Subject: Enrollment Confirmation")
    print(f"Body: Halo {user.first_name}, Anda berhasil mendaftar di course '{course.name}'.")

    return f"Notification sent to {user.email} for course {course.name}"

@shared_task
def send_welcome_email(user_id):
    """Kirim email selamat datang untuk pendaftar baru."""
    from django.contrib.auth.models import User

    user = User.objects.get(pk=user_id)
    print(f"[{datetime.now()}] Sending welcome email to {user.email}")
    print(f"Subject: Welcome to Simple LMS!")
    print(f"Body: Halo {user.first_name}, terima kasih telah bergabung dengan Simple LMS. Selamat belajar!")

    return f"Welcome email sent to {user.email}"

@shared_task
def generate_course_report(course_id):
    """Generate laporan statistik untuk sebuah course."""
    from courses.models import Course, CourseMember, CourseContent, Comment

    course = Course.objects.get(pk=course_id)
    members = CourseMember.objects.filter(course_id=course).count()
    contents = CourseContent.objects.filter(course_id=course).count()
    
    # Hitung semua komentar di setiap konten pada course tersebut
    comments = Comment.objects.filter(content__course_id=course).count()

    report = {
        "course": course.name,
        "total_members": members,
        "total_contents": contents,
        "total_comments": comments,
        "generated_at": str(datetime.now()),
    }

    return report

@shared_task
def generate_daily_stats():
    """
    Generate statistik harian LMS.
    Dijalankan otomatis setiap hari pukul 00:00 oleh Celery Beat.
    """
    from courses.models import Course, CourseMember
    from django.contrib.auth.models import User

    total_courses = Course.objects.count()
    total_users = User.objects.count()
    total_enrollments = CourseMember.objects.count()

    stats = {
        "date": str(datetime.now().date()),
        "total_courses": total_courses,
        "total_users": total_users,
        "total_enrollments": total_enrollments,
    }

    print(f"[Daily Stats] {stats}")

    return stats

@shared_task
def cleanup_expired_data():
    """
    Hapus data temporary atau log yang sudah lebih dari 30 hari.
    Dijalankan otomatis setiap hari pukul 02:00 oleh Celery Beat (saat ini diset 30 detik untuk testing).
    """
    threshold = datetime.now() - timedelta(days=30)
    print(f"[Cleanup] Expired data before {threshold} cleaned up")
    return {"cleaned_before": str(threshold)}

# ==================== Tugas 13: Error Handling & Chaining ====================

@shared_task(bind=True, max_retries=3)
def simulate_flaky_task(self):
    """
    Simulasi task yang error dan mencoba ulang (retry).
    Peluang gagal 70%.
    """
    import random
    
    # Simulasi memanggil third party API yang sering down
    is_success = random.random() > 0.7 
    
    if not is_success:
        print(f"[{datetime.now()}] Task Failed! Retrying... (Attempt {self.request.retries + 1}/{self.max_retries})")
        # Jika gagal, retry dalam 5 detik
        raise self.retry(countdown=5, exc=Exception("Third party API is down!"))
        
    print(f"[{datetime.now()}] Task Succeeded after {self.request.retries} retries!")
    return "Success!"

@shared_task
def send_email_with_report(report_data, email):
    """
    Task lanjutan dari generate_course_report (digunakan untuk Chaining).
    Menerima output report_data dari task sebelumnya, lalu mengirim email.
    """
    print(f"[{datetime.now()}] Mengirim Report ke {email}")
    print(f"Report: {report_data}")
    return f"Report for {report_data['course']} emailed to {email}"
