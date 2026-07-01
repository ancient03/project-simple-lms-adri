# locustfile.py
#
# How auth works in this load test:
#   1. GET /admin/login/ → Django sets csrftoken cookie (CSRF-protected view)
#   2. POST /api/v1/auth/login + X-CSRFToken header → Django creates a real
#      session (sessionid cookie) so SessionAuth accepts all follow-up requests
#   3. Subsequent requests carry both sessionid + csrftoken cookies automatically
#      (requests.Session handles cookies); POST requests include X-CSRFToken header

from locust import HttpUser, task, between


class LMSUser(HttpUser):
    """Simulasi user yang mengakses Simple LMS."""

    wait_time = between(1, 3)
    csrf_token = ""

    def on_start(self):
        """Login dan dapatkan session + CSRF cookie."""
        # Step 1: GET any Django-CSRF-protected page to receive the csrftoken cookie.
        # /admin/login/ is not csrf_exempt, so Django middleware sets the cookie.
        self.client.get("/admin/login/")
        self.csrf_token = self.client.cookies.get("csrftoken", "")

        # Step 2: Login — API creates a real Django session (sessionid cookie).
        # The session is then carried automatically by the requests.Session.
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "teacher1", "password": "teacherpass123"},
            headers={"X-CSRFToken": self.csrf_token},
        )
        if response.status_code == 200:
            # Django may rotate the CSRF token after login
            self.csrf_token = self.client.cookies.get("csrftoken", self.csrf_token)
        else:
            print(f"Login failed: {response.status_code} - {response.text}")

    def post_headers(self):
        """Headers untuk POST/PATCH/DELETE — harus menyertakan X-CSRFToken."""
        return {
            "Content-Type": "application/json",
            "X-CSRFToken": self.csrf_token,
        }

    # ── Read tasks (no CSRF needed for GET) ──────────────────────────────────

    @task(3)
    def get_courses(self):
        """Task: Mengambil daftar course. Weight 3 = paling sering."""
        self.client.get("/api/v1/courses/", name="GET /api/v1/courses/")

    @task(2)
    def get_course_detail(self):
        """Task: Mengambil detail course. Weight 2."""
        self.client.get("/api/v1/courses/1", name="GET /api/v1/courses/{id}")

    # ── Write tasks ───────────────────────────────────────────────────────────

    @task(1)
    def post_comment(self):
        """
        Task: Membuat komentar baru. Weight 1.
        Note: endpoint ini belum diimplementasikan → expect 404.
        """
        self.client.post(
            "/api/v1/contents/1/comments/",
            json={"comment": "Test comment from load test"},
            headers=self.post_headers(),
            name="POST /api/v1/contents/{id}/comments/",
        )

    @task(1)
    def delete_comment(self):
        """
        Task: Buat lalu hapus komentar. Weight 1.
        Note: endpoint ini belum diimplementasikan → expect 404.
        """
        create_response = self.client.post(
            "/api/v1/contents/1/comments/",
            json={"comment": "Comment to delete"},
            headers=self.post_headers(),
            name="POST /api/v1/contents/{id}/comments/ (create for delete)",
        )
        if create_response.status_code == 201:
            comment_id = create_response.json().get("id")
            if comment_id:
                self.client.delete(
                    f"/api/v1/comments/{comment_id}/",
                    headers=self.post_headers(),
                    name="DELETE /api/v1/comments/{id}/",
                )