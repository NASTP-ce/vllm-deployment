from locust import HttpUser, task, between
import random, uuid

MODEL_ID = "/mnt/data/office_work/vllms_inference/Llama-3.2-3B-Instruct"

class ChatUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def chat_completion(self):
        # simulate a random user message
        user_message = random.choice([
            "Hello!", "How are you?", "Tell me a joke.", "What is AI?",
            "Generate a short poem.", "Explain quantum computing."
        ])

        payload = {
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": user_message}],
            "temperature": 0.7,
            "max_tokens": 128,
            "stream": False  # keep it false for load test (stream complicates parsing)
        }

        with self.client.post("/v1/chat/completions", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got {response.status_code}")
