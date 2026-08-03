import datetime

from app.models.user import UserPermission

YEAR = 2030
MONTH = 6


def _deadline_in_target_month(day: int = 15) -> str:
    return datetime.datetime(YEAR, MONTH, day, tzinfo=datetime.timezone.utc).isoformat()


def _deadline_outside_target_month() -> str:
    return datetime.datetime(YEAR, MONTH + 1, 1, tzinfo=datetime.timezone.utc).isoformat()


def _create_shared(client, auth_header, manager, deadline=None):
    payload = {
        "kind": "shared",
        "title": "PR 제출",
        "contents": "이번 주 과제 PR을 제출하세요.",
        "deadline": deadline or _deadline_in_target_month(),
    }
    return client.post("/schedules", json=payload, headers=auth_header(manager)).json()


def _create_personal(client, auth_header, user, deadline=None):
    payload = {
        "kind": "personal",
        "title": "학습일지 작성",
        "contents": "오늘 배운 내용을 정리한다.",
        "deadline": deadline or _deadline_in_target_month(),
    }
    return client.post("/schedules", json=payload, headers=auth_header(user)).json()


def test_student_sees_own_shared_and_personal_mixed(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    _create_shared(client, auth_header, manager)
    _create_personal(client, auth_header, student)

    resp = client.get(f"/schedules?year={YEAR}&month={MONTH}", headers=auth_header(student))

    assert resp.status_code == 200
    kinds = {s["kind"] for s in resp.json()}
    assert kinds == {"shared", "personal"}


def test_schedules_outside_month_excluded(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    _create_shared(client, auth_header, manager, deadline=_deadline_outside_target_month())

    resp = client.get(
        f"/schedules?year={YEAR}&month={MONTH}",
        headers=auth_header(make_user("student@katecam.dev", UserPermission.STUDENT)),
    )

    assert resp.status_code == 200
    assert resp.json() == []


def test_student_excludes_other_students_personal_schedule(client, make_user, auth_header):
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    _create_personal(client, auth_header, student_b)

    resp = client.get(f"/schedules?year={YEAR}&month={MONTH}", headers=auth_header(student_a))

    assert resp.status_code == 200
    assert resp.json() == []


def test_student_can_view_other_students_shared_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    _create_shared(client, auth_header, manager)

    resp = client.get(
        f"/schedules?year={YEAR}&month={MONTH}&student_id={student_b.user_id}",
        headers=auth_header(student_a),
    )

    assert resp.status_code == 200
    kinds = {s["kind"] for s in resp.json()}
    assert kinds == {"shared"}


def test_viewing_others_calendar_hides_their_personal_schedule(client, make_user, auth_header):
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    _create_personal(client, auth_header, student_b)

    resp = client.get(
        f"/schedules?year={YEAR}&month={MONTH}&student_id={student_b.user_id}",
        headers=auth_header(student_a),
    )

    assert resp.status_code == 200
    assert resp.json() == []


def test_student_id_defaults_to_self(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    _create_personal(client, auth_header, manager)

    resp = client.get(f"/schedules?year={YEAR}&month={MONTH}", headers=auth_header(manager))

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["owner_id"] == str(manager.user_id)


def test_manager_can_view_any_students_shared_schedule(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    _create_shared(client, auth_header, manager)

    resp = client.get(
        f"/schedules?year={YEAR}&month={MONTH}&student_id={student.user_id}",
        headers=auth_header(manager),
    )

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["kind"] == "shared"


def test_student_id_not_found(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)

    resp = client.get(
        f"/schedules?year={YEAR}&month={MONTH}&student_id=00000000-0000-0000-0000-000000000000",
        headers=auth_header(manager),
    )

    assert resp.status_code == 404


def test_done_defaults_false_and_reflects_completion(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    schedule = _create_personal(client, auth_header, student)

    before = client.get(f"/schedules?year={YEAR}&month={MONTH}", headers=auth_header(student))
    assert before.json()[0]["done"] is False

    client.put(
        f"/schedules/{schedule['schedule_id']}/completion",
        json={"done": True},
        headers=auth_header(student),
    )

    after = client.get(f"/schedules?year={YEAR}&month={MONTH}", headers=auth_header(student))
    assert after.json()[0]["done"] is True


def test_shared_schedule_done_is_per_student(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    shared = _create_shared(client, auth_header, manager)

    client.put(
        f"/schedules/{shared['schedule_id']}/completion",
        json={"done": True},
        headers=auth_header(student_a),
    )

    resp_a = client.get(f"/schedules?year={YEAR}&month={MONTH}", headers=auth_header(student_a))
    resp_b = client.get(f"/schedules?year={YEAR}&month={MONTH}", headers=auth_header(student_b))

    assert resp_a.json()[0]["done"] is True
    assert resp_b.json()[0]["done"] is False


def test_list_schedules_requires_auth(client):
    resp = client.get(f"/schedules?year={YEAR}&month={MONTH}")

    assert resp.status_code == 401
