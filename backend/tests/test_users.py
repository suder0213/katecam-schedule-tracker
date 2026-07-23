from app.models.user import UserPermission


def test_list_students_returns_only_students_sorted_by_nick_name(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    make_user("student-c@katecam.dev", UserPermission.STUDENT, nick_name="다니엘")
    make_user("student-a@katecam.dev", UserPermission.STUDENT, nick_name="가영")
    make_user("other-manager@katecam.dev", UserPermission.MANAGER)

    resp = client.get("/users", headers=auth_header(manager))

    assert resp.status_code == 200
    nick_names = [u["nick_name"] for u in resp.json()]
    assert nick_names == ["가영", "다니엘"]


def test_list_students_visible_to_student(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    make_user("other-student@katecam.dev", UserPermission.STUDENT, nick_name="나영")

    resp = client.get("/users", headers=auth_header(student))

    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_all_users_returns_every_permission(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    make_user("manager@katecam.dev", UserPermission.MANAGER, nick_name="나매니저")
    make_user("student@katecam.dev", UserPermission.STUDENT, nick_name="다학생")

    resp = client.get("/users/all", headers=auth_header(dev))

    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_list_all_users_forbidden_for_manager(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.get("/users/all", headers=auth_header(manager))

    assert resp.status_code == 403


def test_list_all_users_forbidden_for_student(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.get("/users/all", headers=auth_header(student))

    assert resp.status_code == 403


def test_read_user_dev_can_view_anyone(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.get(f"/users/{manager.user_id}", headers=auth_header(dev))

    assert resp.status_code == 200
    assert resp.json()["email"] == manager.email


def test_read_user_manager_can_view_any_student(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.get(f"/users/{student.user_id}", headers=auth_header(manager))

    assert resp.status_code == 200
    assert resp.json()["email"] == student.email


def test_read_user_manager_can_view_other_manager(client, make_user, auth_header):
    manager = make_user("manager1@katecam.dev", UserPermission.MANAGER)
    other_manager = make_user("manager2@katecam.dev", UserPermission.MANAGER)

    resp = client.get(f"/users/{other_manager.user_id}", headers=auth_header(manager))

    assert resp.status_code == 200
    assert resp.json()["email"] == other_manager.email


def test_read_user_manager_can_view_dev(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.get(f"/users/{dev.user_id}", headers=auth_header(manager))

    assert resp.status_code == 200
    assert resp.json()["email"] == dev.email


def test_read_user_student_forbidden(client, make_user, auth_header):
    student = make_user("student1@katecam.dev", UserPermission.STUDENT)
    other_student = make_user("student2@katecam.dev", UserPermission.STUDENT)

    resp = client.get(f"/users/{other_student.user_id}", headers=auth_header(student))

    assert resp.status_code == 403


def test_read_user_not_found(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.get(
        "/users/00000000-0000-0000-0000-000000000000",
        headers=auth_header(dev),
    )

    assert resp.status_code == 404


def test_promote_student_to_manager(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.patch(
        f"/users/{student.user_id}/permission",
        json={"permission": "manager"},
        headers=auth_header(manager),
    )

    assert resp.status_code == 200
    assert resp.json()["permission"] == "manager"


def test_demote_manager_to_student(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.patch(
        f"/users/{manager.user_id}/permission",
        json={"permission": "student"},
        headers=auth_header(dev),
    )

    assert resp.status_code == 200
    assert resp.json()["permission"] == "student"


def test_cannot_promote_to_dev(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.patch(
        f"/users/{student.user_id}/permission",
        json={"permission": "dev"},
        headers=auth_header(manager),
    )

    assert resp.status_code == 403


def test_cannot_change_dev_target_permission(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.patch(
        f"/users/{dev.user_id}/permission",
        json={"permission": "student"},
        headers=auth_header(manager),
    )

    assert resp.status_code == 403


def test_student_cannot_change_permissions(client, make_user, auth_header):
    student = make_user("student1@katecam.dev", UserPermission.STUDENT)
    other_student = make_user("student2@katecam.dev", UserPermission.STUDENT)

    resp = client.patch(
        f"/users/{other_student.user_id}/permission",
        json={"permission": "manager"},
        headers=auth_header(student),
    )

    assert resp.status_code == 403
