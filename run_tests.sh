#!/bin/bash

# Script to run all load test scenarios for both REST and gRPC

# Create results directory
RESULTS_DIR="load_test_results"
mkdir -p "$RESULTS_DIR"

# Test configurations
CONFIGS=("locust_config_light.py" "locust_config_normal.py" "locust_config_stress.py" "locust_config_stability.py")

echo "Starting load testing..."
echo "Results will be saved to: $RESULTS_DIR"
echo ""

# Function to run a test
run_test() {
    local config_file=$1
    local user_class=$2
    local test_name=$3
    
    # Import config
    source <(python3 -c "
import sys
sys.path.insert(0, '.')
from $config_file import USERS, SPAWN_RATE, DURATION, TEST_NAME
print(f'USERS={USERS}')
print(f'SPAWN_RATE={SPAWN_RATE}')
print(f'DURATION={DURATION}')
print(f'TEST_NAME={TEST_NAME}')
")
    
    local output_dir="$RESULTS_DIR/${TEST_NAME}_${user_class}"
    mkdir -p "$output_dir"
    
    echo "Running $test_name test for $user_class..."
    echo "  Users: $USERS, Spawn rate: $SPAWN_RATE, Duration: $DURATION"
    
    locust \
        --headless \
        --users $USERS \
        --spawn-rate $SPAWN_RATE \
        --run-time $DURATION \
        --host http://localhost:8000 \
        -f locustfile.py \
        -u $user_class \
        --html "$output_dir/report.html" \
        --csv "$output_dir/results" \
        --loglevel INFO
    
    echo "  Test completed. Results saved to $output_dir"
    echo ""
}

# Run tests for REST
echo "=== Testing REST API (FastAPI) ==="
for config in "${CONFIGS[@]}"; do
    run_test "$config" "RestUser" "REST"
done

# Run tests for gRPC
echo "=== Testing gRPC API ==="
for config in "${CONFIGS[@]}"; do
    run_test "$config" "GrpcUser" "gRPC"
done

echo "All tests completed!"
echo "Run 'python compare_results.py' to analyze and compare results."

