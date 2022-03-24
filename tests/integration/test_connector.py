import pytest

def test_connector_list(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/connector/')
    assert response.status_code == 200
