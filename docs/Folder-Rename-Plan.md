# 프로젝트 이름 통일 — katecam-todo-tracker → katecam-schedule-tracker

## 배경
아래 세 곳의 이름이 서로 달랐음:
- 로컬 폴더명: `katecam-todo-tracker`
- GitHub 원격 저장소명: `katecam-schedule-tracker`
- Docker Compose 컨테이너/볼륨명: `katecam-todo-tracker-*` (폴더명을 그대로 따라간 것)

`katecam-schedule-tracker`로 통일하기로 결정.

## 작업 순서

1. **`docker-compose.yml`에 `name: katecam-schedule-tracker` 명시**
   - 이후 폴더명이 무엇이든 컨테이너/볼륨명이 `katecam-schedule-tracker-*`로 고정됨
2. **기존 컨테이너/볼륨 정리 및 재생성**
   - `docker compose down`으로 기존 `katecam-todo-tracker-*` 컨테이너 제거
   - 새 이름으로 `docker compose up -d db` 재기동 → 새 볼륨 생성(기존 dev 시드 데이터는 사라짐, 재현 가능하므로 문제 없음)
   - Alembic 마이그레이션 재적용 + 시드 스크립트 재실행
3. **로컬 폴더명 변경**
   - `katecam-todo-tracker` → `katecam-schedule-tracker`
   - 주의: 현재 Claude Code 세션이 이 폴더를 작업 디렉토리로 물고 있으므로, 리네임 직후 이 세션의 파일 도구는 예전 경로를 참조하다 실패할 수 있음
   - 리네임 이후 에디터(VS Code 등)와 터미널을 새 경로로 다시 열어야 함
4. **GitHub 원격 저장소**
   - 이미 `katecam-schedule-tracker`로 되어 있어 변경 불필요

## 완료 후 확인 사항
- [ ] `docker compose config`에서 컨테이너명이 `katecam-schedule-tracker-db-1`로 뜨는지 확인
- [ ] 새 폴더 경로(`.../katecam-schedule-tracker`)에서 정상적으로 `git status`, `docker compose ps` 동작 확인
- [ ] `.venv`, `node_modules` 등 절대경로에 의존하는 로컬 설정(에디터 인터프리터 경로 등)이 있다면 새 경로로 재설정
