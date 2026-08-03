from app.models.user import UserPermission


def test_dev_can_create_notion_text(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.post(
        "/crawl-texts",
        json={"source": "notion", "raw_text": "이번 주 과제는 금요일까지 제출입니다."},
        headers=auth_header(dev),
    )

    assert resp.status_code == 201
    assert resp.json()["source"] == "notion"
    assert resp.json()["channel"] is None


def test_dev_can_create_discord_text_with_channel(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.post(
        "/crawl-texts",
        json={"source": "discord", "channel": "공지방", "raw_text": "다음주 화요일 스터디 모임"},
        headers=auth_header(dev),
    )

    assert resp.status_code == 201
    assert resp.json()["channel"] == "공지방"


def test_discord_without_channel_rejected(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.post(
        "/crawl-texts",
        json={"source": "discord", "raw_text": "x"},
        headers=auth_header(dev),
    )

    assert resp.status_code == 422


def test_notion_with_channel_rejected(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.post(
        "/crawl-texts",
        json={"source": "notion", "channel": "공지방", "raw_text": "x"},
        headers=auth_header(dev),
    )

    assert resp.status_code == 422


def test_student_can_create_crawl_text(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.post(
        "/crawl-texts",
        json={"source": "notion", "raw_text": "x"},
        headers=auth_header(student),
    )

    assert resp.status_code == 201
    assert resp.json()["created_by"]["user_id"] == str(student.user_id)


def test_manager_can_create_crawl_text(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.post(
        "/crawl-texts",
        json={"source": "notion", "raw_text": "x"},
        headers=auth_header(manager),
    )

    assert resp.status_code == 201


def test_create_crawl_text_requires_auth(client):
    resp = client.post("/crawl-texts", json={"source": "notion", "raw_text": "x"})

    assert resp.status_code == 401
