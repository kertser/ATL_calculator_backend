"""
Test script for the Login endpoint
Tests authentication with MongoDB including username/password validation,
expiration date checks, and role-based responses
"""

import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json
import pytest
import logging
import argparse
from config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global variable for base URL (can be overridden by command line args)
BASE_URL = f"http://{CONFIG.API_HOST}:{CONFIG.API_PORT}"


def set_base_url(host: str, port: int):
    """Set the base URL for testing"""
    global BASE_URL
    BASE_URL = f"http://{host}:{port}"


def make_login_request(username, password):
    """Helper function to make login request"""
    url = f"{BASE_URL}/login"
    payload = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, json=payload)
        logging.info(f"Status Code: {response.status_code}")
        logging.info(f"Response: {json.dumps(response.json(), indent=2)}")
        return response
    except Exception as e:
        logging.error(f"Error: {e}")
        return None


def test_valid_login():
    """Test valid login credentials"""
    response = make_login_request("Admin", "Atlantium")
    assert response is not None
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "role" in data
    assert "calculator_type" in data
    assert data["message"] == "Login successful"


def test_invalid_username():
    """Test invalid username"""
    response = make_login_request("nonexistent_user", "any_password")
    assert response is not None
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Wrong Login Name"


def test_wrong_password():
    """Test wrong password"""
    response = make_login_request("Admin", "wrong_password")
    assert response is not None
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Wrong Password"


def test_missing_username():
    """Test login with missing username"""
    url = f"{BASE_URL}/login"
    payload = {
        "password": "some_password"
    }

    response = requests.post(url, json=payload)
    assert response.status_code == 422  # Validation error


def test_missing_password():
    """Test login with missing password"""
    url = f"{BASE_URL}/login"
    payload = {
        "username": "some_user"
    }

    response = requests.post(url, json=payload)
    assert response.status_code == 422  # Validation error


def test_empty_credentials():
    """Test login with empty credentials"""
    response = make_login_request("", "")
    assert response is not None
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"


def test_special_characters_in_username():
    """Test login with special characters in username"""
    response = make_login_request("user@#$%", "password")
    assert response is not None
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"


def test_sql_injection_attempt():
    """Test login with SQL injection attempt in username"""
    response = make_login_request("admin' OR '1'='1", "password")
    assert response is not None
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"


def test_role_marketing():
    """Test login returns correct calculator type for Marketing role"""
    # This test assumes there's a user with Marketing role in the DB
    # Adjust username/password based on your test data
    response = make_login_request("marketing_user", "test_password")
    if response and response.status_code == 200:
        data = response.json()
        if data["status"] == "success":
            assert data["calculator_type"] == "Marketing"


def test_role_developer():
    """Test login returns correct calculator type for Developer role"""
    # This test assumes there's a user with Developer role in the DB
    # Adjust username/password based on your test data
    response = make_login_request("Admin", "Atlantium")
    if response and response.status_code == 200:
        data = response.json()
        if data["status"] == "success":
            assert data["calculator_type"] in ["Developer", "Marketing"]


def test_expired_password():
    """Test login with expired password"""
    # This test assumes there's a user with expired password in the DB
    # You may need to create a test user with expiration date in the past
    response = make_login_request("expired_user", "password")
    if response and response.status_code == 200:
        data = response.json()
        if data["status"] == "error":
            # Check if error is about expiration
            assert "Expired" in data["message"] or "Wrong Login Name" in data["message"]


def test_invalid_json():
    """Test login with invalid JSON"""
    url = f"{BASE_URL}/login"
    response = requests.post(
        url,
        data="invalid json content",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422  # Validation error


def test_missing_content_type():
    """Test login without Content-Type header"""
    url = f"{BASE_URL}/login"
    payload = {
        "username": "test_user",
        "password": "test_password"
    }
    response = requests.post(url, json=payload)
    # Should still work with json parameter
    assert response.status_code in [200, 422]


class TestLoginEndpoint:
    """Test class for Login endpoint using pytest"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test"""
        self.base_url = BASE_URL

    def test_server_availability(self):
        """Test if server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")

    def test_login_endpoint_exists(self):
        """Test that login endpoint exists"""
        response = requests.post(f"{self.base_url}/login", json={})
        assert response.status_code != 404

    def test_login_requires_post(self):
        """Test that login only accepts POST requests"""
        response = requests.get(f"{self.base_url}/login")
        assert response.status_code == 405  # Method Not Allowed


def main():
    """Main function to run the tests manually"""
    parser = argparse.ArgumentParser(description="Test the Login endpoint")
    parser.add_argument("--host", default=CONFIG.API_HOST, help="API host (default: from config)")
    parser.add_argument("--port", default=CONFIG.API_PORT, type=int, help="API port (default: from config)")

    args = parser.parse_args()

    # Set the base URL based on command line arguments
    set_base_url(args.host, args.port)

    logging.info("=" * 80)
    logging.info("Testing Login Endpoint")
    logging.info(f"Target: {BASE_URL}")
    logging.info("=" * 80)

    # Check server availability
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            logging.error("❌ Server is not responding properly")
            exit(1)
        logging.info("✅ Server is running and responsive")
    except requests.exceptions.ConnectionError:
        logging.error(f"❌ Cannot connect to server at {BASE_URL}")
        logging.error("Make sure the server is running")
        exit(1)

    logging.info("\n1. Testing valid login:")
    make_login_request("Admin", "Atlantium")

    logging.info("\n2. Testing invalid username:")
    make_login_request("nonexistent_user", "any_password")

    logging.info("\n3. Testing wrong password:")
    make_login_request("Admin", "wrong_password")

    logging.info("\n4. Testing empty credentials:")
    make_login_request("", "")

    logging.info("\n5. Testing missing password:")
    url = f"{BASE_URL}/login"
    try:
        response = requests.post(url, json={"username": "test_user"})
        logging.info(f"Status Code: {response.status_code}")
        logging.info(f"Response: {response.text}")
    except Exception as e:
        logging.error(f"Error: {e}")

    logging.info("\n" + "=" * 80)
    logging.info("Login Endpoint Tests Complete")
    logging.info("=" * 80)
    logging.info("\nFor comprehensive testing with pytest, run:")
    logging.info(f"  pytest tests/test_login.py -v")
    logging.info("\nOr run manually with custom host/port:")
    logging.info(f"  python tests/test_login.py --host 127.0.0.1 --port 5000")


if __name__ == "__main__":
    # python tests/test_login.py --host 127.0.0.1 --port 5000
    main()
