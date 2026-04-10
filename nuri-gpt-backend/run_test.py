from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

# We will just run pytest normally and print the failed output of the test using a python runner
import subprocess
try:
    print(subprocess.check_output(["uv", "run", "pytest", "tests/test_generate.py", "-k", "test_generate_log_success", "--tb=short"], stderr=subprocess.STDOUT).decode())
except subprocess.CalledProcessError as e:
    print(e.output.decode())
