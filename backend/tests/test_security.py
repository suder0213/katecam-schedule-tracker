from app.core.security import hash_password, verify_password


def test_hash_password_is_salted():
    hashed_1 = hash_password("password123")
    hashed_2 = hash_password("password123")

    assert hashed_1 != hashed_2


def test_verify_password_correct():
    hashed = hash_password("password123")

    assert verify_password("password123", hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("password123")

    assert verify_password("wrong-password", hashed) is False
