import datetime

from app.models.user import UserPermission

FAR_FUTURE_YEAR = 2031


def _deadline(month: int, day: int) -> str:
    return datetime.datetime(FAR_FUTURE_YEAR, month, day, tzinfo=datetime.timezone.utc).isoformat()


def _create_personal(client, auth_header, user, month: int, day: int, title: str):
    return client.post(
        "/schedules",
        json={
            "kind": "personal",
            "title": title,
            "contents": "c",
            "deadline": _deadline(month, day),
        },
        headers=auth_header(user),
    ).json()


def test_todo_sorted_by_nearest_deadline(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    _create_personal(client, auth_header, student, 8, 20, "나중 일정")
    _create_personal(client, auth_header, student, 6, 1, "가장 급한 일정")
    _create_personal(client, auth_header, student, 7, 15, "중간 일정")

    resp = client.get("/schedules/todo", headers=auth_header(student))

    assert resp.status_code == 200
    titles = [s["title"] for s in resp.json()]
    assert titles == ["가장 급한 일정", "중간 일정", "나중 일정"]


def test_todo_excludes_completed(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    done_one = _create_personal(client, auth_header, student, 6, 1, "완료함")
    _create_personal(client, auth_header, student, 6, 2, "미완료")

    client.put(
        f"/schedules/{done_one['schedule_id']}/completion",
        json={"done": True},
        headers=auth_header(student),
    )

    resp = client.get("/schedules/todo", headers=auth_header(student))

    titles = [s["title"] for s in resp.json()]
    assert titles == ["미완료"]


def test_todo_includes_shared_schedules(client, make_user, auth_header):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    client.post(
        "/schedules",
        json={"kind": "shared", "title": "공유 일정", "contents": "c", "deadline": _deadline(6, 1)},
        headers=auth_header(manager),
    )

    resp = client.get("/schedules/todo", headers=auth_header(student))

    titles = [s["title"] for s in resp.json()]
    assert "공유 일정" in titles


def test_todo_excludes_other_users_personal_schedules(client, make_user, auth_header):
    student_a = make_user("student-a@katecam.dev", UserPermission.STUDENT)
    student_b = make_user("student-b@katecam.dev", UserPermission.STUDENT)
    _create_personal(client, auth_header, student_b, 6, 1, "학생B 일정")

    resp = client.get("/schedules/todo", headers=auth_header(student_a))

    titles = [s["title"] for s in resp.json()]
    assert "학생B 일정" not in titles


def test_todo_respects_limit(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    for day in range(1, 6):
        _create_personal(client, auth_header, student, 6, day, f"일정{day}")

    resp = client.get("/schedules/todo?limit=2", headers=auth_header(student))

    assert len(resp.json()) == 2


def test_todo_requires_auth(client):
    resp = client.get("/schedules/todo")

    assert resp.status_code == 401
