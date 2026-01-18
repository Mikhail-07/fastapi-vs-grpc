@echo off
REM Script to run all load test scenarios for both REST and gRPC

REM Create results directory
set RESULTS_DIR=load_test_results
if not exist "%RESULTS_DIR%" mkdir "%RESULTS_DIR%"

echo Starting load testing...
echo Results will be saved to: %RESULTS_DIR%
echo.

REM Test configurations
set CONFIGS=locust_config_light.py locust_config_normal.py locust_config_stress.py locust_config_stability.py

REM Function to run a test
:run_test
set config_file=%~1
set user_class=%~2
set test_name=%~3

REM Extract config values using Python
for /f "tokens=*" %%i in ('python -c "import sys; sys.path.insert(0, '.'); from %config_file% import USERS, SPAWN_RATE, DURATION, TEST_NAME; print('USERS=' + str(USERS)); print('SPAWN_RATE=' + str(SPAWN_RATE)); print('DURATION=' + DURATION); print('TEST_NAME=' + TEST_NAME)"') do set %%i

set output_dir=%RESULTS_DIR%\%TEST_NAME%_%user_class%
if not exist "%output_dir%" mkdir "%output_dir%"

echo Running %test_name% test for %user_class%...
echo   Users: %USERS%, Spawn rate: %SPAWN_RATE%, Duration: %DURATION%

locust --headless --users %USERS% --spawn-rate %SPAWN_RATE% --run-time %DURATION% --host http://localhost:8000 -f locustfile.py -u %user_class% --html "%output_dir%\report.html" --csv "%output_dir%\results" --loglevel INFO

echo   Test completed. Results saved to %output_dir%
echo.
goto :eof

REM Run tests for REST
echo === Testing REST API (FastAPI) ===
for %%c in (%CONFIGS%) do call :run_test %%c RestUser REST

REM Run tests for gRPC
echo === Testing gRPC API ===
for %%c in (%CONFIGS%) do call :run_test %%c GrpcUser gRPC

echo All tests completed!
echo Run 'python compare_results.py' to analyze and compare results.

pause

