"""Dev seed data: one dev, one manager, a few students, and sample schedules.

Run with: python -m scripts.seed
"""

import datetime

from app.core.security import hash_password
from app.db.base import SessionLocal
from app.models import Schedule, Team, TeamMember, User
from app.models.schedule import ScheduleKind
from app.models.user import UserPermission


def seed() -> None:
    session = SessionLocal()
    try:
        dev = User(
            email="dev@katecam.dev",
            password=hash_password("password123"),
            nick_name="dev",
            permission=UserPermission.DEV,
        )
        manager = User(
            email="manager@katecam.dev",
            password=hash_password("password123"),
            nick_name="manager",
            permission=UserPermission.MANAGER,
        )
        students = [
            User(
                email=f"student{i}@katecam.dev",
                password=hash_password("password123"),
                nick_name=f"student{i}",
                permission=UserPermission.STUDENT,
            )
            for i in range(1, 4)
        ]
        session.add_all([dev, manager, *students])
        session.flush()

        team = Team(name="OO대-1팀")
        session.add(team)
        session.flush()
        session.add_all(TeamMember(team_id=team.team_id, user_id=s.user_id) for s in students)

        shared_schedule = Schedule(
            kind=ScheduleKind.SHARED,
            title="PR 제출",
            contents="이번 주 과제 PR을 제출하세요.",
            deadline=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7),
            student_id=None,
        )
        personal_schedule = Schedule(
            kind=ScheduleKind.PERSONAL,
            title="학습일지 작성",
            contents="오늘 배운 내용을 정리한다.",
            deadline=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
            student_id=students[0].user_id,
        )
        session.add_all([shared_schedule, personal_schedule])

        session.commit()
        print("Seeded:")
        print(f"  dev: {dev.email} ({dev.user_id})")
        print(f"  manager: {manager.email} ({manager.user_id})")
        for s in students:
            print(f"  student: {s.email} ({s.user_id})")
        print(f"  team: {team.name} ({team.team_id})")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
