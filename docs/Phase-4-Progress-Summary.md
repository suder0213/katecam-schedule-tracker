# Phase 4 구현 요약

`docs/Implementation-Plan.md` 기준 Phase 4(Agent 기반 일정 추가 계획) 진행 내용과 과정에서 있었던 설계 변경, 트러블슈팅을 정리한다. Phase 0~3은 `docs/Phase-0-2-Progress-Summary.md`, `docs/Phase-3-Progress-Summary.md` 참고.

## 구현 항목

| 항목 | 내용 |
|---|---|
| 4-1 텍스트 입력 | `POST /crawl-texts`(dev 전용) — source(notion/discord)+channel 저장, CHECK 제약으로 조합 강제 |
| 4-2 Agent 분석 | `POST /crawl-texts/{id}/analyze` — LLM 구조화 출력 → `ScheduleProposal`(제안 카드) 생성, 실패 시 3회 재시도 |
| 4-3 조회/Approve | `GET /crawl-texts/{id}`, `GET /schedule-proposals?raw_text_id=`, `POST /schedule-proposals/{id}/{approve,reject}` |
| 4-4 백업 | create-only라 "이전 상태"가 없어 실제 구현 불필요(설계로 이미 충족) |
| 4-5 반영 로직 | approve 엔드포인트에 포함 — 승인 시 실제 `Schedule(kind=shared)` 생성 |
| 4-6 자동 크롤링/스케줄러 | 설계만, 구현은 MVP 이후로 유지 (계획서 그대로) |

## 원 계획 대비 변경된 결정사항

### LLM 프로바이더를 Claude API → 카카오 발급 OpenAI 호환 프록시로 전환

원래 계획은 Anthropic Claude API를 직접 호출하는 거였는데, 카카오테크캠프에서 발급한 OpenAI 호환 프록시(`base_url` + `api_key`만 바꾸는 방식)를 쓰기로 결정. `anthropic` 패키지(코드에서 실제로 쓰이진 않던 상태) 제거, `langchain-openai` 추가. `app/core/llm.py::chat_model()` 헬퍼로 프록시 연결 — 실제 프록시로 일반 채팅 + structured output(Tool calling 기반 Pydantic 강제) 둘 다 스모크 테스트 완료.

### Agent 제안 카드 승인을 "계획(Plan) 전체 단위" → "카드(개별 제안) 단위"로 변경

`docs/Frontend-Feature-Spec.md`를 채우는 과정에서 "하나의 텍스트에서 나온 카드들을 한 박스로 묶어 보여주되, 카드 단위로 부분 승인 가능해야 한다"는 요구사항이 확정됨. 이에 따라 원래 계획했던 `Schedule_Plan`(plan 전체가 pending/approved/rejected 상태를 가짐) 테이블 설계를 버리고, **`ScheduleProposal` 개별 row가 각자 상태를 가지는** 구조로 변경. 백업도 카드 단위로 개별 생성하기로 함(사용자 200명 안팎 규모라 파일 개수 부담 적음).

### 이번 단계는 create만 지원 — update(기존 일정 참조)는 이후로 미룸

Agent가 "update" 제안을 하려면 어떤 기존 일정을 가리키는지 알아야 하는데, LLM은 우리 DB의 schedule_id를 전혀 모름 — 현재 공유 일정 목록을 컨텍스트로 주고 제목 매칭 후 백엔드에서 UUID로 역변환하는 방식이 필요해서 복잡도가 높아짐. 이번 Phase 4에서는 **create만 지원**하기로 단순화(`ScheduleProposal`에 `action`/`target_schedule_id` 필드 자체를 두지 않음). update는 나중에 별도로 설계.

### Agent 제안 카드의 근거 표시 방식 — 카드별 스니펫 대신 원문 텍스트 링크

원래 계획은 "각 항목에 title/contents/deadline/근거 스니펫"이었는데, "하나의 텍스트에서 파생된 계획들이니 스니펫을 각각 만드는 것보다 원문 텍스트나 원문으로 이동하는 링크를 걸어두는 게 더 경제적"이라는 판단으로 변경. `ScheduleProposal.raw_text_id`로 원문(`CrawlText`)을 참조하고, `GET /crawl-texts/{id}`로 원문을 따로 조회하는 구조로 충분.

### Agent의 delete 제안 범위 제외

PRD 원문(`Trimmed-PRD.md`, 레거시로 취급하기로 함)에는 Agent가 Update/Delete까지 제안하되 사람 승인을 거치는 걸로 돼 있었지만, 이번 구현에서는 **delete는 사람이 직접 수행**하는 것으로 확정 — Agent는 create만 제안.

## `args_schema` 관련 확인 (구현 변경 없음)

"Agent tool call의 args_schema로 이중 검증이 가능하지 않냐"는 질문이 나와서 확인. 결론: `with_structured_output(PydanticModel)`도 내부적으로 Pydantic → JSON Schema 변환을 거쳐 LLM에 도구 스펙으로 전달하기 때문에, `Field(description=...)`가 `args_schema` 방식과 **완전히 동일하게** 작동함(실제로 `ProposedScheduleItem`의 JSON Schema를 덤프해서 description이 정상적으로 들어가 있음을 확인). `args_schema`(LangChain `@tool`)는 모델이 여러 도구 중 하나를 스스로 선택하는 ReAct형 에이전트에 쓰는 패턴이라, 지금처럼 단일 스키마 추출 작업에는 오히려 과한 구조. 진짜 차이점(의미적 validator — 빈 title, 과거 deadline 등 거르기)은 MVP 범위상 이번엔 보류하기로 함.

## 트러블슈팅

- **테스트 DB 정리 목록 누락.** `tests/conftest.py`의 `TABLES_IN_FK_ORDER`에 `crawl_texts`/`schedule_proposals`가 빠져있어서, 전체 스위트로 돌릴 때만 테스트 간 데이터가 누적되는 문제 발생(개별 실행 시엔 통과해서 처음엔 원인 파악에 혼선). FK 순서 맞춰서 추가해 해결.
- **테스트 코드가 `GET /schedules`의 `student_id` 필수 조건을 놓침.** Approve/Reject 테스트에서 생성된 Schedule을 확인하려고 dev 계정으로 `GET /schedules?year=&month=`를 호출했는데, dev/manager는 `student_id` 없이 호출하면 400이 나는 Phase 3 규칙을 깜빡함. 캘린더 API를 거치지 않고 `db_session`으로 직접 `Schedule` row를 조회하는 방식으로 테스트를 고침.
- **Windows 콘솔 한글 인코딩으로 인한 curl 테스트 혼선.** 한글이 포함된 JSON을 curl `-d` 인자로 직접 넘기면 Git Bash에서 인코딩이 깨져 "There was an error parsing the body" 에러가 남(실제 API 버그 아님). UTF-8 파일로 payload를 작성해 `--data-binary @file`로 넘기는 방식으로 전환해 해결.
- **Agent 자동화 테스트는 실제 프록시를 호출하지 않음.** `chat_model()`을 monkeypatch로 교체해서 비용/네트워크 의존성 없이 성공/재시도-실패 케이스를 검증. 실제 프록시 연동 자체는 수동으로 한 번 end-to-end 확인(진짜 공지 텍스트로 마감일 2건 정확히 추출, 상대 날짜 계산도 정확, 무관한 내용은 필터링됨).

## 테스트 현황

- `test_crawl_texts.py`(7), `test_crawl_texts_analyze.py`(5), `test_schedule_proposals.py`(13) 신규 추가
- 기존 테스트와 합쳐 총 **113개 테스트 통과**, CI 환경(프록시 시크릿 없음)에서도 통과 확인

## 현재 상태

Phase 0~4 전부 구현 및 검증 완료(4-4/4-6은 설계로 충족/의도적 보류). 다음은 Phase 5(프론트엔드) — 인증 화면(5-1) 구현 및 실브라우저 검증까지 완료된 상태에서 이 문서를 작성함.
