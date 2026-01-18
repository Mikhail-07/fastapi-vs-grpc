#!/usr/bin/env python3
"""
Python script to run all load test scenarios for both REST and gRPC
Cross-platform alternative to shell scripts
"""
import os
import sys
import subprocess
import importlib.util
import requests
import grpc

# Add gRPC service path
grpc_service_path = os.path.join(os.path.dirname(__file__), "rpc-grpc-protobuf", "glossary_grpc_project", "glossary_service")
sys.path.insert(0, grpc_service_path)

from glossary_pb2 import ListTermsRequest
from glossary_pb2_grpc import GlossaryServiceStub

# Create results directory
RESULTS_DIR = "load_test_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Test configurations
CONFIGS = [
    "locust_config_light",
    "locust_config_normal",
    "locust_config_stress",
    "locust_config_stability",
]


def load_config(config_name):
    """Load configuration from a config file"""
    spec = importlib.util.spec_from_file_location(config_name, f"{config_name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.USERS, module.SPAWN_RATE, module.DURATION, module.TEST_NAME


def run_test(config_name, user_class, protocol_name):
    """Run a single test scenario"""
    users, spawn_rate, duration, test_name = load_config(config_name)
    
    output_dir = os.path.join(RESULTS_DIR, f"{test_name}_{user_class}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Running {test_name} test for {user_class} ({protocol_name})...")
    print(f"  Users: {users}, Spawn rate: {spawn_rate}, Duration: {duration}")
    
    # Build locust command with environment variable for user class selection
    env = os.environ.copy()
    env["LOCUST_USER_CLASS"] = user_class
    
    # Build locust command
    cmd = [
        "locust",
        "--headless",
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", duration,
        "--host", "http://localhost:8000",
        "-f", "locustfile.py",
        "--html", os.path.join(output_dir, "report.html"),
        "--csv", os.path.join(output_dir, "results"),
        "--loglevel", "INFO"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        print(f"  Test completed. Results saved to {output_dir}")
        print()
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error running test: {e}")
        print(f"  stderr: {e.stderr}")
        print()
        return False


def check_servers():
    """Check if both servers are running"""
    print("Checking if servers are running...")
    
    # Check REST server
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        rest_ok = response.status_code == 200
    except:
        rest_ok = False
    
    # Check gRPC server
    try:
        channel = grpc.insecure_channel("localhost:50051")
        stub = GlossaryServiceStub(channel)
        request = ListTermsRequest()
        stub.ListTerms(request, timeout=2)
        channel.close()
        grpc_ok = True
    except:
        grpc_ok = False
    
    if not rest_ok:
        print("✗ REST API server (localhost:8000) is not running")
        print("  Start it with: cd fastapi-swagger && python main.py")
    
    if not grpc_ok:
        print("✗ gRPC server (localhost:50051) is not running")
        print("  Start it with: cd rpc-grpc-protobuf/glossary_grpc_project/glossary_service && python glossary.py")
    
    if rest_ok and grpc_ok:
        print("✓ Both servers are running")
        return True
    else:
        print("\nPlease start the servers before running load tests.")
        return False


def main():
    """Main function to run all tests"""
    # Check servers first
    if not check_servers():
        print("\nUse 'python check_servers.py' for detailed server status.")
        sys.exit(1)
    
    print("\nStarting load testing...")
    print(f"Results will be saved to: {RESULTS_DIR}")
    print()
    
    # Run tests for REST
    print("=== Testing REST API (FastAPI) ===")
    for config in CONFIGS:
        run_test(config, "RestUser", "REST")
    
    # Run tests for gRPC
    print("=== Testing gRPC API ===")
    for config in CONFIGS:
        run_test(config, "GrpcUser", "gRPC")
    
    print("All tests completed!")
    print("Run 'python compare_results.py' to analyze and compare results.")


if __name__ == "__main__":
    main()

