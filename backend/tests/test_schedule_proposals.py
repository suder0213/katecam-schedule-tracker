import datetime

from app.models.crawl_text import CrawlSource, CrawlText
from app.models.schedule import Schedule, ScheduleKind
from app.models.schedule_proposal import ProposalStatus, ScheduleProposal
from app.models.user import UserPermission

DEADLINE = datetime.datetime(2026, 7, 24, tzinfo=datetime.timezone.utc)


def _make_proposal(db_session, title="기획서 제출"):
    crawl_text = CrawlText(source=CrawlSource.NOTION, raw_text="원문")
    db_session.add(crawl_text)
    db_session.commit()
    db_session.refresh(crawl_text)

    proposal = ScheduleProposal(
        raw_text_id=crawl_text.raw_text_id,
        title=title,
        contents="내용",
        deadline=DEADLINE,
    )
    db_session.add(proposal)
    db_session.commit()
    db_session.refresh(proposal)
    return crawl_text, proposal


def test_read_crawl_text(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    crawl_text, _ = _make_proposal(db_session)

    resp = client.get(f"/crawl-texts/{crawl_text.raw_text_id}", headers=auth_header(dev))

    assert resp.status_code == 200
    assert resp.json()["raw_text_id"] == str(crawl_text.raw_text_id)


def test_read_crawl_text_not_found(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.get("/crawl-texts/00000000-0000-0000-0000-000000000000", headers=auth_header(dev))

    assert resp.status_code == 404


def test_read_crawl_text_requires_dev(client, make_user, auth_header, db_session):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)
    crawl_text, _ = _make_proposal(db_session)

    resp = client.get(f"/crawl-texts/{crawl_text.raw_text_id}", headers=auth_header(student))

    assert resp.status_code == 403


def test_list_proposals_all(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    _make_proposal(db_session, title="A")
    _make_proposal(db_session, title="B")

    resp = client.get("/schedule-proposals", headers=auth_header(dev))

    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_proposals_filtered_by_raw_text_id(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    crawl_text_a, _ = _make_proposal(db_session, title="A")
    _make_proposal(db_session, title="B")

    resp = client.get(
        f"/schedule-proposals?raw_text_id={crawl_text_a.raw_text_id}", headers=auth_header(dev)
    )

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "A"


def test_list_proposals_requires_dev(client, make_user, auth_header):
    student = make_user("student@katecam.dev", UserPermission.STUDENT)

    resp = client.get("/schedule-proposals", headers=auth_header(student))

    assert resp.status_code == 403


def test_update_pending_proposal(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    _, proposal = _make_proposal(db_session, title="원래 제목")

    new_deadline = datetime.datetime(2026, 7, 25, 9, 0, tzinfo=datetime.timezone.utc)
    resp = client.patch(
        f"/schedule-proposals/{proposal.proposal_id}",
        json={"title": "수정된 제목", "deadline": new_deadline.isoformat()},
        headers=auth_header(dev),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "수정된 제목"
    assert body["contents"] == "내용"
    assert body["deadline"] == new_deadline.isoformat().replace("+00:00", "Z")


def test_update_proposal_allows_manager(client, make_user, auth_header, db_session):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    _, proposal = _make_proposal(db_session)

    resp = client.patch(
        f"/schedule-proposals/{proposal.proposal_id}",
        json={"title": "수정 시도"},
        headers=auth_header(manager),
    )

    assert resp.status_code == 200


def test_update_already_processed_proposal_rejected(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    _, proposal = _make_proposal(db_session)
    client.post(f"/schedule-proposals/{proposal.proposal_id}/approve", headers=auth_header(dev))

    resp = client.patch(
        f"/schedule-proposals/{proposal.proposal_id}",
        json={"title": "수정 시도"},
        headers=auth_header(dev),
    )

    assert resp.status_code == 409


def test_update_proposal_not_found(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.patch(
        "/schedule-proposals/00000000-0000-0000-0000-000000000000",
        json={"title": "수정 시도"},
        headers=auth_header(dev),
    )

    assert resp.status_code == 404


def test_approve_creates_shared_schedule(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    _, proposal = _make_proposal(db_session, title="기획서 제출")

    resp = client.post(
        f"/schedule-proposals/{proposal.proposal_id}/approve", headers=auth_header(dev)
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    created = db_session.query(Schedule).filter(Schedule.title == "기획서 제출").one()
    assert created.kind == ScheduleKind.SHARED
    assert created.owner_id is None


def test_approve_already_processed_rejected(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    _, proposal = _make_proposal(db_session)
    client.post(f"/schedule-proposals/{proposal.proposal_id}/approve", headers=auth_header(dev))

    resp = client.post(
        f"/schedule-proposals/{proposal.proposal_id}/approve", headers=auth_header(dev)
    )

    assert resp.status_code == 409


def test_approve_not_found(client, make_user, auth_header):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)

    resp = client.post(
        "/schedule-proposals/00000000-0000-0000-0000-000000000000/approve",
        headers=auth_header(dev),
    )

    assert resp.status_code == 404


def test_approve_allows_manager(client, make_user, auth_header, db_session):
    manager = make_user("manager@katecam.dev", UserPermission.MANAGER)
    _, proposal = _make_proposal(db_session)

    resp = client.post(
        f"/schedule-proposals/{proposal.proposal_id}/approve", headers=auth_header(manager)
    )

    assert resp.status_code == 200


def test_reject_does_not_create_schedule(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    _, proposal = _make_proposal(db_session, title="거절될 일정")

    resp = client.post(
        f"/schedule-proposals/{proposal.proposal_id}/reject", headers=auth_header(dev)
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    assert db_session.query(Schedule).filter(Schedule.title == "거절될 일정").first() is None


def test_reject_already_processed(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    _, proposal = _make_proposal(db_session)
    client.post(f"/schedule-proposals/{proposal.proposal_id}/reject", headers=auth_header(dev))

    resp = client.post(
        f"/schedule-proposals/{proposal.proposal_id}/reject", headers=auth_header(dev)
    )

    assert resp.status_code == 409


def test_partial_approval_within_same_text(client, make_user, auth_header, db_session):
    dev = make_user("dev@katecam.dev", UserPermission.DEV)
    crawl_text = CrawlText(source=CrawlSource.NOTION, raw_text="원문")
    db_session.add(crawl_text)
    db_session.commit()
    db_session.refresh(crawl_text)

    keep = ScheduleProposal(
        raw_text_id=crawl_text.raw_text_id, title="유지", contents="c", deadline=DEADLINE
    )
    drop = ScheduleProposal(
        raw_text_id=crawl_text.raw_text_id, title="거절", contents="c", deadline=DEADLINE
    )
    db_session.add_all([keep, drop])
    db_session.commit()
    db_session.refresh(keep)
    db_session.refresh(drop)

    client.post(f"/schedule-proposals/{keep.proposal_id}/approve", headers=auth_header(dev))
    client.post(f"/schedule-proposals/{drop.proposal_id}/reject", headers=auth_header(dev))

    resp = client.get(
        f"/schedule-proposals?raw_text_id={crawl_text.raw_text_id}", headers=auth_header(dev)
    )
    statuses = {p["title"]: p["status"] for p in resp.json()}
    assert statuses["유지"] == "approved"
    assert statuses["거절"] == ProposalStatus.REJECTED.value
