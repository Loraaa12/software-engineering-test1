from locust import HttpUser, task, between
import os

class FileStorageUser(HttpUser):
    wait_time = between(1, 3)  # интервал между заявките

    @task
    def get_root(self):
        self.client.get("/")

    @task
    def health_check(self):
        self.client.get("/health")

    @task
    def upload_file(self):
        # качване на файл test.txt
        files = {
            "file": ("test.txt", b"locust load test", "text/plain")
        }
        self.client.post("/files", files=files)

    @task
    def get_metrics(self):
        self.client.get("/metrics")
