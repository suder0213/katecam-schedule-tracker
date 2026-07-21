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

## 트러블슈팅

- **컬럼 rename 후 테스트 DB가 stale해지는 문제.** `tests/conftest.py`가 `Base.metadata.create_all()`만 호출하고 있었는데, 이건 없는 테이블만 만들지 이미 존재하는 테이블의 컬럼 변경은 반영하지 않음. `student_id→owner_id` 마이그레이션 직후 스케줄 테스트 전체가 `column schedules.owner_id does not exist` 에러로 실패. `drop_all()` 후 `create_all()`로 변경해 앞으로 모델이 바뀔 때마다 테스트 DB가 항상 최신 스키마로 재생성되도록 수정.
- **테스트 코드의 UUID 타입 불일치.** `team_resp.json()["team_id"]`가 문자열인데 이를 `uuid.UUID`로 변환하지 않고 그대로 `TeamMember(team_id=...)`에 넘겨서, SQLAlchemy의 insertmanyvalues sentinel 매칭이 실패(`Can't match sentinel values...`). 문자열을 `uuid.UUID()`로 감싸서 해결 — 실제 프로덕션 코드 버그는 아니고 테스트 헬퍼의 실수.
- **FK 제약조건 이름은 rename 후에도 옛 이름(`schedules_student_id_fkey`) 유지.** Postgres의 `ALTER COLUMN ... RENAME`은 제약조건 이름까지 자동으로 바꿔주지 않음. 기능적으로는 문제없는 화장품 수준의 불일치라 그대로 둠.
- **불필요하게 복잡했던 테스트 헬퍼.** `_create_team` 헬퍼를 처음엔 conftest의 `auth_header` fixture를 억지로 재사용하려다 `auth_header_for`라는 중복 함수까지 만들어버림 — `create_access_token`을 직접 import해서 쓰는 것으로 단순화.

## 테스트 현황

- `test_users.py`(11), `test_teams.py`(18), `test_schedules.py`(21), `test_schedules_calendar.py`(10) 신규 추가
- 기존 `test_auth.py`(19), `test_security.py`(3), `test_rate_limit.py`(3)와 합쳐 총 **85개 테스트 통과**
- `tests/conftest.py`에 `make_user`(임의 권한의 인증된 유저를 DB에 직접 생성), `auth_header`(그 유저의 access token 헤더 생성), `db_session`(API가 아직 없는 관계를 테스트에서 직접 넣기 위한 raw DB 세션) fixture 추가 — Phase 3 전반에서 재사용

## 현재 상태

Phase 0~3 전부 구현 및 검증 완료. 다음은 Phase 4(Agent 기반 일정 추가 계획 — 텍스트 입력 → Claude API 분석 → Approve → 백업).
