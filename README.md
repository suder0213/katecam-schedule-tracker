# 🍪 카테캠 일정 트래커

카카오테크 캠퍼스(카테캠) 수강생용 일정 공유·추적 웹 서비스. Discord/Notion에 흩어진 공지·일정을 한곳에서 확인하고 완료 여부를 체크할 수 있게 하는 것을 목표로 한다. LLM(Agent)이 원문 텍스트에서 일정을 추출해 제안하고, 운영진/개발자가 검토·승인하는 반자동 파이프라인을 포함한다.

- **배포:** https://suderhome.com
- **문서:** `docs/` — PRD(`Trimmed-PRD.md`), 구현 계획(`Implementation-Plan.md`), Phase별 진행 요약(`Phase-0-2` ~ `Phase-7-Progress-Summary.md`)

## 주요 기능

- **인증** — 이메일/비밀번호 가입·로그인, JWT(access + refresh 쿠키)
- **권한 3단계** — 학생 / 운영진(manager) / 개발자(dev), 승격은 운영진·개발자가 웹 UI에서, 개발자 승격만 DB 직접 조작
- **일정** — 공유 일정(운영진/개발자가 생성) + 개인 일정(본인 CRUD), 월간 캘린더 뷰, 완료 체크, TODO(마감 임박순) 목록
- **팀** — 팀 생성(운영진/개발자), 가입/탈퇴(본인), 삭제(운영진/개발자)
- **Agent 검토** — Discord/Notion 원문 텍스트를 붙여넣으면 LLM이 일정 후보를 추출 → 운영진/개발자가 항목별로 수정·승인·거절 → 승인 시 공유 일정으로 반영
- **계정 관리** — 전체 계정 목록, 권한 변경(학생↔운영진), 계정 삭제(개발자 전용)

## 기술 스택

| 영역 | 스택 |
|---|---|
| 백엔드 | FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, python-jose(JWT), passlib(bcrypt), APScheduler, LangChain(OpenAI-호환 프록시) |
| 프론트엔드 | React 19, TypeScript, Vite, React Router, Tailwind CSS |
| 배포 | Docker Compose(db+backend+nginx), nginx(정적 서빙 + 리버스 프록시 + HTTPS), Let's Encrypt(certbot), AWS EC2 |
| CI/CD | GitHub Actions — lint/test/build 후 `main` push 시 EC2로 자동 배포 |

## 폴더 구조

```
backend/            FastAPI 앱
  app/
    api/routes/      auth, users, teams, schedules, crawl_texts, schedule_proposals
    core/            보안(JWT/해싱), 설정, rate limit, LLM(Agent) 연동
    models/          SQLAlchemy 모델
    schemas/         Pydantic 스키마
  alembic/           DB 마이그레이션
  tests/             pytest 통합 테스트
frontend/            Vite + React 앱
  src/
    pages/            로그인/회원가입/대시보드/계정 관리/Agent 검토
    components/        캘린더, 사이드바(TODO/학생/팀), 헤더 등
    auth/               인증 컨텍스트, 라우트 가드
    api/                백엔드 호출 래퍼
nginx/               프로덕션 리버스 프록시/정적 서빙 설정
docs/                PRD, 구현 계획, Phase별 진행 요약
docker-compose.yml         로컬 개발용
docker-compose.prod.yml    프로덕션(EC2)용
```

## 로컬 개발 환경

```bash
docker compose up -d
```

- 프론트엔드: http://localhost:5173 (Vite dev server, 파일 변경 즉시 반영)
- 백엔드: http://localhost:8000 (`--reload`)
- DB: PostgreSQL, `localhost:5432`

최초 실행 시 마이그레이션과 시드 데이터가 필요하면:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed
```

`backend/.env`는 git에 포함되지 않으므로 `backend/.env.example`을 참고해 로컬에 직접 생성한다.

### 테스트

```bash
cd backend
pytest                    # 백엔드 (136 passed, 3 skipped — rate limit 기본 비활성화로 인한 의도적 스킵)

cd frontend
npm run lint              # oxlint
npm run build             # tsc -b && vite build
```

## 배포

`docker-compose.prod.yml` 기준으로 db + backend(프로덕션 모드) + nginx(정적 build 서빙 + `/auth`,`/users`,`/teams`,`/schedules`,`/crawl-texts`,`/schedule-proposals`,`/health` 리버스 프록시)를 EC2 단일 인스턴스에 Docker Compose로 구동한다. HTTPS는 Let's Encrypt(certbot, webroot 방식)로 발급한다. `main` 브랜치에 push되어 CI(백엔드/프론트엔드/docker-compose 테스트)를 통과하면 GitHub Actions가 EC2에 SSH로 접속해 `git pull` → 재빌드 → 마이그레이션까지 자동으로 수행한다. 자세한 절차와 트러블슈팅은 `docs/Phase-6-Progress-Summary.md` 참고.

## 진행 현황

Phase 0(환경 셋업)부터 Phase 6(배포)까지 계획대로 완료했고, 배포 후 발견된 UX 개선(Phase 7)까지 반영되어 있다. 각 Phase의 설계 변경·트러블슈팅은 `docs/Phase-*-Progress-Summary.md`에 정리되어 있다.
