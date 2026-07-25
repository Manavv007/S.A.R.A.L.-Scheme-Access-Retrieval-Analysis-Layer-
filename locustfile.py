import os
from locust import HttpUser, task, between

API_KEY = os.getenv("SARAL_API_KEY", "YOUR_KEY_HERE")

PROFILE = {
    "age": 28,
    "gender": "Male",
    "state": "Gujarat",
    "caste_category": "General",
    "occupation": "Student",
    "income": "200000",
    "language": "English",
}

class SaralUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.client.headers.update({"X-API-Key": API_KEY})

    @task(3)
    def recommend(self):
        self.client.post("/api/v1/recommend", json=PROFILE)

    @task(1)
    def chat(self):
        self.client.post(
            "/api/v1/chat",
            json={"query": "What schemes can I get?", "profile": PROFILE, "history": []},
        )