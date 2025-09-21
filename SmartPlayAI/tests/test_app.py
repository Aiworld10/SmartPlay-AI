# test_app.py
# Tests for user registration and login functionality using FastAPI's TestClient
import uuid  # for generating unique usernames
# use the synchronous TestClient for testing FastAPI endpoints such as get, post


def test_register_user(client):
    """Test user registration with valid data."""
    unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/auth/register",
        data={
            "username": unique_username,
            "password1": "testpassword",
            "password2": "testpassword"
        }
    )
    assert response.status_code == 200
    # Check that the response contains HTML with success message
    assert f"Account created successfully for {unique_username}" in response.text
    assert "You can now log in" in response.text


def test_valid_login(client):
    """Test successful login flow."""
    # Create a unique user for this test
    unique_username = f"loginuser_{uuid.uuid4().hex[:8]}"
    register_response = client.post(
        "/auth/register",
        data={
            "username": unique_username,
            "password1": "testpassword",
            "password2": "testpassword"
        }
    )
    assert register_response.status_code == 200
    assert f"Account created successfully for {unique_username}" in register_response.text

    # Now test login
    response = client.post(
        "/auth/login",
        data={"username": unique_username, "password": "testpassword"}
    )
    assert response.status_code == 200
    # Check for redirect header for successful login
    assert "HX-Redirect" in response.headers
    assert response.headers["HX-Redirect"] == "/auth/theme-selection"
    # Check that access_token cookie is set
    assert "access_token" in response.cookies


def test_invalid_login(client):
    """Test login with invalid credentials."""
    # Use a username that definitely doesn't exist
    non_existent_user = f"nonexistent_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/auth/login",
        data={"username": non_existent_user, "password": "wrongpassword"}
    )
    assert response.status_code == 200  # HTML response, not 401
    # Check that the response contains error message
    assert "Incorrect username or password" in response.text
    assert "Please try again" in response.text


def test_register_password_mismatch(client):
    """Test registration with mismatched passwords."""
    unique_username = f"mismatchuser_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/auth/register",
        data={
            "username": unique_username,
            "password1": "password1",
            "password2": "password2"
        }
    )
    assert response.status_code == 200
    # Check that the response contains password mismatch error
    assert "Passwords do not match" in response.text


def test_register_short_password(client):
    """Test registration with password that's too short."""
    unique_username = f"shortuser_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/auth/register",
        data={
            "username": unique_username,
            "password1": "123",
            "password2": "123"
        }
    )
    assert response.status_code == 200
    # Check that the response contains password length error
    assert "Password must be at least 6 characters long" in response.text


def test_register_short_username(client):
    """Test registration with username that's too short."""
    response = client.post(
        "/auth/register",
        data={
            "username": "ab",
            "password1": "validpassword",
            "password2": "validpassword"
        }
    )
    assert response.status_code == 200
    # Check that the response contains username length error
    assert "Username must be at least 3 characters long" in response.text


def test_register_duplicate_username(client):
    """Test registration with duplicate username."""
    username = f"duplicate_{uuid.uuid4().hex[:8]}"

    # Register first user
    response1 = client.post(
        "/auth/register",
        data={
            "username": username,
            "password1": "password1",
            "password2": "password1"
        }
    )
    assert response1.status_code == 200
    assert f"Account created successfully for {username}" in response1.text

    # Try to register same username again
    response2 = client.post(
        "/auth/register",
        data={
            "username": username,
            "password1": "password2",
            "password2": "password2"
        }
    )
    assert response2.status_code == 200
    assert "Registration failed. Username might already exist" in response2.text


def test_get_theme_selection_unauthenticated(client):
    """Test accessing theme selection page without authentication."""
    response = client.get("/auth/theme-selection")
    assert response.status_code == 401  # Unauthorized
    # Check that the response contains login prompt
