import pytest


@pytest.fixture
def user_seeds():
    """Gets a list of two users for every possible role 

    Returns:
        list of (dict of (str, str)): list of users
    """
    return [
        {'username': 'admin1', 'password': 'password', 'role': 'admin'},
        {'username': 'admin2', 'password': 'password', 'role': 'admin'},
        {'username': 'maintainer1', 'password': 'password', 'role': 'maintainer'},
        {'username': 'maintainer2', 'password': 'password', 'role': 'maintainer'},
        {'username': 'planner1', 'password': 'password', 'role': 'planner'},
        {'username': 'planner2', 'password': 'password', 'role': 'planner'},
    ]


@pytest.fixture
def unexisting_user():
    """Gets an user that is not included in user_seeds

    Returns:
        dict of (str, str): the unexisting user
    """
    return {'username': 'username', 'password': 'password', 'role': 'admin'}


@pytest.fixture(autouse=True)
def setup(app, user_seeds):
    """Before each test it drops every table and recreates them. 
    Then it creates an user for every dictionary present in user_seeds

    Returns:
        boolean: the return status
    """
    with app.app_context():
        from db import db
        db.drop_all()
        db.create_all()
        from models.user import UserModel
        for seed in user_seeds:
            user = UserModel(**seed)
            user.save_to_db()
    return True


@pytest.fixture
def admin_user(user_seeds):
    """ Finds the first admin user among the user seeds

    Returns:
        dict of (str, str): The admin user
    """
    return next(user for user in user_seeds if user["role"] == "admin")


@pytest.fixture
def admin_client(client, admin_user):
    """ Creates a test client with preset admin authorization headers taken from the login endpoint 

    Returns:
        FlaskClient: The test client
    """
    res = client.post(
        "/login", data=admin_user)
    access_token = res.get_json()["access_token"]
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + access_token
    return client


def test_unexisting_user_not_in_user_seeds(user_seeds, unexisting_user):
    """ unexisting_user's username should not be included among user_seeds usernames """
    filtered_users = list(filter(lambda user: user['username'] ==
                                 unexisting_user['username'], user_seeds))
    assert len(filtered_users) == 0


def test_get_user_success(admin_client, user_seeds):
    """ Tests a succesful retrival of a single user """
    test_user = user_seeds[0]
    res = admin_client.get(f"/user/{test_user['username']}")
    assert res.status_code == 200
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_get_user_not_found(admin_client, unexisting_user):
    """ Tests a failed retrival of a single user by using an username for an user that does not exist """
    test_user = unexisting_user
    res = admin_client.get(f"/user/{test_user['username']}")
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()


def test_get_users_success(admin_client, user_seeds):
    """ Tests a succesful retrival of a page of users """
    test_current_page = 1
    test_page_size = len(user_seeds) - 1

    res = admin_client.get(
        f"/users?current_page={test_current_page}&page_size={test_page_size}")

    assert res.status_code == 200
    assert len(res.get_json()['rows']) <= test_page_size
    assert res.get_json()['meta']['count'] == len(user_seeds)
    assert res.get_json()['meta']['current_page'] == test_current_page
    assert res.get_json()['meta']['page_size'] == test_page_size

    import math
    expected_page_count = math.ceil(len(user_seeds) / test_page_size)
    assert res.get_json()['meta']['page_count'] == expected_page_count


def test_get_users_page_not_found(admin_client, user_seeds):
    """ Tests a failed retrival of a page of users using a non-existing current_page """
    test_page_size = 5
    import math
    test_page_count = math.ceil(len(user_seeds) / test_page_size)
    test_current_page = test_page_count + 1
    res = admin_client.get(
        f"/users?current_page={test_current_page}&page_size={test_page_size}")

    assert res.status_code == 404
    assert "message" in res.get_json().keys()


def test_post_user_success(admin_client, unexisting_user):
    """ Tests a succesful creation of an user """
    test_user = unexisting_user
    res = admin_client.post('/user', data=test_user)

    assert res.status_code == 201
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_post_user_already_exists(admin_client, user_seeds):
    """ Tests a failed creation of an user using an username for an user that already exists """
    test_user = user_seeds[0]
    res = admin_client.post('/user', data=test_user)

    assert res.status_code == 400
    assert 'message' in res.get_json().keys()


def test_post_user_missing_username(admin_client):
    """ Tests a failed creation of an user by omitting the username """
    test_user_without_username = {'password': 'password', 'role': 'admin'}
    res = admin_client.post('/user', data=test_user_without_username)
    assert res.status_code == 400
    assert 'message' in res.get_json().keys()
    assert 'username' in res.get_json()['message'].keys()


def test_post_user_missing_password(admin_client):
    """ Tests a failed creation of an user by omitting the password """
    test_user_without_password = {'username': 'username', 'role': 'admin'}
    res = admin_client.post('/user', data=test_user_without_password)
    assert res.status_code == 400
    assert 'message' in res.get_json().keys()
    assert 'password' in res.get_json()['message'].keys()


def test_post_user_missing_role(admin_client):
    """ Tests a failed creation of an user by omitting the role """
    test_user_without_role = {'username': 'username', 'password': 'password'}
    res = admin_client.post('/user', data=test_user_without_role)
    assert res.status_code == 400
    assert 'message' in res.get_json().keys()
    assert 'role' in res.get_json()['message'].keys()


def test_put_user_success(admin_client, unexisting_user, user_seeds):
    """ Tests a successful edit of an user  """
    test_user = unexisting_user
    test_user.pop('password')
    test_old_user = user_seeds[0]

    res = admin_client.put(
        f"/user/{test_old_user['username']}", data=test_user)
    assert res.status_code == 200
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_put_user_username_success(admin_client, unexisting_user, user_seeds):
    """ Tests a succesful edit of an user by only editing his username """
    test_user = {'username': unexisting_user['username']}
    test_old_user = user_seeds[0]

    res = admin_client.put(
        f"/user/{test_old_user['username']}", data=test_user)
    assert res.status_code == 200
    assert res.get_json()['username'] == test_user['username']
    assert res.get_json()['role'] == test_old_user['role']
    assert 'password' not in res.get_json().keys()


def test_put_user_role_success(admin_client, unexisting_user, user_seeds):
    """ Tests a succesful edit of an user by only editing his role """
    test_user = {'role': unexisting_user['role']}
    test_old_user = user_seeds[0]

    res = admin_client.put(
        f"/user/{test_old_user['username']}", data=test_user)
    assert res.status_code == 200
    assert res.get_json()['username'] == test_old_user['username']
    assert res.get_json()['role'] == test_user['role']
    assert 'password' not in res.get_json().keys()


def test_put_user_not_found(admin_client, unexisting_user):
    """ Tests a failed edit of an user by using and username for an user that does not exist """
    test_user = unexisting_user
    res = admin_client.put(f"/user/{test_user['username']}", data={})
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()


def test_put_user_new_username_already_existing(admin_client, user_seeds):
    """ Tests a failed edit of an user by using a new username for an user that already exists """
    test_user = user_seeds[0]
    user_with_username_already_existing = user_seeds[1]
    res = admin_client.put(
        f"/user/{test_user['username']}", data=user_with_username_already_existing)
    assert res.status_code == 400
    assert 'message' in res.get_json().keys()


def test_delete_user_success(admin_client, user_seeds):
    """ Tests a successful deletion of an user """
    test_user = user_seeds[0]
    res = admin_client.delete(f"/user/{test_user['username']}")
    assert res.status_code == 200
    assert 'message' in res.get_json().keys()


def test_delete_user_not_found(admin_client, unexisting_user):
    """ Tests a failed deletion of an user by using an username for an user that does not exist """
    test_user = unexisting_user
    res = admin_client.delete(f"/user/{test_user['username']}")
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()
