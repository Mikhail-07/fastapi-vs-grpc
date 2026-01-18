"""
Locust load testing file for comparing FastAPI REST and gRPC performance
"""
import random
import sys
import os
import time
from locust import HttpUser, User, task, between, events
import grpc
import requests

# Add gRPC service path to sys.path
grpc_service_path = os.path.join(os.path.dirname(__file__), "rpc-grpc-protobuf", "glossary_grpc_project", "glossary_service")
sys.path.insert(0, grpc_service_path)

from glossary_pb2 import (
    GetTermRequest,
    ListTermsRequest,
    SearchTermsRequest,
    AddTermRequest,
)
from glossary_pb2_grpc import GlossaryServiceStub

# Sample keywords from the database
SAMPLE_KEYWORDS = [
    "WebGL", "WebGPU", "Vertex Shader", "Fragment Shader", "GPU",
    "Shader", "Buffer", "Texture", "Render Pipeline", "Uniform",
    "VBO", "FBO", "GLSL", "WGSL", "Compute Shader"
]

# Search queries for testing
SEARCH_QUERIES = ["Shader", "GPU", "Web", "Buffer", "Render", "Texture", "GL", "Pipeline"]

# REST API base URL
REST_BASE_URL = "http://localhost:8000"

# gRPC server address
GRPC_SERVER = "localhost:50051"

# Select user class based on environment variable
# Set LOCUST_USER_CLASS to "RestUser" or "GrpcUser" to test specific protocol
USER_CLASS = os.getenv("LOCUST_USER_CLASS", "RestUser")


# Conditionally define user classes based on environment variable
if USER_CLASS in ["RestUser", "all"]:
    class RestUser(HttpUser):
        """Locust user class for testing FastAPI REST API"""
        
        host = REST_BASE_URL
        wait_time = between(1, 3)  # Wait 1-3 seconds between requests
        
        def on_start(self):
            """Called when a user starts"""
            self.keywords = SAMPLE_KEYWORDS.copy()
            random.shuffle(self.keywords)
        
        @task(6)
        def get_all_terms(self):
            """GET /terms - Light operation, returns all terms"""
            with self.client.get("/terms", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Status code: {response.status_code}")
        
        @task(6)
        def get_term_by_keyword(self):
            """GET /terms/{keyword} - Light operation, single term lookup"""
            keyword = random.choice(self.keywords)
            with self.client.get(f"/terms/{keyword}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # 404 is expected for some random keywords
                else:
                    response.failure(f"Status code: {response.status_code}")
        
        @task(3)
        def search_terms(self):
            """GET /terms/search?q={query} - Medium operation, LIKE query"""
            query = random.choice(SEARCH_QUERIES)
            with self.client.get(f"/terms/search?q={query}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Status code: {response.status_code}")
        
        @task(1)
        def create_term(self):
            """POST /terms - Medium operation, database write"""
            # Generate unique keyword to avoid conflicts
            unique_keyword = f"TestTerm_{random.randint(10000, 99999)}"
            payload = {
                "keyword": unique_keyword,
                "description": f"Test description for {unique_keyword}"
            }
            with self.client.post("/terms", json=payload, catch_response=True) as response:
                if response.status_code == 201:
                    response.success()
                elif response.status_code == 400:
                    # Term already exists, this is acceptable
                    response.success()
                else:
                    response.failure(f"Status code: {response.status_code}")


if USER_CLASS in ["GrpcUser", "all"]:
    class GrpcUser(User):
        """Locust user class for testing gRPC API"""
        
        wait_time = between(1, 3)  # Wait 1-3 seconds between requests
        
        def on_start(self):
            """Called when a user starts"""
            # Create gRPC channel and stub
            self.channel = grpc.insecure_channel(GRPC_SERVER)
            self.stub = GlossaryServiceStub(self.channel)
            self.keywords = SAMPLE_KEYWORDS.copy()
            random.shuffle(self.keywords)
        
        def on_stop(self):
            """Called when a user stops"""
            if hasattr(self, 'channel'):
                self.channel.close()
        
        @task(6)
        def list_terms(self):
            """ListTerms - Light operation, returns all terms"""
            start_time = time.time()
            try:
                request = ListTermsRequest()
                response = self.stub.ListTerms(request, timeout=10)
                response_time = int((time.time() - start_time) * 1000)
                events.request.fire(
                    request_type="gRPC",
                    name="ListTerms",
                    response_time=response_time,
                    response_length=0,
                    exception=None,
                )
            except grpc.RpcError as e:
                response_time = int((time.time() - start_time) * 1000)
                events.request.fire(
                    request_type="gRPC",
                    name="ListTerms",
                    response_time=response_time,
                    response_length=0,
                    exception=e,
                )
        
        @task(6)
        def get_term(self):
            """GetTerm - Light operation, single term lookup"""
            start_time = time.time()
            try:
                keyword = random.choice(self.keywords)
                request = GetTermRequest(keyword=keyword)
                response = self.stub.GetTerm(request, timeout=10)
                response_time = int((time.time() - start_time) * 1000)
                events.request.fire(
                    request_type="gRPC",
                    name="GetTerm",
                    response_time=response_time,
                    response_length=0,
                    exception=None,
                )
            except grpc.RpcError as e:
                response_time = int((time.time() - start_time) * 1000)
                # NOT_FOUND is acceptable for random keywords
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    events.request.fire(
                        request_type="gRPC",
                        name="GetTerm",
                        response_time=response_time,
                        response_length=0,
                        exception=None,
                    )
                else:
                    events.request.fire(
                        request_type="gRPC",
                        name="GetTerm",
                        response_time=response_time,
                        response_length=0,
                        exception=e,
                    )
        
        @task(3)
        def search_terms(self):
            """SearchTerms - Medium operation, LIKE query"""
            start_time = time.time()
            try:
                query = random.choice(SEARCH_QUERIES)
                request = SearchTermsRequest(query=query)
                response = self.stub.SearchTerms(request, timeout=10)
                response_time = int((time.time() - start_time) * 1000)
                events.request.fire(
                    request_type="gRPC",
                    name="SearchTerms",
                    response_time=response_time,
                    response_length=0,
                    exception=None,
                )
            except grpc.RpcError as e:
                response_time = int((time.time() - start_time) * 1000)
                events.request.fire(
                    request_type="gRPC",
                    name="SearchTerms",
                    response_time=response_time,
                    response_length=0,
                    exception=e,
                )
        
        @task(1)
        def add_term(self):
            """AddTerm - Medium operation, database write"""
            start_time = time.time()
            try:
                # Generate unique keyword to avoid conflicts
                unique_keyword = f"TestTerm_{random.randint(10000, 99999)}"
                request = AddTermRequest(
                    keyword=unique_keyword,
                    description=f"Test description for {unique_keyword}"
                )
                response = self.stub.AddTerm(request, timeout=10)
                response_time = int((time.time() - start_time) * 1000)
                events.request.fire(
                    request_type="gRPC",
                    name="AddTerm",
                    response_time=response_time,
                    response_length=0,
                    exception=None,
                )
            except grpc.RpcError as e:
                response_time = int((time.time() - start_time) * 1000)
                # ALREADY_EXISTS is acceptable
                if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                    events.request.fire(
                        request_type="gRPC",
                        name="AddTerm",
                        response_time=response_time,
                        response_length=0,
                        exception=None,
                    )
                else:
                    events.request.fire(
                        request_type="gRPC",
                        name="AddTerm",
                        response_time=response_time,
                        response_length=0,
                        exception=e,
                    )

