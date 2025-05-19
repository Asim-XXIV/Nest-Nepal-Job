from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # simulate user think-time

    def on_start(self):
        # Login and store token for authenticated requests
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword"
        }
        response = self.client.post("/api/login/", json=login_data)
        if response.status_code == 200:
            token = response.json().get("access")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print("Login failed:", response.text)

    @task
    def view_profile(self):
        self.client.get("/api/profile/")

    @task
    def change_password(self):
        self.client.post("/api/change-password/", json={
            "old_password": "testpassword",
            "new_password": "newtestpassword",
            "confirm_password": "newtestpassword"
        })

    @task
    def list_institutions(self):
        self.client.get("/api/job/institutions/")

    @task
    def create_institution(self):
        self.client.post("/api/job/institutions/", json={
            "name": "Test Institution",
            "description": "A demo institution"
        })

    @task
    def list_jobs(self):
        self.client.get("/api/job/jobs/")

    @task
    def apply_for_job(self):
        self.client.post("/api/job/job-applications/", json={
            "job": 1,
            "cover_letter": "I am interested in this position."
        })

    @task
    def list_users_admin(self):
        self.client.get("/api/admin/users/")

    @task
    def view_user_detail_admin(self):
        self.client.get("/api/admin/users/1/")  # simulate viewing user with ID 1
