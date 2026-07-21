import datetime

from app.models.user import UserPermission

DEADLINE = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat()


def _shared_payload():
    return {
        "kind": "shared",
        "title": "PR 제출",
        "contents": "이번 주 과제 PR을 제출하세요.",
        "deadline": DEADLINE,
    }


def _personal_payload():
    return {
        "kind": "personal",
        "title": "학습일지 작성",
        "contents": "오늘 배운 내용을 정리한다.",
        "deadline": DEADLINE,
    }


def test_manager_can_create_shared_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.post("/schedules", json=_shared_payload(), headers=auth_header(manager))

    assert resp.status_code == 201
    assert resp.json()["kind"] == "shared"
    assert resp.json()["owner_id"] is None


def test_student_cannot_create_shared_schedule(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.post("/schedules", json=_shared_payload(), headers=auth_header(student))

    assert resp.status_code == 403


def test_any_authenticated_user_can_create_personal_schedule(client, make_user, auth_header):
    for permission in (UserPermission.STUDENT, UserPermission.MANAGER, UserPermission.DEV):
        user = make_user(f"user-{permission.value}@katecam.dev", permission)

        resp = client.post("/schedules", json=_personal_payload(), headers=auth_header(user))

        assert resp.status_code == 201
        assert resp.json()["owner_id"] == str(user.user_id)


def test_create_schedule_requires_auth(client):
    resp = client.post("/schedules", json=_personal_payload())

    assert resp.status_code == 401


def test_manager_can_update_shared_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    create_resp = client.post("/schedules", json=_shared_payload(), headers=auth_header(manager))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.patch(
        f"/schedules/{schedule_id}", json={"title": "수정된 제목"}, headers=auth_header(manager)
    )

    assert resp.status_code == 200
    assert resp.json()["title"] == "수정된 제목"


def test_student_cannot_update_shared_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_shared_payload(), headers=auth_header(manager))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.patch(
        f"/schedules/{schedule_id}", json={"title": "해킹시도"}, headers=auth_header(student)
    )

    assert resp.status_code == 403


def test_owner_can_update_own_personal_schedule(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_personal_payload(), headers=auth_header(student))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.patch(
        f"/schedules/{schedule_id}", json={"title": "수정"}, headers=auth_header(student)
    )

    assert resp.status_code == 200
    assert resp.json()["title"] == "수정"


def test_other_student_cannot_update_personal_schedule(client, make_user, auth_header):
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post(
        "/schedules", json=_personal_payload(), headers=auth_header(student_a)
    )
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.patch(
        f"/schedules/{schedule_id}", json={"title": "해킹시도"}, headers=auth_header(student_b)
    )

    assert resp.status_code == 403


def test_manager_cannot_update_others_personal_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_personal_payload(), headers=auth_header(student))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.patch(
        f"/schedules/{schedule_id}", json={"title": "관리자 수정"}, headers=auth_header(manager)
    )

    assert resp.status_code == 403


def test_update_nonexistent_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.patch(
        "/schedules/00000000-0000-0000-0000-000000000000",
        json={"title": "x"},
        headers=auth_header(manager),
    )

    assert resp.status_code == 404


def test_manager_can_delete_shared_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    create_resp = client.post("/schedules", json=_shared_payload(), headers=auth_header(manager))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.delete(f"/schedules/{schedule_id}", headers=auth_header(manager))

    assert resp.status_code == 204


def test_student_cannot_delete_shared_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_shared_payload(), headers=auth_header(manager))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.delete(f"/schedules/{schedule_id}", headers=auth_header(student))

    assert resp.status_code == 403


def test_owner_can_delete_own_personal_schedule(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_personal_payload(), headers=auth_header(student))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.delete(f"/schedules/{schedule_id}", headers=auth_header(student))

    assert resp.status_code == 204


def test_delete_nonexistent_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.delete(
        "/schedules/00000000-0000-0000-0000-000000000000", headers=auth_header(manager)
    )

    assert resp.status_code == 404


def test_delete_schedule_with_completion_row_cascades(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_personal_payload(), headers=auth_header(student))
    schedule_id = create_resp.json()["schedule_id"]
    client.put(
        f"/schedules/{schedule_id}/completion",
        json={"done": True},
        headers=auth_header(student),
    )

    resp = client.delete(f"/schedules/{schedule_id}", headers=auth_header(student))

    assert resp.status_code == 204


def test_owner_can_complete_own_personal_schedule(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_personal_payload(), headers=auth_header(student))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.put(
        f"/schedules/{schedule_id}/completion",
        json={"done": True},
        headers=auth_header(student),
    )

    assert resp.status_code == 200
    assert resp.json()["done"] is True
    assert resp.json()["owner_id"] == str(student.user_id)


def test_completion_upsert_updates_existing_row(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_personal_payload(), headers=auth_header(student))
    schedule_id = create_resp.json()["schedule_id"]

    first = client.put(
        f"/schedules/{schedule_id}/completion",
        json={"done": True},
        headers=auth_header(student),
    )
    second = client.put(
        f"/schedules/{schedule_id}/completion",
        json={"done": False},
        headers=auth_header(student),
    )

    assert first.json()["done"] is True
    assert second.json()["done"] is False
    assert first.json()["created_at"] == second.json()["created_at"]


def test_other_student_cannot_complete_others_personal_schedule(client, make_user, auth_header):
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post(
        "/schedules", json=_personal_payload(), headers=auth_header(student_a)
    )
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.put(
        f"/schedules/{schedule_id}/completion",
        json={"done": True},
        headers=auth_header(student_b),
    )

    assert resp.status_code == 403


def test_any_student_can_complete_shared_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_shared_payload(), headers=auth_header(manager))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.put(
        f"/schedules/{schedule_id}/completion",
        json={"done": True},
        headers=auth_header(student),
    )

    assert resp.status_code == 200
    assert resp.json()["owner_id"] == str(student.user_id)


def test_shared_schedule_completion_is_per_user(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    create_resp = client.post("/schedules", json=_shared_payload(), headers=auth_header(manager))
    schedule_id = create_resp.json()["schedule_id"]

    client.put(
        f"/schedules/{schedule_id}/completion",
        json={"done": True},
        headers=auth_header(student_a),
    )
    resp_b = client.put(
        f"/schedules/{schedule_id}/completion",
        json={"done": False},
        headers=auth_header(student_b),
    )

    assert resp_b.json()["done"] is False
    assert resp_b.json()["owner_id"] == str(student_b.user_id)


def test_complete_nonexistent_schedule(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.put(
        "/schedules/00000000-0000-0000-0000-000000000000/completion",
        json={"done": True},
        headers=auth_header(student),
    )

    assert resp.status_code == 404


def test_complete_requires_auth(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    create_resp = client.post("/schedules", json=_shared_payload(), headers=auth_header(manager))
    schedule_id = create_resp.json()["schedule_id"]

    resp = client.put(f"/schedules/{schedule_id}/completion", json={"done": True})

    assert resp.status_code == 401
