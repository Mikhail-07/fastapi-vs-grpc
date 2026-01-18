#!/usr/bin/env python3
"""
Script to check if both REST and gRPC servers are running before load testing
"""
import sys
import requests
import grpc
import os

# Add gRPC service path
grpc_service_path = os.path.join(os.path.dirname(__file__), "rpc-grpc-protobuf", "glossary_grpc_project", "glossary_service")
sys.path.insert(0, grpc_service_path)

from glossary_pb2 import ListTermsRequest
from glossary_pb2_grpc import GlossaryServiceStub

REST_URL = "http://localhost:8000"
GRPC_SERVER = "localhost:50051"


def check_rest_server():
    """Check if REST API server is running"""
    try:
        response = requests.get(f"{REST_URL}/", timeout=2)
        if response.status_code == 200:
            print("✓ REST API server is running")
            return True
        else:
            print(f"✗ REST API server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ REST API server is not accessible: {e}")
        return False


def check_grpc_server():
    """Check if gRPC server is running"""
    try:
        channel = grpc.insecure_channel(GRPC_SERVER)
        stub = GlossaryServiceStub(channel)
        request = ListTermsRequest()
        # Try to call with short timeout
        response = stub.ListTerms(request, timeout=2)
        channel.close()
        print("✓ gRPC server is running")
        return True
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            print("✗ gRPC server is not responding (timeout)")
        else:
            print(f"✗ gRPC server error: {e}")
        return False
    except Exception as e:
        print(f"✗ gRPC server is not accessible: {e}")
        return False


def main():
    """Main function"""
    print("Checking servers...")
    print()
    
    rest_ok = check_rest_server()
    grpc_ok = check_grpc_server()
    
    print()
    if rest_ok and grpc_ok:
        print("✓ Both servers are ready for load testing!")
        return 0
    else:
        print("✗ Some servers are not ready. Please start them before running load tests.")
        print()
        print("To start servers:")
        print("  REST: cd fastapi-swagger && python main.py")
        print("  gRPC: cd rpc-grpc-protobuf/glossary_grpc_project/glossary_service && python glossary.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())

