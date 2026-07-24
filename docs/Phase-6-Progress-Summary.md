# Phase 6 구현 요약

`docs/Implementation-Plan.md` 기준 Phase 6(배포) 진행 내용과 과정에서 있었던 설계 변경, 트러블슈팅을 정리한다. Phase 0~5는 `docs/Phase-0-2-Progress-Summary.md`, `docs/Phase-3-Progress-Summary.md`, `docs/Phase-4-Progress-Summary.md`, `docs/Phase-5-Progress-Summary.md` 참고.

## 구현 항목

| 항목 | 내용 |
|---|---|
| 6-1 EC2 인스턴스 준비 | 신규 EC2(us-east-1, Amazon Linux 2023, t3.small, gp3 20GB) 생성. 예전에 쓰던 탄력적 IP(`54.80.230.167`)와 DNS(`suderhome.com`)는 그대로 재사용 — EIP를 새 인스턴스에 재연결만 함. 보안그룹은 22(SSH, 내 IP)/80/443만 오픈, 8000/5173은 외부 미노출(nginx만 진입점) |
| 6-2 프로덕션 Docker Compose | `docker-compose.prod.yml` 신규 작성 — db(로컬과 동일) + backend(`--reload` 제거, bind mount 제거) + nginx. 로컬 `docker-compose.yml`(dev)은 그대로 두고 손대지 않음 |
| nginx 리버스 프록시 + 정적 서빙 | `nginx/Dockerfile`(멀티스테이지: frontend `npm run build` → nginx 이미지에 정적 파일 포함), `nginx/nginx.conf`(80은 443으로 리다이렉트, 443이 `/auth` 등 API 경로는 backend로 프록시하고 나머지는 SPA 정적 서빙), `nginx/snippets/proxy.conf`(공통 프록시 헤더) |
| 6-3 환경변수/시크릿 | `backend/.env`는 EC2에만 생성(git 미포함 재확인). 로컬 `.env`와 달리 `DATABASE_URL`을 `db:5432`(컨테이너 서비스명)로, `JWT_SECRET`을 `openssl rand -hex 32`로 새로 발급한 값으로 교체 |
| 6-4 HTTPS | Let's Encrypt(certbot) + webroot 방식으로 `suderhome.com` 인증서 발급, 이후 본 스택 기동 |
| 6-5 CI/CD (계획 외 추가) | `.github/workflows/ci.yml`에 `deploy` job 추가 — `main` push 후 기존 backend/frontend/docker-compose CI가 전부 통과해야 실행(`needs`), `appleboy/ssh-action`으로 EC2에 SSH 접속해 `git pull` + `docker compose -f docker-compose.prod.yml up -d --build` + `alembic upgrade head` 자동 실행. EC2 접속 정보(`EC2_HOST`/`EC2_USER`/`EC2_SSH_KEY`)는 GitHub repo secret으로 등록 |

## 원 계획 대비 변경된 결정사항

### 프론트엔드를 프로덕션에서 정적 build + nginx로 서빙 (dev의 vite 서버 그대로 쓰지 않음)

원 계획(`Implementation-Plan.md` 6-2)은 "로컬 docker-compose.yml과 동일 구조 유지"를 전제했으나, HTTPS 터미네이션에 nginx(또는 Caddy)가 필수인 이상 그 nginx가 정적 파일까지 같이 서빙하는 편이 더 단순하고 안전하다고 판단해 vite dev 서버 컨테이너를 프로덕션에서 제외. `nginx/Dockerfile`이 멀티스테이지로 `npm run build` 결과물을 직접 이미지에 포함시키는 구조로 대체.

### 인증서 최초 발급의 chicken-and-egg 문제를 2단계 절차로 해결

`nginx.conf`(최종본, git에 커밋)는 이미 `/etc/letsencrypt/live/suderhome.com/...` 인증서 경로를 참조하므로, 인증서가 없는 상태에서 이 설정으로 nginx를 띄우면 컨테이너가 뜨지도 못해 certbot의 webroot 검증조차 할 수 없는 문제가 있었음. `nginx/bootstrap.conf`(HTTP만 응답하는 임시 설정, 이미지에는 포함 안 됨)로 별도의 임시 `nginx:alpine` 컨테이너를 잠깐 띄워 인증서를 먼저 발급받고, 그 컨테이너를 내린 뒤 본 스택(`docker-compose.prod.yml`)을 기동하는 순서로 해결.

## 트러블슈팅

- **EC2 재사용 시 SSH host key 경고.** 예전에 지운 인스턴스가 쓰던 탄력적 IP를 새 인스턴스에 재연결하니 SSH가 "REMOTE HOST IDENTIFICATION HAS CHANGED" 경고를 띄움. 실제 MITM이 아니라 같은 IP에 물리적으로 다른 서버가 붙으며 host key가 바뀐 것뿐 — `ssh-keygen -R <IP>`로 기존 known_hosts 항목 제거 후 재접속.
- **Amazon Linux 2023 기본 이미지에 git, 최신 Docker Compose/Buildx 플러그인이 없음.** `dnf`로 `docker`는 설치되지만 Compose/Buildx 플러그인은 리포에 없거나(`docker compose version` 실패) 너무 오래된 버전이 들어있어(`compose build requires buildx 0.17.0 or later`) GitHub 릴리즈에서 최신 바이너리를 `~/.docker/cli-plugins` 또는 `/usr/local/lib/docker/cli-plugins`에 직접 받아 설치. git도 `sudo dnf install -y git`로 별도 설치 필요.
- **PR CI에서 Black 포맷 검사 실패.** `backend/tests/test_users.py`의 한 줄이 직전 커밋에서 Black을 거치지 않고 들어가 라인 길이 규칙을 어김. `python -m black tests/test_users.py`로 재포맷 후 별도 커밋.
- **로컬 백엔드 테스트가 전부 실패로 돌아섬(포맷 수정 후 재검증 중 발견).** venv에 `bcrypt`가 `requirements.txt`에 고정된 `4.0.1`이 아니라 `5.0.0`으로 드리프트되어 있어 passlib과 호환이 깨짐(`module 'bcrypt' has no attribute '__about__'`). `pip install -r requirements.txt`로 고정 버전 재설치해 해결. 이 과정에서 무관한 `langchain-core`가 상위 버전으로 같이 올라가며 이 venv에 함께 들어있던(요구사항 파일엔 없는) 다른 패키지들(`langchain`, `langchain-google-genai` 등)과 충돌 경고가 떴으나, 백엔드 자체 테스트(130 passed, 3 skipped)엔 영향 없음을 확인.
- **배포 직후 회원가입/로그인 실패, 웹사이트 접속은 정상.** 새 Postgres 컨테이너에 Alembic 마이그레이션을 자동 실행하는 설정이 없어(dev/prod 모두 수동 실행 전제) 테이블이 비어있던 상태. `docker compose -f docker-compose.prod.yml exec backend alembic upgrade head`로 해결.
- **개발자 계정 격상이 API로 안 됨.** `PATCH /users/{id}/permission`은 `CHANGEABLE_PERMISSIONS`(student/manager)만 허용하고 dev로의 승격은 라우트에서 명시적으로 403 처리(`backend/app/api/routes/users.py`) — 의도된 제약. DB에 직접 `UPDATE users SET permission=... WHERE email=...`로 처리. `user_permission` enum이 실제 DB에 저장된 값의 대소문자를 모델 정의(`dev`/`manager`/`student`, 소문자)와 다르게 인식해 첫 시도가 `invalid input value for enum` 에러로 실패 — `SELECT enum_range(NULL::user_permission)`로 실제 값 확인 후 정정.

## 테스트 현황

- 백엔드: **136 passed, 3 skipped**(rate limiting 기본 비활성화로 인한 의도적 스킵), 실패 0
- 실브라우저로 `https://suderhome.com`에서 회원가입~로그인~계정, 팀 생성/가입/탈퇴/삭제 정상 동작 확인
- CI/CD: PR #4 병합으로 `deploy` job까지 포함한 전체 파이프라인을 실제로 1회 통과시켜 검증(배포 후 `https://suderhome.com` 200 응답 확인)

## 현재 상태

Phase 6(6-1~6-5) 배포 및 CI/CD 구축 완료. `https://suderhome.com`에서 실서비스 운영 중 — HTTPS 적용, 기존 탄력적 IP/DNS 재사용, db 포함 전체 스택이 단일 EC2 위 Docker Compose로 구동되며, `main` push 시 GitHub Actions가 자동으로 재배포함.
