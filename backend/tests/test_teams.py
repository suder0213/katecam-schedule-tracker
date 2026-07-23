import uuid

from app.core.security import create_access_token
from app.models.team import TeamMember
from app.models.user import UserPermission


def test_manager_can_create_team(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.post("/teams", json={"name": "1팀"}, headers=auth_header(manager))

    assert resp.status_code == 201
    assert resp.json()["name"] == "1팀"


def test_dev_can_create_team(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.post("/teams", json={"name": "2팀"}, headers=auth_header(dev))

    assert resp.status_code == 201


def test_student_cannot_create_team(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.post("/teams", json={"name": "3팀"}, headers=auth_header(student))

    assert resp.status_code == 403


def test_create_team_requires_auth(client):
    resp = client.post("/teams", json={"name": "4팀"})

    assert resp.status_code == 401


def test_list_teams_visible_to_any_authenticated_user(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    client.post("/teams", json={"name": "1팀"}, headers=auth_header(manager))

    resp = client.get("/teams", headers=auth_header(student))

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "1팀"


def test_list_teams_requires_auth(client):
    resp = client.get("/teams")

    assert resp.status_code == 401


def test_list_team_members(client, make_user, auth_header, db_session):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student1 = make_user("student1@katecam.dev", UserPermission.STUDENT)
    student2 = make_user("student2@katecam.dev", UserPermission.STUDENT)

    team_resp = client.post("/teams", json={"name": "1팀"}, headers=auth_header(manager))
    team_id = uuid.UUID(team_resp.json()["team_id"])

    db_session.add(TeamMember(team_id=team_id, user_id=student1.user_id))
    db_session.add(TeamMember(team_id=team_id, user_id=student2.user_id))
    db_session.commit()

    resp = client.get(f"/teams/{team_id}/members", headers=auth_header(student1))

    assert resp.status_code == 200
    emails = {member["email"] for member in resp.json()}
    assert emails == {student1.email, student2.email}


def test_list_team_members_not_found(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.get(
        "/teams/00000000-0000-0000-0000-000000000000/members",
        headers=auth_header(student),
    )

    assert resp.status_code == 404


def _create_team(client, manager, name="1팀"):
    headers = {"Authorization": f"Bearer {create_access_token(manager.user_id)}"}
    resp = client.post("/teams", json={"name": name}, headers=headers)
    return uuid.UUID(resp.json()["team_id"])


def test_student_can_add_self_to_team(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)

    resp = client.post(
        f"/teams/{team_id}/members",
        json={"user_id": str(student.user_id)},
        headers=auth_header(student),
    )

    assert resp.status_code == 201
    assert resp.json()["user_id"] == str(student.user_id)


def test_student_cannot_add_other_student(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)

    resp = client.post(
        f"/teams/{team_id}/members",
        json={"user_id": str(student_b.user_id)},
        headers=auth_header(student_a),
    )

    assert resp.status_code == 403


def test_manager_can_add_any_student(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)

    resp = client.post(
        f"/teams/{team_id}/members",
        json={"user_id": str(student.user_id)},
        headers=auth_header(manager),
    )

    assert resp.status_code == 201


def test_add_member_duplicate_rejected(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)
    client.post(
        f"/teams/{team_id}/members",
        json={"user_id": str(student.user_id)},
        headers=auth_header(student),
    )

    resp = client.post(
        f"/teams/{team_id}/members",
        json={"user_id": str(student.user_id)},
        headers=auth_header(student),
    )

    assert resp.status_code == 400


def test_add_member_team_not_found(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.post(
        "/teams/00000000-0000-0000-0000-000000000000/members",
        json={"user_id": str(student.user_id)},
        headers=auth_header(student),
    )

    assert resp.status_code == 404


def test_add_member_user_not_found(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    team_id = _create_team(client, manager)

    resp = client.post(
        f"/teams/{team_id}/members",
        json={"user_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_header(manager),
    )

    assert resp.status_code == 404


def test_student_can_remove_self(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)
    client.post(
        f"/teams/{team_id}/members",
        json={"user_id": str(student.user_id)},
        headers=auth_header(student),
    )

    resp = client.delete(
        f"/teams/{team_id}/members/{student.user_id}", headers=auth_header(student)
    )

    assert resp.status_code == 204


def test_student_cannot_remove_other_student(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)
    client.post(
        f"/teams/{team_id}/members",
        json={"user_id": str(student_b.user_id)},
        headers=auth_header(student_b),
    )

    resp = client.delete(
        f"/teams/{team_id}/members/{student_b.user_id}", headers=auth_header(student_a)
    )

    assert resp.status_code == 403


def test_manager_can_remove_any_member(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)
    client.post(
        f"/teams/{team_id}/members",
        json={"user_id": str(student.user_id)},
        headers=auth_header(student),
    )

    resp = client.delete(
        f"/teams/{team_id}/members/{student.user_id}", headers=auth_header(manager)
    )

    assert resp.status_code == 204


def test_remove_member_not_found(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)

    resp = client.delete(
        f"/teams/{team_id}/members/{student.user_id}", headers=auth_header(manager)
    )

    assert resp.status_code == 404


def test_list_my_teams_returns_only_joined_teams(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    team_a = _create_team(client, manager, name="1팀")
    _create_team(client, manager, name="2팀")

    client.post(
        f"/teams/{team_a}/members",
        json={"user_id": str(student.user_id)},
        headers=auth_header(student),
    )

    resp = client.get("/teams/mine", headers=auth_header(student))

    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()]
    assert names == ["1팀"]


def test_list_my_teams_empty_when_not_joined(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    _create_team(client, manager)

    resp = client.get("/teams/mine", headers=auth_header(student))

    assert resp.status_code == 200
    assert resp.json() == []


def test_list_my_teams_requires_auth(client):
    resp = client.get("/teams/mine")

    assert resp.status_code == 401


def test_manager_can_delete_team(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    team_id = _create_team(client, manager)

    resp = client.delete(f"/teams/{team_id}", headers=auth_header(manager))

    assert resp.status_code == 204
    assert client.get("/teams", headers=auth_header(manager)).json() == []


def test_dev_can_delete_team(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    team_id = _create_team(client, dev)

    resp = client.delete(f"/teams/{team_id}", headers=auth_header(dev))

    assert resp.status_code == 204


def test_deleting_team_removes_memberships(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)
    client.post(
        f"/teams/{team_id}/members",
        json={"user_id": str(student.user_id)},
        headers=auth_header(student),
    )

    resp = client.delete(f"/teams/{team_id}", headers=auth_header(manager))

    assert resp.status_code == 204
    assert client.get("/teams/mine", headers=auth_header(student)).json() == []


def test_student_cannot_delete_team(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    team_id = _create_team(client, manager)

    resp = client.delete(f"/teams/{team_id}", headers=auth_header(student))

    assert resp.status_code == 403


def test_delete_team_not_found(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.delete(f"/teams/{uuid.uuid4()}", headers=auth_header(manager))

    assert resp.status_code == 404


def test_delete_team_requires_auth(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    team_id = _create_team(client, manager)

    resp = client.delete(f"/teams/{team_id}")

    assert resp.status_code == 401
