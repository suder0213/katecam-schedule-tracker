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
   - `Schedule(schedule_id: UUID PK, kind: Enum['personal','shared'], title, contents, deadline: DateTime, student_id: UUID | None FK, created_at: DateTime, updated_at: DateTime)`
   - `Schedule_Completion(schedule_id: UUID FK, student_id: UUID FK, done: bool, created_at: DateTime, updated_at: DateTime)` — 복합 PK (schedule_id, student_id). 기존 `updated_at`은 "완료 상태가 마지막으로 바뀐 시각"으로 유지, `created_at`은 row가 최초 upsert된 시각(=최초로 상태를 건드린 시각)
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
   - `GET /users/{id}` (dev만 전체 조회, manager는 소속 학생만)
   - `PATCH /users/{id}/permission` (student → manager 승격, **manager/dev 모두 가능** — PRD 결정 #2에서 "manager 본인은 승격 불가"였던 것을 변경. dev 전용 규칙(개발자 권한 자체는 DB 직접 조작으로만 부여, 웹 UI로 dev 승격 불가)은 그대로 유지)
   - verify: manager 계정으로 student를 manager로 승격 시 200, 승격 대상이 이미 dev이거나 승격 결과가 dev가 되는 요청은 manager/dev 모두 403 (dev 승격은 여전히 DB 직접 조작만 가능)

3-2. Team CRUD
   - `POST /teams` (manager/dev만, 결정 #4/#6)
   - `GET /teams`, `GET /teams/{id}/members`
   - verify: student 계정으로 팀 생성 시도 시 403

3-3. Team_Member CRUD (팀 배정, 결정 #4)
   - `POST /teams/{id}/members` — manager/dev/학생 본인 모두 가능 (본인 user_id만 등록 가능하도록 student 권한 제한)
   - `DELETE /teams/{id}/members/{user_id}` — 동일 권한 규칙
   - verify: student A가 student B를 팀에 넣으려 하면 403, 본인을 넣으면 200

3-4. Schedule CRUD — 공유 일정 (kind='shared')
   - `POST/PATCH/DELETE /schedules` (manager/dev만, 결정)
   - `GET /schedules?kind=shared` (전체 학생 조회 가능)
   - verify: student 계정으로 공유 일정 생성 시 403, 조회는 200

3-5. Schedule CRUD — 개인 일정 (kind='personal')
   - 본인 소유 student_id로만 CRUD 가능
   - verify: 타 학생의 개인 일정에 접근 시 403/404

3-6. Schedule_Completion (진행 상황 업데이트)
   - `PUT /schedules/{id}/completion` — upsert 방식 (row 없으면 생성, 있으면 done/updated_at 갱신)
   - row 없을 때 조회 시 애플리케이션 레벨에서 `done=false`로 응답하는 로직 구현 (Phase 1-3에서 남긴 주석의 실제 구현)
   - verify: completion row가 없는 schedule을 조회해도 done=false로 응답, PUT 이후 실제 row 생성 확인

3-7. 특정 User 일정 조회 (권한 분리, PRD MVP 항목)
   - manager: 소속 학생의 개인 일정 진행상황 R
   - dev: 전체 조회
   - verify: manager가 비소속 학생 일정 조회 시 403

---

## Phase 4. Agent 기반 일정 추가 계획 (MVP 크롤링 파트)

목표: PRD MVP 핵심 — "수동 텍스트 입력 → Agent 분석 → 사람 Approve → 실제 반영 → 반영 전 백업" 흐름 구현. Phase 3 Schedule CRUD 완료 후 진행 (Agent가 결국 Schedule을 C/U 하므로).

4-1. 텍스트 입력 API
   - `POST /crawl-texts` (dev 전용) — Discord/Notion 내용을 수동 복사한 원문 텍스트 저장
   - verify: dev 계정만 호출 가능, 저장된 원문 row 확인

4-2. Agent 분석 → "추가 계획" 생성
   - Claude API 호출: 원문 텍스트 → 구조화된 일정 변경 계획(JSON: create/update 목록, 각 항목에 title/contents/deadline/근거 스니펫)
   - 계획은 DB에 별도 상태(예: `Schedule_Plan` 테이블: plan_id, raw_text_id, proposed_changes(JSON), status: pending/approved/rejected)로 저장 — 즉시 Schedule에 반영하지 않음
   - verify: 샘플 텍스트로 호출 시 사람이 읽을 수 있는 구조화된 JSON 계획이 저장됨

4-3. 계획 조회/Approve API
   - `GET /schedule-plans` (dev 조회)
   - `POST /schedule-plans/{id}/approve` / `POST /schedule-plans/{id}/reject`
   - verify: reject 시 Schedule 테이블 변경 없음, approve 시에만 실제 반영

4-4. 백업 생성 (Approve 직전, 결정 #11 — EC2 로컬 폴더)
   - approve 처리 직전, 영향받는 Schedule row들을 JSON/CSV로 스냅샷하여 로컬 폴더에 파일로 저장 (파일명에 timestamp+plan_id)
   - verify: approve 호출 시 백업 파일이 먼저 생성되고, 그 다음에만 실제 Schedule C/U가 실행되는 순서를 코드/테스트로 확인 (백업 실패 시 반영 중단되어야 함)

4-5. Approve 반영 로직
   - 계획의 create/update 항목을 실제 Schedule 테이블에 반영
   - PRD 원칙: "Agent는 CR은 자유롭게, UD는 가급적 사람 승인 후"만 — 이번 흐름은 애초에 전부 사람이 approve하므로 원칙을 만족
   - verify: approve 후 Schedule 테이블에 실제 반영, 백업 파일과 diff 비교 가능

4-6. (참고, MVP 이후) 자동 크롤링/스케줄러
   - MVP 이후 단계: Discord/Notion 권한 확보 시 4-1의 수동 입력을 자동 수집으로 대체
   - APScheduler(AsyncIOScheduler + CronTrigger, Asia/Seoul 정오, 결정 #8)로 4-1~4-2 파이프라인을 자동 트리거
   - 수동 실행 엔드포인트(dev 전용)와 스케줄 트리거가 동일 함수를 공유하도록 설계 (PRD 명시)
   - uvicorn 멀티워커 사용 시 크롤링 중복 실행 방지 위해 크롤링 담당 프로세스는 단일 워커로 운영
   - 이번 구현 순서에서는 설계만 남기고 실제 구현은 MVP 이후로 미룸

---

## Phase 5. 프론트엔드

목표: 위 API들을 사용하는 React(Vite, CSR) 화면 구현. Phase 2~4의 API가 어느 정도 안정화된 뒤 병행 가능하나, 최소 Phase 2(인증)는 선행되어야 함.

5-1. 인증 화면
   - 회원가입/이메일 인증 안내/로그인/로그아웃
   - access token 저장 전략 (메모리 or 짧은 수명 스토리지), refresh는 쿠키이므로 프론트에서 직접 접근 안 함
   - verify: 로그인 → 보호된 페이지 접근 → 로그아웃 → 접근 차단 흐름 수동 테스트

5-2. 대시보드 (학생 기본 화면)
   - 공유 일정 목록 + 완료 체크, 개인 일정 CRUD, 팀 소속 확인/변경
   - verify: 학생 계정으로 로그인해 각 기능 수동 조작 확인

5-3. 운영진 화면
   - 공유 일정 CRUD, 팀 생성, 소속 학생 일정 조회
   - verify: manager 계정 권한 범위 내에서만 버튼/화면 노출 (프론트 가드는 UX용, 실제 권한은 백엔드가 최종 판단)

5-4. 개발자 화면
   - 전체 계정 관리, permission 승격, 텍스트 입력 → Agent 계획 조회/Approve/Reject 화면
   - verify: dev 계정으로 전체 플로우(Phase 4) 수동 테스트

---

## Phase 6. 배포

목표: AWS EC2/RDS 기반 배포 (결정 #11 백업은 EC2 로컬 폴더 유지).

6-1. EC2에 Docker Compose로 backend+db 배포 (또는 db는 우선 EC2 Docker, 추후 RDS 이관)
6-2. 프론트엔드 빌드 산출물 배포 (S3+CloudFront 또는 동일 EC2 nginx 서빙)
6-3. 환경변수/시크릿 관리 (.env를 실제 서버에만 배치, git에는 커밋 금지)
6-4. HTTPS 설정 (refresh 쿠키가 Secure 속성이므로 필수)
   - verify: 배포된 도메인에서 로그인~완료체크~Agent 계획 승인까지 전체 플로우 1회 수동 통과

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
