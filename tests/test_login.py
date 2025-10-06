import requests
import json
import pytest

# Server URL
BASE_URL = "http://localhost:5000"


def make_login_request(username, password):
    """Helper function to make login request"""
    url = f"{BASE_URL}/login"
    payload = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_valid_login():
    """Test valid login credentials"""
    response = make_login_request("Admin", "Atlantium")
    assert response is not None
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_invalid_username():
    """Test invalid username"""
    response = make_login_request("invalid_user", "any_password")
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


if __name__ == "__main__":
    print("=== Testing Login Endpoint ===")

    print("\n1. Testing valid login:")
    make_login_request("Admin", "password")

    print("\n2. Testing invalid username:")
    make_login_request("invalid_user", "any_password")

    print("\n3. Testing wrong password:")
    make_login_request("Admin", "wrong_password")
