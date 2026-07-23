# 카테캠 주간 트래커 — 구현 순서 (Implementation Plan)

> Trimmed-PRD.md(결정 반영본)를 근거로 작성한 실행 순서 문서. 각 Phase는 이전 Phase의 산출물에 의존하므로 순서를 지켜 진행하는 것을 권장. 각 Step에는 완료 기준(verify)을 명시해 자체 검증 가능하도록 함.
>
> 저장소 구조 가정: 모노레포 (`backend/`, `frontend/` 디렉토리 분리)
> Agent(크롤링) 파트는 MVP 범위(수동 텍스트 입력 → Agent 분석 → Approve → 반영)만 상세히 다루고, MVP 이후 자동 크롤링/스케줄러는 개략적으로만 언급.

---

## Phase 0. 저장소/개발 환경 셋업

목표: 코드를 작성하기 전 프로젝트 골격과 로컬 개발 환경을 갖춘다.

0-1. 모노레포 디렉토리 구조 생성
   - `backend/` (FastAPI), `frontend/` (React + Vite), `docs/` (기존 유지)
   - verify: `tree` 또는 `ls`로 최상위 구조 확인

0-2. 백엔드 프로젝트 초기화
   - FastAPI, Uvicorn, SQLAlchemy(or SQLModel), Alembic(마이그레이션), Pydantic, python-jose/pyjwt, passlib[bcrypt], python-dotenv 의존성 확정
   - `pyproject.toml` 또는 `requirements.txt` 작성
   - verify: `uvicorn main:app`으로 빈 FastAPI 앱이 뜨고 `/health` 200 응답

0-3. PostgreSQL 로컬 환경 (Docker Compose)
   - `docker-compose.yml`에 postgres 서비스 정의 (결정: EC2 Docker → 추후 RDS)
   - `.env.example` 작성 (DB_URL, JWT_SECRET 등 플레이스홀더만, 실값은 `.env`에 gitignore)
   - verify: `docker compose up -d db` 후 `psql`로 접속 확인

0-4. 프론트엔드 프로젝트 초기화
   - React + Vite (CSR, 결정 #9), TypeScript 권장
   - verify: `npm run dev`로 기본 페이지 렌더링 확인

0-5. Lint/format 및 CI 뼈대
   - 백엔드: ruff/black, 프론트: eslint/prettier
   - GitHub Actions로 최소 lint + test 워크플로 추가 (선택이나 권장)
   - verify: `git push` 시 CI가 트리거되고 통과

---

## Phase 1. 데이터 모델 & 마이그레이션

목표: PRD의 데이터 모델(초안)을 실제 DB 스키마로 구현. 이후 모든 API가 이 스키마 위에서 동작하므로 최우선.

1-1. `User` 테이블
   - `user_id: UUID (PK)`, `email: str (unique)`, `password: str (bcrypt hash)`, `nick_name: str | None`, `permission: Enum['dev','manager','student']`, `created_at: DateTime`, `updated_at: DateTime`
   - verify: Alembic 마이그레이션 적용 후 psql에서 테이블/제약조건 확인 (email unique index 포함), insert 시 created_at/updated_at 자동 채워짐, update 시 updated_at만 갱신됨

1-2. `Team` / `Team_Member` 테이블 (결정 #14/#15, N:M)
   - `Team(team_id: UUID PK, name: str, created_at: DateTime, updated_at: DateTime)`
   - `Team_Member(team_id: UUID FK, user_id: UUID FK, created_at: DateTime)` — 복합 PK 또는 unique(team_id, user_id). 배정 관계 자체는 수정 대상이 아니라 생성/삭제만 있으므로 updated_at은 두지 않음
   - verify: FK 제약 확인, 동일 (team_id, user_id) 중복 삽입 시 에러 발생 확인, Team row는 이름 변경 시 updated_at 갱신 확인

1-3. `Schedule` / `Schedule_Completion` 테이블 (통합 모델, 결정 #3/#4/#7)
   - `Schedule(schedule_id: UUID PK, kind: Enum['personal','shared'], title, contents, deadline: DateTime, owner_id: UUID | None FK, created_at: DateTime, updated_at: DateTime)` — `owner_id`는 원래 `student_id`였으나 Phase 3 진행 중 "개인 일정은 학생뿐 아니라 모든 권한이 가질 수 있음"이 확인되어 명칭 변경(마이그레이션으로 rename)
   - `Schedule_Completion(schedule_id: UUID FK, owner_id: UUID FK, done: bool, created_at: DateTime, updated_at: DateTime)` — 복합 PK (schedule_id, owner_id). 기존 `updated_at`은 "완료 상태가 마지막으로 바뀐 시각"으로 유지, `created_at`은 row가 최초 upsert된 시각(=최초로 상태를 건드린 시각)
   - verify: row 없을 때 애플리케이션 레벨에서 `done=false` 기본 처리 로직이 필요함을 주석/문서로 남김 (DB 레벨 기본값 아님 — PRD 명시사항). Schedule 수정 시 updated_at만 갱신되고 created_at은 불변인지 테스트

1-3-1. created_at/updated_at 공통 처리 방식
   - ORM 레벨(SQLAlchemy) 공통 Mixin/Base로 구현: `created_at`은 insert 시 서버 타임스탬프로 1회만 설정, `updated_at`은 insert/update 시마다 갱신 (DB `onupdate` 트리거 또는 ORM 이벤트 훅 중 택1, 팀 내부 컨벤션에 맞춰 통일)
   - 모든 테이블(User/Team/Team_Member/Schedule/Schedule_Completion)에 동일하게 적용
   - verify: 아무 테이블이나 하나 골라 row 생성 후 즉시 update, created_at은 그대로이고 updated_at만 바뀌었는지 확인

1-4. 시드 스크립트 (개발용)
   - dev 계정 1개, manager 1개, student 여러 명, 샘플 Schedule 몇 건
   - verify: 시드 실행 후 각 permission별 최소 1 row 존재 확인

---

## Phase 2. 인증 (Auth)

> **MVP 범위 축소 (Phase 6 착수 전 결정).** 이메일 인증(2-2/2-3, AWS SES 연동 포함)과 rate limiting(2-8)을 실제로는 끄기로 함 — 학생 규모(200명 안팎)에서 악용 가능성이 낮다고 판단, 이메일 인증은 실제 메일 발송 인프라(SES 샌드박스 해제 등) 구축 비용 대비 이득이 낮음. 회원가입 시 `is_verified=True`로 즉시 활성화하고, 악용 계정은 관리자가 직접 삭제(Phase 3-1 계정 관리 기능)하는 방식으로 대응. rate limiting은 `RATE_LIMIT_ENABLED=false`가 기본값. 두 기능 모두 코드/테스트는 삭제하지 않고 주석 처리 또는 스킵 처리로 남겨서 필요해지면 다시 켤 수 있게 함 — 이에 따라 **Phase 6 배포에는 SES 연동이 포함되지 않음**.

목표: 이메일 인증 기반 회원가입/로그인과 JWT 발급 체계 (결정 #10/#12/#21) 구현. 이후 모든 API가 인증에 의존하므로 Phase 1 다음으로 최우선.

2-1. 비밀번호 해싱 유틸
   - bcrypt로 hash/verify 함수 작성 (결정 #12)
   - verify: 유닛 테스트 — 같은 비밀번호도 매번 다른 해시가 나오되 verify는 true

2-2. 회원가입 API (이메일 인증 전 단계)
   - `POST /auth/signup`: email, password(최소 8자, 결정 #21), nick_name 입력 → 미인증 상태 User row 생성
   - 이메일 인증 토큰 생성 및 발송 (AWS SES 연동, PRD "외부 연동" 항목)
   - verify: 회원가입 후 DB에 미인증 상태 row 존재, 인증 메일이 (개발 환경에서는 로그/Mailtrap 등으로) 발송됨

2-3. 이메일 인증 확인 API
   - `GET /auth/verify?token=...` → User 인증 상태로 전환
   - 동일 이메일 중복 가입 방지 로직 확인 (unique constraint + 애플리케이션 레벨 체크)
   - verify: 미인증 상태로 로그인 시도 시 거부됨을 테스트

2-4. 로그인 / JWT 발급
   - `POST /auth/login`: access token(30분, 응답 바디/헤더로 전달) + refresh token(90일, httpOnly+Secure 쿠키) 동시 발급
   - verify: 로그인 응답에 access token 포함, Set-Cookie에 httpOnly+Secure 속성 확인 (curl -v 또는 브라우저 devtools)

2-5. Refresh / Rotation
   - `POST /auth/refresh`: 기존 refresh token으로 새 access+refresh 발급, 기존 refresh는 즉시 폐기
   - verify: 폐기된 refresh token으로 재요청 시 401

2-6. 로그아웃
   - 클라이언트 쿠키 삭제로 처리 (서버 세션 저장 없음, PRD 명시)
   - verify: 로그아웃 후 쿠키가 클라이언트에서 삭제됨

2-7. 인증 미들웨어 / 의존성 주입
   - FastAPI `Depends`로 `get_current_user`, permission 체크 데코레이터/dependency 작성 (dev > manager > student)
   - verify: 인증 없이 보호된 엔드포인트 호출 시 401, 권한 부족 시 403

2-8. Rate limiting (결정 #19)
   - 애플리케이션 레벨 구현 (Nginx/Gateway 아님), 동일 IP 초당 10회 이상 시 임시 블락 (로그인 전 signup/login도 보호해야 하므로 IP 단위)
   - verify: 짧은 시간에 10회 이상 요청 시 이후 요청이 차단됨을 테스트

---

## Phase 3. 핵심 CRUD API (권한 분리 포함)

목표: PRD "핵심 기능" 0/1/2/3 계층을 구현. Phase 2의 인증/권한 의존성 위에서 진행.

3-1. User 관리 API
   - `GET /users/me` (본인 조회)
   - `GET /users/{id}` (manager/dev 모두 전체 유저 조회 가능 — 팀 소속, 대상의 권한과 무관하게 제한 없음)
   - `PATCH /users/{id}/permission` (student ↔ manager 양방향 변경, **manager/dev 모두 가능** — PRD 결정 #2에서 "manager 본인은 승격 불가"였던 것을 변경. dev 전용 규칙(개발자 권한 자체는 DB 직접 조작으로만 부여, 웹 UI로 dev 승격/강등 불가)은 그대로 유지)
   - verify: manager 계정으로 student를 manager로 승격 시 200, manager를 student로 강등 시 200, 대상이 dev이거나 요청 결과가 dev가 되는 경우는 manager/dev 모두 403 (dev 권한 변경은 여전히 DB 직접 조작만 가능)

3-2. Team CRUD
   - `POST /teams` (manager/dev만, 결정 #4/#6)
   - `GET /teams`, `GET /teams/{id}/members`
   - verify: student 계정으로 팀 생성 시도 시 403

3-3. Team_Member CRUD (팀 배정, 결정 #4)
   - `POST /teams/{id}/members` — manager/dev/학생 본인 모두 가능 (본인 user_id만 등록 가능하도록 student 권한 제한)
   - `DELETE /teams/{id}/members/{user_id}` — 동일 권한 규칙
   - verify: student A가 student B를 팀에 넣으려 하면 403, 본인을 넣으면 200

> **프론트엔드 달력 UI 확정에 따른 재설계 (3-4~3-7)**: 학생/운영진/개발자 화면 모두 "월 단위 큰 달력에 공유+개인 일정이 섞여서 표시, 클릭 시 상세" 형태로 확정됨(Phase 5 참고). 이에 따라 기존 "공유 조회/개인 조회/타 유저 조회"로 흩어져 있던 GET을 **달력 조회용 통합 엔드포인트 하나**로 합침. CUD(생성/수정/삭제)는 기존처럼 공유/개인이 분리된 채로 유지.

3-4. Schedule 조회 — 달력용 통합 조회
   - `GET /schedules?year=&month=&student_id=(선택)` — 해당 월에 걸리는 schedule을 kind 구분 없이(shared+personal 섞어서) 반환, 각 항목에 그 student 기준 완료 여부(done) 포함
   - `student_id` 생략 시 본인 기준. student가 본인 아닌 `student_id`를 지정하면 403
   - manager/dev는 `student_id` 지정 가능 — 팀 소속과 무관하게 임의의 student 지정 가능 (3-1과 동일 원칙), 미지정 시 400
   - verify: 월 경계(예: 그 달 1일 마감/말일 마감)에 걸치는 일정이 포함되는지, student가 타 student_id로 조회 시 403, manager가 임의 student_id로 조회 시 200

3-5. Schedule CRUD — 공유 일정 (kind='shared')
   - `POST/PATCH/DELETE /schedules` (manager/dev만, 결정)
   - verify: student 계정으로 공유 일정 생성 시 403

3-6. Schedule CRUD — 개인 일정 (kind='personal')
   - 본인 소유 owner_id로만 CRUD 가능 (student뿐 아니라 모든 권한이 개인 일정을 가질 수 있음, PRD "0. 공통" 참고)
   - verify: 타 유저의 개인 일정에 접근 시 403/404

3-7. Schedule_Completion (진행 상황 업데이트)
   - `PUT /schedules/{id}/completion` — upsert 방식 (row 없으면 생성, 있으면 done/updated_at 갱신)
   - row 없을 때 3-4 통합 조회에서 애플리케이션 레벨으로 `done=false` 응답하는 로직 구현 (Phase 1-3에서 남긴 주석의 실제 구현)
   - verify: completion row가 없는 schedule이 3-4 조회에서 done=false로 응답, PUT 이후 실제 row 생성 및 반영 확인

---

## Phase 4. Agent 기반 일정 추가 계획 (MVP 크롤링 파트)

목표: PRD MVP 핵심 — "수동 텍스트 입력 → Agent 분석 → 사람 Approve → 실제 반영 → 반영 전 백업" 흐름 구현. Phase 3 Schedule CRUD 완료 후 진행 (Agent가 결국 Schedule을 C/U 하므로).

> **`docs/Frontend-Feature-Spec.md` 기준 재설계.** 원래 이 Phase는 "계획(Plan) 전체를 통째로 approve/reject"하는 구조였는데, 프론트엔드 화면 명세를 구체화하면서 **"하나의 원문 텍스트에서 나온 제안들을 카드 단위로 개별 승인/거절"**하는 것으로 변경됨. 아래 4-1~4-6은 이 변경을 반영해 다시 작성.

4-1. 텍스트 입력 API
   - `POST /crawl-texts` (dev 전용) — Discord/Notion 내용을 수동 복사한 원문 텍스트 저장
   - 요청 필드: `source: 'notion' | 'discord'`, `channel: str | None`(discord일 때만 — 예: "공지방", "학습공지방"), `raw_text: str`
   - Agent가 출처/채널별로 나뉘므로(2-4 참고: Notion 1개 + Discord는 채널별 Sub-Agent), 저장 시점에 어느 Agent가 처리해야 할지 구분할 수 있어야 함
   - verify: dev 계정만 호출 가능, 저장된 원문 row에 source/channel 확인

4-2. Agent 분석 → "제안 카드" 생성
   - Claude API 호출(Tool use로 구조화된 출력 강제): 원문 텍스트 → create/update 제안 목록(JSON). **delete는 Agent가 제안하지 않음** — 삭제는 항상 사람이 직접 수행
   - 파싱 실패 시 최대 3회까지 재시도, 계속 실패하면 "파싱 실패" 상태로 표시(사람이 원문을 보고 직접 처리)
   - 근거는 카드별 스니펫을 따로 만들지 않고, 카드들이 속한 원문 텍스트(`raw_text_id`)를 참조해서 화면에서 원문을 한 번만 보여주는 방식(2-5b 참고)
   - 신규 테이블 `ScheduleProposal`: `proposal_id(PK), raw_text_id(FK), action('create'|'update'), title, contents, deadline, target_schedule_id(UUID|None, update일 때만 대상 Schedule 참조), status('pending'|'approved'|'rejected'|'parse_failed'), created_at, updated_at`
   - 기존 계획에 있던 plan 전체 단위의 `Schedule_Plan` 테이블은 두지 않음 — **status를 포함한 모든 상태가 `ScheduleProposal`(카드) 레벨**에 있음. 원문 텍스트(`CrawlText`)는 여러 `ScheduleProposal`을 가질 수 있는 1:N 관계
   - verify: 샘플 텍스트로 호출 시 사람이 읽을 수 있는 `ScheduleProposal` row들이 저장됨(각각 독립적으로 pending 상태)

4-3. 제안 카드 조회/Approve API
   - `GET /crawl-texts/{id}` — 원문 텍스트 조회(카드 묶음 상단에 표시/링크용)
   - `GET /schedule-proposals?raw_text_id=` (dev 조회) — 특정 원문에 딸린 카드들, 혹은 전체 카드 목록(원문 텍스트 단위로 그룹핑해서 반환)
   - `POST /schedule-proposals/{id}/approve` / `POST /schedule-proposals/{id}/reject` — **카드(개별 제안) 단위**로 호출
   - verify: reject 시 Schedule 테이블 변경 없음(해당 카드만 rejected), approve 시 그 카드 하나만 실제 반영, 같은 원문의 다른 카드는 영향 없음(부분 승인 확인)

4-4. 백업 생성 (Approve 직전, 결정 #11 — EC2 로컬 폴더)
   - approve 처리 직전, **그 카드가 영향을 주는 Schedule row 하나**를 JSON/CSV로 스냅샷하여 로컬 폴더에 파일로 저장(파일명에 timestamp+proposal_id)
   - `action='create'`인 카드는 되돌릴 "이전 상태"가 없으므로 백업을 만들 필요 없음(생성 자체가 새 row라 스냅샷 대상이 없음) — `action='update'`인 카드만 approve 직전 기존 Schedule row를 백업
   - 카드 단위 백업이라 파일 수가 늘어날 수 있지만, 사용자 규모(200명 안팎)를 고려하면 부담 크지 않다고 판단(Frontend-Feature-Spec.md 결정 로그)
   - verify: update 카드 approve 시 백업 파일이 먼저 생성되고 그 다음에만 실제 Schedule U가 실행되는 순서 확인(백업 실패 시 반영 중단), create 카드는 백업 없이 바로 반영되는지 확인

4-5. Approve 반영 로직
   - 카드의 `action`에 따라 실제 Schedule 테이블에 반영(create면 새 Schedule 생성, update면 `target_schedule_id`의 Schedule을 수정)
   - PRD 원칙: "Agent는 CR은 자유롭게, UD는 가급적 사람 승인 후"만 — 이번 흐름은 애초에 전부 사람이 approve하므로 원칙을 만족
   - approve 반영 실패 시 카드 상태를 pending으로 되돌리고 프론트에 에러 표시(2-5c)
   - verify: approve 후 Schedule 테이블에 실제 반영, update의 경우 백업 파일과 diff 비교 가능

4-6. (참고, MVP 이후) 자동 크롤링/스케줄러
   - MVP 이후 단계: Discord/Notion 권한 확보 시 4-1의 수동 입력을 자동 수집으로 대체
   - APScheduler(AsyncIOScheduler + CronTrigger, Asia/Seoul 정오, 결정 #8)로 4-1~4-2 파이프라인을 자동 트리거
   - 수동 실행 엔드포인트(dev 전용)와 스케줄 트리거가 동일 함수를 공유하도록 설계 (PRD 명시)
   - uvicorn 멀티워커 사용 시 크롤링 중복 실행 방지 위해 크롤링 담당 프로세스는 단일 워커로 운영
   - 이번 구현 순서에서는 설계만 남기고 실제 구현은 MVP 이후로 미룸
   - **참고(범위 밖)**: Discord 음악추천채널 전용 Agent는 매일 9시 자동 종합 실행이 계획되어 있으나(Frontend-Feature-Spec.md 2-5e) 아직 설계 확정 전 — 이번 Phase 4 구현 범위에 포함하지 않음. 다만 크롤링 파이프라인을 "채널별로 다른 처리(schedule 추출이 아닌 다른 종류의 콘텐츠도 있을 수 있음)"를 나중에 얹기 쉬운 구조로 짜두면 좋음

---

## Phase 5. 프론트엔드

목표: 위 API들을 사용하는 React(Vite, CSR) 화면 구현. Phase 2~4의 API가 어느 정도 안정화된 뒤 병행 가능하나, 최소 Phase 2(인증)는 선행되어야 함.

5-1. 인증 화면
   - 회원가입/이메일 인증 안내/로그인/로그아웃
   - access token 저장 전략 (메모리 or 짧은 수명 스토리지), refresh는 쿠키이므로 프론트에서 직접 접근 안 함
   - verify: 로그인 → 보호된 페이지 접근 → 로그아웃 → 접근 차단 흐름 수동 테스트

5-2. 대시보드 (학생 기본 화면) — 달력 UI
   - 월 단위 큰 달력. 각 날짜 박스 안에 그 날짜가 마감인 일정이 작은 박스로 표시됨 (공유/개인은 색 또는 아이콘으로만 구분, 같은 달력에 섞어서 표시)
   - 일정 박스 클릭 → 상세 정보(제목/내용/마감/완료 여부) 확인, 완료 체크 토글
   - 이전 달/다음 달 이동 (`GET /schedules?year=&month=`)
   - 개인 일정 CRUD(생성/수정/삭제)는 달력 위에서 직접 조작
   - verify: 학생 계정으로 로그인 후 달력에 공유+개인 일정이 섞여서 보이고, 클릭 시 상세 확인, 완료 체크 토글 확인, 이전/다음 달 이동 확인

5-3. 운영진 화면 — 학생 화면 + 사이드바
   - 메인 영역은 5-2와 동일한 달력 UI (다만 공유 일정 CRUD 버튼 노출)
   - 좌측 사이드바에 탭 2개:
     - "학생" 탭: 전체 학생 가나다순 flat list
     - "팀" 탭: 팀 가나다순, 아코디언으로 접고 펼치면 소속 학생 표시 (`GET /teams`, `GET /teams/{id}/members` 사용)
   - 사이드바에서 학생 선택 시 메인 달력이 그 학생의 달력으로 전환 (`GET /schedules?year=&month=&student_id=`)
   - 팀 소속과 무관하게 사이드바의 아무 학생이나 선택해 조회 가능 (3-1/3-4 결정과 동일 원칙)
   - verify: 학생 탭/팀 탭 전환 및 아코디언 펼침/접힘 동작, 학생 선택 시 그 학생 달력으로 전환, manager 계정 권한 범위 내에서만 버튼 노출(프론트 가드는 UX용, 실제 권한은 백엔드가 최종 판단)

5-4. 개발자 화면
   - 1차로는 5-3(운영진 화면)과 완전히 동일하게 구현
   - 전체 계정 관리/permission 승격 UI, 텍스트 입력 → Agent 계획 조회/Approve/Reject 화면(Phase 4 연동)은 이후 별도 단계에서 추가
   - verify: dev 계정으로 운영진 화면과 동일하게 동작하는지 확인

---

## Phase 6. 배포

> **RDS는 쓰지 않고 db까지 포함해 전부 EC2 위 Docker Compose로 배포하기로 확정.** 초안의 "우선 EC2 Docker, 추후 RDS 이관" 방향 그대로 — 현재 규모(200명 안팎)에서는 RDS로 옮길 필요가 없다고 판단. 프론트엔드도 별도 S3+CloudFront 없이 같은 EC2에서 Docker Compose로 함께 서빙(로컬 개발 구성과 최대한 동일하게 유지해 배포/디버깅 복잡도를 낮춤). 이메일 인증을 껐으므로(Phase 2 참고) SES 연동도 이번 배포 범위에 없음.

목표: AWS EC2 단일 인스턴스에 Docker Compose로 전체 스택(db+backend+frontend) 배포, HTTPS 적용까지 (결정 #11 백업은 EC2 로컬 폴더 유지).

6-1. EC2 인스턴스 준비
   - 인스턴스 생성, Docker/Docker Compose 설치, 보안 그룹에서 80/443(및 임시로 8000/5173) 오픈
   - verify: EC2에 SSH 접속해 `docker compose version` 확인

6-2. 프로덕션용 Docker Compose 배포 (db+backend+frontend 전부 EC2에)
   - 로컬 `docker-compose.yml`과 동일 구조 유지, backend `--reload` 제거 등 프로덕션에 맞게 조정
   - db 컨테이너 볼륨은 EC2 로컬 디스크에 유지(RDS 미사용)
   - verify: EC2에서 `docker compose up -d` 후 backend `/health`와 frontend 응답 확인

6-3. 환경변수/시크릿 관리
   - `.env`는 EC2에만 배치, git에는 커밋하지 않음(`JWT_SECRET`, `PROXY_TOKEN` 등)
   - verify: 저장소에 시크릿이 커밋되지 않았는지 재확인, EC2 `.env` 파일 권한 제한

6-4. HTTPS 설정 (refresh 쿠키가 Secure 속성이므로 필수)
   - Nginx(또는 Caddy) 리버스 프록시 + Let's Encrypt(certbot)으로 인증서 발급, HTTP→HTTPS 리다이렉트
   - verify: 배포된 도메인에서 로그인~완료체크~Agent 계획 승인까지 전체 플로우 1회 수동 통과

6-5. (참고, 범위 밖) 이메일 발송 / RDS 이관
   - 이메일 인증은 Phase 2에서 이미 MVP 범위 밖으로 뺐으므로 SES 연동은 불필요
   - 사용자 규모가 늘어나 RDS 이관이 실제로 필요해지면 별도 단계로 진행

---

## 진행 체크리스트 요약

| Phase | 내용 | 선행 조건 |
|---|---|---|
| 0 | 저장소/환경 셋업 | 없음 |
| 1 | 데이터 모델/마이그레이션 | Phase 0 |
| 2 | 인증(JWT/이메일) | Phase 1 |
| 3 | 핵심 CRUD(User/Team/Schedule) | Phase 2 |
| 4 | Agent 계획→Approve→백업 | Phase 3 |
| 5 | 프론트엔드 | Phase 2 (최소), Phase 3~4와 병행 가능 |
| 6 | 배포 | Phase 1~5 완료 |
