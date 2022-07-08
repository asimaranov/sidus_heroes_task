import datetime

from fastapi.testclient import TestClient

from api import app
import random
import string

random.seed(datetime.datetime.now().microsecond)


def gen_user():
    return {
        "username": ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
        "email": ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '@gmail.com',
        "password": ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    }


TEST_USER = gen_user()
TEST_UPDATED_USER = gen_user()


def test_user_creation():
    with TestClient(app) as client:
        response = client.post("/create_user", json=TEST_USER)
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json['id'] > 0


def test_that_username_cant_be_retaken():
    with TestClient(app) as client:
        response = client.post("/create_user", json=TEST_USER)
    assert response.json()['status_code'] == 409


def test_user_correct_auth():
    with TestClient(app) as client:
        response = client.post("/token", json=TEST_USER, data={
            'username': TEST_USER['username'],
            'password': TEST_USER['password'],
        })
    assert response.status_code == 200
    assert response.json()['token_type'] == 'bearer'


def test_user_incorrect_auth_invalid_password():
    with TestClient(app) as client:
        response = client.post("/token", json=TEST_USER, data={
            'username': TEST_USER['username'],
            'password': TEST_USER['password'] + 'a',
        })
    assert response.status_code == 400
    assert response.json()['detail'] == 'Incorrect password'


def test_user_incorrect_auth_invalid_username():
    with TestClient(app) as client:
        response = client.post("/token", json=TEST_USER, data={
            'username': TEST_USER['username'] + 'a',
            'password': TEST_USER['password'],
        })
    assert response.status_code == 400
    assert response.json()['detail'] == "User doesn't exists"


def test_user_update():
    with TestClient(app) as client:
        auth_response = client.post("/token", json=TEST_USER, data={
            'username': TEST_USER['username'],
            'password': TEST_USER['password'],
        })
        assert auth_response.status_code == 200
        token = auth_response.json()['access_token']
        update_user_response = client.post("/update_user",
                                           json={'email': TEST_UPDATED_USER['email']},
                                           headers={
                                               f'Authorization': f'Bearer {token}',
                                               'Content-Type': 'application/json'}
                                           )
        assert update_user_response.status_code == 200
        assert update_user_response.json()['email'] == TEST_UPDATED_USER['email']


def test_get_user():
    with TestClient(app) as client:
        auth_response = client.get("/get_user")
        assert auth_response.status_code == 200


def test_get_user_caching():
    with TestClient(app) as client:
        auth_response = client.get("/get_user")
        assert auth_response.status_code == 200
        assert auth_response.json()['cached'] is True


def test_user_update_drops_cache():
    with TestClient(app) as client:
        auth_response = client.post("/token", json=TEST_USER, data={
            'username': TEST_USER['username'],
            'password': TEST_USER['password'],
        })

        token = auth_response.json()['access_token']
        client.post("/update_user",
                    json={'email': TEST_UPDATED_USER['email']},
                    headers={
                        f'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'}
                    )

        auth_response = client.get("/get_user")
        assert auth_response.status_code == 200
        assert auth_response.json()['cached'] is False
