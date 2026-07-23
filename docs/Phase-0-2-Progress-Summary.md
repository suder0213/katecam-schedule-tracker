# Phase 0~2 구현 요약

`docs/Implementation-Plan.md` 기준 Phase 0(환경 셋업) ~ Phase 2(인증) 진행 내용과 과정에서 있었던 트러블슈팅, 원 계획 대비 변경된 결정사항을 정리한다.

## Phase 0. 저장소/개발 환경 셋업

- 모노레포 구조(`backend/`, `frontend/`, `docs/`), FastAPI + Uvicorn + SQLAlchemy + Alembic, `docker-compose.yml`(postgres), React+Vite+TS 프론트엔드, ruff/black + CI 워크플로까지 스캐폴딩 완료 상태에서 시작.

### 트러블슈팅: 로컬 폴더명 리네임

- 배경: 로컬 폴더명(`katecam-todo-tracker`)과 GitHub 저장소명/의도한 이름(`katecam-schedule-tracker`)이 어긋나 있었음.
- 조치: `docker-compose.yml`에 `name: katecam-schedule-tracker` 고정 → 기존 컨테이너/볼륨 정리 → 로컬 폴더명 리네임 → 새 경로에서 세션 재시작.
- 리네임 후 발견된 잔재: `backend/.venv`의 `pyvenv.cfg`와 `Scripts/activate*`에 옛 경로(`katecam-todo-tracker/backend/.venv`)가 하드코딩되어 있었음 → `.venv` 삭제 후 새 경로에서 재생성으로 해결.
- Docker Desktop이 꺼져있어 최초 확인 때 컨테이너/볼륨 정리 여부를 못 봤다가, 이후 다시 켠 뒤 확인 — 옛 이름(`katecam-todo-tracker-*`) 잔여물 없음, 볼륨은 `katecam-schedule-tracker_db_data` 하나만 존재함을 확인.

### 트러블슈팅: CI가 실제로는 실패하는 상태였음

- alembic이 자동 생성한 마이그레이션 파일(`9df94d8b18d6_init_user_team_schedule_models.py`)이 ruff(import 정렬, 라인 100자 초과)와 black 포맷을 통과하지 못하는 상태로 커밋되어 있었음.
- CI의 backend job이 `ruff check .` / `black --check .`를 실제로 실행하므로, 이 상태로 push하면 CI가 실패함을 실행해서 직접 확인.
- `ruff --fix` + `black .`로 포맷만 수정(로직 변경 없음), 재검증 후 커밋.

## Phase 1. 데이터 모델 & 마이그레이션

- `User`(user_id UUID PK, email unique, password, nick_name, permission Enum, timestamps), `Team`/`TeamMember`(복합 PK + unique 제약, TeamMember는 updated_at 없음), `Schedule`/`ScheduleCompletion`(복합 PK) 모델 구현.
- `TimestampMixin`(created_at + updated_at, onupdate)/`CreatedAtMixin`(created_at만) 공통 처리.
- 시드 스크립트(`scripts/seed.py`): dev 1 / manager 1 / student 3 / team 1 / schedule 2건(shared+personal).
- 검증: 실제 DB에 마이그레이션 적용 → ORM으로 insert/update 반복 실행해 unique/FK/복합PK 제약 위반 시 에러 발생 확인, updated_at만 갱신되고 created_at은 불변임을 실측.

## Phase 2. 인증 (Auth)

### 구현 항목

| 항목 | 내용 |
|---|---|
| 2-1 비밀번호 해싱 | `app/core/security.py` — passlib bcrypt `hash_password`/`verify_password` |
| 2-2 회원가입 | `POST /auth/signup` — 이메일/비밀번호(8자 이상)/닉네임, 미인증 User 생성, 인증 토큰을 로그로 "발송"(dev 스텁) |
| 2-3 이메일 인증 | `GET /auth/verify?token=...` — JWT 서명 기반 stateless 토큰(DB에 토큰 저장 안 함), idempotent |
| 2-4 로그인/JWT | `POST /auth/login` — access token(30분, 응답 바디) + refresh token(90일, httpOnly+Secure+SameSite=lax 쿠키) |
| 2-5 Refresh | `POST /auth/refresh` — 쿠키의 refresh token 검증 후 access+refresh 재발급(rotation) |
| 2-6 로그아웃 | `POST /auth/logout` — 서버 상태 없이 쿠키 삭제만 |
| 2-7 인증 미들웨어 | `app/api/deps.py` — `get_current_user`(Bearer 토큰 검증), `require_permission(*allowed)`(권한 allowlist 팩토리) |
| 2-8 Rate limiting | `app/core/rate_limit.py` — IP 기준 초당 10회 초과 시 60초 임시 차단 (ASGI 미들웨어) |

`GET /users/me` (Phase 3-1 항목이지만 2-7 인증 미들웨어를 실제로 검증할 protected 엔드포인트가 필요해서 최소 형태로 조기 구현).

### 원 계획 대비 변경된 결정사항

- **Refresh token 만료: 14일 → 90일.** "로그아웃 안 하면 최대한 로그인 유지"라는 접근성 요구사항 때문에, rotation을 통한 sliding session으로 사실상 장기 로그인 유지를 노리되 완전 무기한은 탈취 리스크가 있어 90일로 절충.
- **Refresh rotation을 완전 stateless로 단순화.** 원래 PRD는 "폐기된 refresh token으로 재요청 시 401"을 요구했는데, 이건 서버가 발급된/폐기된 토큰을 어딘가 저장해야만 가능 — 그런데 PRD의 다른 문장은 "서버 측 세션 저장을 안 둔다"고 명시해서 자기모순이었음. 논의 후 **RefreshToken 테이블 없이 완전 stateless 유지**(재사용 가능한 refresh token, 폐기 추적 없음)로 결정. 대신 90일 만료가 유일한 안전판.
- **Rate limit: 초당 5회 → 10회.**
- **Rate limit 기준: "동일 사용자" → 동일 IP.** PRD 원문은 사용자 단위였지만, signup/login처럼 인증 전 요청도 보호해야 해서 IP 기준으로 구현. 검토 후 문서를 실제 구현에 맞춰 수정.
- **이메일 인증은 GET 유지.** POST가 REST 원칙상 더 맞다는 논의가 있었으나, 이메일의 `<a href>` 링크는 GET만 발생시킬 수 있어 POST로 바꾸려면 프론트엔드 중간 페이지가 필요 — UX 단순성을 위해 GET 유지 결정.
- **이메일 발송은 개발용 로그 스텁.** AWS SES 연동은 실제 배포 단계로 미룸(로그에 인증 링크만 출력).

### 트러블슈팅

- **JWT `jti` 누락으로 인한 rotation 버그.** refresh token의 payload가 `sub`/`purpose`/`exp`만 있었는데, `exp`가 초 단위로 잘리다 보니 로그인 직후 같은 1초 안에 refresh를 호출하면 "새로 발급한" 토큰이 이전 토큰과 문자 그대로 동일해지는 문제 발견(자동화 테스트 작성 중 발견). `jti`(랜덤 UUID)를 payload에 추가해 항상 유니크하도록 수정.
- **TestClient에서 Secure 쿠키가 안 돌아오는 문제.** `fastapi.testclient.TestClient`의 기본 base_url이 `http://testserver`라서, httpx 쿠키 저장소가 `Secure` 속성이 붙은 refresh 쿠키를 다음 요청에 자동으로 실어 보내지 않음(http는 secure 컨텍스트가 아니므로). `TestClient(app, base_url="https://testserver")`로 해결.
- **Rate limit 미들웨어가 테스트끼리 간섭하는 문제.** 모든 `TestClient` 요청이 동일한 가짜 client host(`testclient`)로 잡히기 때문에, IP 기준 카운터가 테스트 케이스를 넘나들며 누적되어 서로 관련 없는 테스트가 429로 실패할 수 있었음. 미들웨어의 상태를 인스턴스 변수에서 모듈 레벨로 옮기고 `reset_rate_limit_state()`를 노출, `conftest.py`에서 매 테스트 전 리셋하도록 처리.
- **Windows 환경 특유의 자잘한 이슈들.** `ps`/`pkill`이 Windows 프로세스를 제대로 못 잡아 stray uvicorn/vite 프로세스가 포트를 물고 있던 문제(→ `taskkill //F //IM python.exe`로 정리), vite가 기본 바인딩하는 `localhost`(IPv6)와 `curl`이 지정한 `127.0.0.1`(IPv4)이 달라 연결이 안 되던 문제(→ `localhost`로 재시도).

### 테스트 인프라

- 처음엔 curl로 수동 통합 테스트만 하다가, Phase 2가 끝난 시점에 자동화로 전환.
- `backend/tests/conftest.py`: 별도 `katecam_test` DB(없으면 자동 생성) + `get_db` dependency override + 매 테스트 후 테이블 정리 + rate limit 상태 리셋.
- `backend/tests/test_auth.py`(19개), `test_rate_limit.py`(3개), `test_security.py`(3개) — 총 25개 테스트로 회원가입/이메일인증/로그인/refresh/로그아웃/`/users/me`/rate limit 전 시나리오 커버.
- `.github/workflows/ci.yml`: backend job에 Postgres 서비스 컨테이너 추가, `alembic upgrade head` + `pytest` 스텝 추가(이전에는 CI에 테스트 실행 자체가 없었음).

## 현재 상태

Phase 0, 1, 2 전부 구현 완료 및 검증 완료. 다음은 Phase 3(핵심 CRUD API — User/Team/Schedule, 권한 분리).
