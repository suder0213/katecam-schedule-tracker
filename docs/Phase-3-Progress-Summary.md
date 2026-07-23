# Phase 3 구현 요약

`docs/Implementation-Plan.md` 기준 Phase 3(핵심 CRUD API) 진행 내용과 과정에서 있었던 설계 변경, 트러블슈팅을 정리한다. Phase 0~2는 `docs/Phase-0-2-Progress-Summary.md` 참고.

## 구현 항목

| 항목 | 내용 |
|---|---|
| 3-1 User 관리 | `GET /users/me`, `GET /users/{id}`, `PATCH /users/{id}/permission` |
| 3-2 Team CRUD | `POST /teams`(manager/dev만), `GET /teams`, `GET /teams/{id}/members`(인증된 누구나) |
| 3-3 TeamMember CRUD | `POST/DELETE /teams/{id}/members` — student는 본인만, manager/dev는 임의 유저 |
| 3-4 Schedule 달력 통합 조회 | `GET /schedules?year=&month=&student_id=` — 공유+개인 섞어서, 완료 여부 포함 |
| 3-5/3-6 Schedule CRUD | `POST/PATCH/DELETE /schedules` — kind에 따라 권한 분기 |
| 3-7 Schedule_Completion | `PUT /schedules/{id}/completion` — upsert, done 양방향 토글 가능 |

## 원 계획 대비 변경된 결정사항

### Manager 조회 범위 — "소속 학생만" → "팀 무관 전체"

원래 PRD/계획서는 "manager는 소속 학생만 조회 가능"이었는데, 실제로는 "매니저가 굳이 같은 팀일 필요는 없다"는 요구사항 확인 후 팀 소속 여부와 무관하게 전체 조회로 변경. 처음엔 "student만" 조회 가능으로 좁혔다가, 재논의 끝에 **manager/dev 모두 dev를 포함한 전체 유저를 제한 없이 조회 가능**하도록 최종 확정(`GET /users/{id}`). 3-4(일정 조회), 3-7 관련 문구도 전부 "전체" 기준으로 통일.

### User permission 변경 — "student→manager 승격만" → "양방향 변경"

원래 계획은 승격(student→manager)만 다뤘는데, "manager를 student로 바꿀 수도 있어야지"라는 지적으로 `PATCH /users/{id}/permission`을 양방향으로 확장. dev로의 승격/dev 대상 변경은 여전히 API로 불가(DB 직접 조작만) — 이 제약은 그대로 유지.

### 프론트엔드 달력 UI 확정에 따른 Schedule 조회 재설계

학생/운영진/개발자 화면이 "월 단위 큰 달력에 공유+개인 일정이 섞여서 표시(색/아이콘만 구분), 사이드바에서 학생 선택(탭: 학생 flat list / 팀 아코디언)" 형태로 확정되면서, 원래 계획의 "공유 조회 따로 / 타 유저 조회 따로"(옛 3-4, 3-7)를 `GET /schedules?year=&month=&student_id=` **통합 엔드포인트 하나**로 합침. CUD는 기존처럼 공유/개인 분리 유지. Phase 5(프론트엔드) 문서도 이 달력 UI에 맞춰 재작성.

### `Schedule.student_id` → `owner_id` 리네이밍

3-6 개인 일정 CRUD를 구현하다가 "개인 일정은 학생뿐 아니라 dev/manager도 가질 수 있다"(PRD "0. 공통" 섹션에 이미 명시돼 있었음)는 점이 재확인되면서, `student_id`라는 컬럼명이 실제 의미와 안 맞음을 발견. `Schedule`/`Schedule_Completion` 양쪽 모두 `owner_id`로 리네이밍(모델 + 마이그레이션 + seed + 문서 전부 반영). 단, 3-4의 쿼리 파라미터 `student_id`(달력에서 볼 학생을 지정)는 별개 개념이라 그대로 유지.

### FK에 ON DELETE CASCADE 추가

Phase 3 CRUD를 다 만든 뒤 "CASCADE가 제대로 선언돼 있나?"는 질문에 점검해보니, 모든 FK가 `ondelete` 미지정(기본값 NO ACTION) 상태였음. 실제로 `schedule_completions.schedule_id → schedules.schedule_id`에 CASCADE가 없어서, 완료 기록이 하나라도 있는 일정을 `DELETE /schedules/{id}`로 지우면 `ForeignKeyViolation`으로 500 에러가 나는 게 재현됨(테스트가 전부 완료기록 없는 일정만 삭제해서 못 잡았던 케이스). 논의 후 다음 5개 FK 전부 `ON DELETE CASCADE`로 변경:
- `schedule_completions.schedule_id → schedules.schedule_id`
- `team_members.team_id → teams.team_id` (팀 삭제 API는 아직 없지만 미리 선언)
- `schedules.owner_id`, `team_members.user_id`, `schedule_completions.owner_id` → `users.user_id` (유저 삭제 시 관련 데이터 전부 연쇄 삭제 — `DELETE /users/{id}` API 자체는 아직 계획에 없음)

Postgres는 `ALTER TABLE ... ALTER COLUMN`으로 FK의 `ondelete`만 바꿀 수 없어서, 마이그레이션에서 5개 제약조건을 각각 `DROP CONSTRAINT` 후 같은 이름으로 `ondelete="CASCADE"`를 붙여 재생성. 회귀 테스트(`test_delete_schedule_with_completion_row_cascades`)로 고정.

### Schedule에 `kind`/`owner_id` 정합성 CHECK 제약조건 추가

CASCADE를 점검하다가 "shared 일정에 owner_id가 실수로 채워지면, 그 유저가 삭제될 때 모두가 봐야 할 공유 일정까지 CASCADE로 같이 사라질 수 있는 것 아니냐"는 지적이 나옴. 확인해보니 `kind='shared'`면 `owner_id`가 항상 `NULL`이어야 한다는 규칙이 **애플리케이션 코드에서만** 지켜지고 있었고(생성 시에만 그렇게 세팅, `PATCH`로도 못 바꿈), DB 레벨에서 강제되진 않고 있었음. 다음 CHECK 제약조건을 `schedules` 테이블에 추가해 DB 레벨에서 원천 차단:

```sql
CHECK ((kind = 'SHARED' AND owner_id IS NULL) OR (kind = 'PERSONAL' AND owner_id IS NOT NULL))
```

- SQLAlchemy `Enum`이 값을 대문자 멤버 이름(`SHARED`/`PERSONAL`)으로 저장한다는 걸 Phase 2에서 이미 알고 있었어서, CHECK 조건도 대문자로 작성(소문자로 썼으면 항상 거짓이 되어 모든 insert가 막혔을 것).
- Alembic autogenerate는 CHECK 제약조건 변경을 감지하지 못해서(다른 무관한 drift만 잡음) 마이그레이션을 직접 작성.
- 실제로 두 위반 케이스(shared인데 owner_id 있음 / personal인데 owner_id 없음) 모두 psql로 직접 insert 시도해서 거부되는 것 확인, `db_session` fixture로 회귀 테스트 2개 추가.

## 트러블슈팅

- **컬럼 rename 후 테스트 DB가 stale해지는 문제.** `tests/conftest.py`가 `Base.metadata.create_all()`만 호출하고 있었는데, 이건 없는 테이블만 만들지 이미 존재하는 테이블의 컬럼 변경은 반영하지 않음. `student_id→owner_id` 마이그레이션 직후 스케줄 테스트 전체가 `column schedules.owner_id does not exist` 에러로 실패. `drop_all()` 후 `create_all()`로 변경해 앞으로 모델이 바뀔 때마다 테스트 DB가 항상 최신 스키마로 재생성되도록 수정.
- **테스트 코드의 UUID 타입 불일치.** `team_resp.json()["team_id"]`가 문자열인데 이를 `uuid.UUID`로 변환하지 않고 그대로 `TeamMember(team_id=...)`에 넘겨서, SQLAlchemy의 insertmanyvalues sentinel 매칭이 실패(`Can't match sentinel values...`). 문자열을 `uuid.UUID()`로 감싸서 해결 — 실제 프로덕션 코드 버그는 아니고 테스트 헬퍼의 실수.
- **FK 제약조건 이름은 rename 후에도 옛 이름(`schedules_student_id_fkey`) 유지.** Postgres의 `ALTER COLUMN ... RENAME`은 제약조건 이름까지 자동으로 바꿔주지 않음. 기능적으로는 문제없는 화장품 수준의 불일치라 그대로 둠.
- **불필요하게 복잡했던 테스트 헬퍼.** `_create_team` 헬퍼를 처음엔 conftest의 `auth_header` fixture를 억지로 재사용하려다 `auth_header_for`라는 중복 함수까지 만들어버림 — `create_access_token`을 직접 import해서 쓰는 것으로 단순화.

## 테스트 현황

- `test_users.py`(11), `test_teams.py`(18), `test_schedules.py`(24), `test_schedules_calendar.py`(10) 신규 추가
- 기존 `test_auth.py`(19), `test_security.py`(3), `test_rate_limit.py`(3)와 합쳐 총 **88개 테스트 통과**
- `tests/conftest.py`에 `make_user`(임의 권한의 인증된 유저를 DB에 직접 생성), `auth_header`(그 유저의 access token 헤더 생성), `db_session`(API가 아직 없는 관계를 테스트에서 직접 넣기 위한 raw DB 세션) fixture 추가 — Phase 3 전반에서 재사용

## 현재 상태

Phase 0~3 전부 구현 및 검증 완료. 다음은 Phase 4(Agent 기반 일정 추가 계획 — 텍스트 입력 → Claude API 분석 → Approve → 백업).
