import datetime

from app.core.agent import ProposedScheduleItem, ProposedScheduleItems
from app.models.user import UserPermission

SAMPLE_ITEMS = ProposedScheduleItems(
    items=[
        ProposedScheduleItem(
            title="기획서 제출",
            contents="개인 프로젝트 기획서를 제출해주세요.",
            deadline=datetime.datetime(2026, 7, 24, tzinfo=datetime.timezone.utc),
        ),
        ProposedScheduleItem(
            title="코드리뷰 세션",
            contents="코드리뷰 세션이 있습니다.",
            deadline=datetime.datetime(2026, 7, 27, 10, 0, tzinfo=datetime.timezone.utc),
        ),
    ]
)


class _FakeStructuredModel:
    def __init__(self, result=None, always_raise=False):
        self.result = result
        self.always_raise = always_raise
        self.call_count = 0

    def invoke(self, prompt):
        self.call_count += 1
        if self.always_raise:
            raise ValueError("boom")
        return self.result


class _FakeChatModel:
    def __init__(self, structured_model):
        self.structured_model = structured_model

    def with_structured_output(self, schema):
        return self.structured_model


def _create_text(client, auth_header, dev):
    return client.post(
        "/crawl-texts",
        json={"source": "notion", "raw_text": "이번 주 금요일까지 기획서 제출"},
        headers=auth_header(dev),
    ).json()


def test_analyze_creates_proposals(client, make_user, auth_header, monkeypatch):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    text = _create_text(client, auth_header, dev)

    fake_model = _FakeChatModel(_FakeStructuredModel(result=SAMPLE_ITEMS))
    monkeypatch.setattr("app.core.agent.chat_model", lambda: fake_model)

    resp = client.post(f"/crawl-texts/{text['raw_text_id']}/analyze", headers=auth_header(dev))

    assert resp.status_code == 201
    body = resp.json()
    assert len(body) == 2
    assert {p["title"] for p in body} == {"기획서 제출", "코드리뷰 세션"}
    assert all(p["status"] == "pending" for p in body)
    assert all(p["raw_text_id"] == text["raw_text_id"] for p in body)


def test_analyze_retries_then_fails(client, make_user, auth_header, monkeypatch):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    text = _create_text(client, auth_header, dev)

    structured_model = _FakeStructuredModel(always_raise=True)
    fake_model = _FakeChatModel(structured_model)
    monkeypatch.setattr("app.core.agent.chat_model", lambda: fake_model)

    resp = client.post(f"/crawl-texts/{text['raw_text_id']}/analyze", headers=auth_header(dev))

    assert resp.status_code == 422
    assert structured_model.call_count == 3


def test_analyze_nonexistent_text(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.post(
        "/crawl-texts/00000000-0000-0000-0000-000000000000/analyze",
        headers=auth_header(dev),
    )

    assert resp.status_code == 404


def test_student_can_trigger_analyze(client, make_user, auth_header, monkeypatch):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    text = _create_text(client, auth_header, dev)

    fake_model = _FakeChatModel(_FakeStructuredModel(result=SAMPLE_ITEMS))
    monkeypatch.setattr("app.core.agent.chat_model", lambda: fake_model)

    resp = client.post(f"/crawl-texts/{text['raw_text_id']}/analyze", headers=auth_header(student))

    assert resp.status_code == 201


def test_analyze_requires_auth(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    text = _create_text(client, auth_header, dev)

    resp = client.post(f"/crawl-texts/{text['raw_text_id']}/analyze")

    assert resp.status_code == 401
