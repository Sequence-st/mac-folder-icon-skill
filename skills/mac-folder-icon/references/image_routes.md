# 이미지 생성 경로 고르기

순서: ① 코덱스 내장 → ② 연결된 이미지 MCP → ③ 구글 플로우(브라우저 자동화) → ④ 사용자가 직접.
먼저 `"$PY" <SKILL>/scripts/route.py get` 으로 저장된 선택이 있는지 본다. 있고 그 도구가 지금도 보이면 바로 그 경로로 간다.

모든 경로 공통
- 결과는 `~/Pictures/folder-icons/<이름>/raw_N.png` 로 저장한다.
- 레퍼는 사용자 사진/그림 **1장**. 주문서는 `prompt.txt` 전문 그대로.
- 기본 **1장 · 1K(약 1024px) · 1:1**. 사용자가 더 원할 때만 늘린다.
- 유료면 생성 전에 「이번 1장에 ○○ 크레딧(또는 약 $○)」을 알린다. 견적 도구가 없으면 「견적 도구가 없어서 뽑은 뒤 잔액으로 확인」이라고 말한다.

---

## ① 코덱스

코덱스(Codex CLI·앱)로 이 스킬을 쓰고 있으면 내장 이미지 생성 도구로 뽑는다. MCP 연결이 필요 없고 사용자의 ChatGPT 요금제 사용량으로 처리된다.
- 사용자 사진을 먼저 이미지로 열어(보기 도구) 생성기가 볼 수 있게 한 뒤, `prompt.txt` 전문으로 생성한다.
- 만든 그림은 보통 `~/.codex/generated_images/<세션>/` 아래에 PNG로 생긴다. 가장 최근 파일을 작업 폴더의 `raw_N.png` 로 복사한다.
- 내장 도구가 꺼져 있으면(`codex features list` 에서 `image_generation false`) 사용자에게 켜는 법을 알려 주거나 ④로 간다.

## ② 클로드 코드 + 이미지 MCP

지금 쓸 수 있는 도구 목록에서 아래 이름을 찾는다. 앞에 붙는 서버 이름(`mcp__<서버>__`)은 사용자마다 다를 수 있으니 **뒤쪽 도구 이름과 서버 이름 둘 다** 본다.

| 서비스 | 생성 도구 | 비용·잔액 확인 | 사진 올리기 | 메모 |
|---|---|---|---|---|
| 매그니픽(Magnific) | `images_generate` | `simulate_cost`, `account_balance` | `creations_upload_image` 또는 `creations_request_upload` | 모델 목록 `images_models_list`. 결과 기다리기 `creations_wait` |
| 힉스필드(Higgsfield) | `generate_image` | `balance`, `models_explore` | `media_upload` → 받은 주소로 파일 PUT → `media_confirm` | 결과 `jobs_wait` |
| 폴로(Pollo AI) | `generate_image` | `estimate_generation_cost`, `account_status` | `upload_image` | 상태 `get_generation_status` |
| 빠나나(BBANANA) | `generate_image` | `check_credits` | `create_upload_url` + `confirm_upload` (작은 파일은 `upload_image`) | 모델 `list_models`, 상태 `get_status` |
| 오픈아트(OpenArt) | `openart_generate_image` | `openart_model_cost` | `openart_upload_sign`(터미널) / `openart_upload_pick`(창) | 모델 `openart_model_list` |
| 클링(Kling) | `image_to_image`(사진 있음) / `text_to_image` | `query_membership_and_credits` | `file_upload` | 먼저 `who_am_i` |
| AICRON | `generate_image` | `get_credits` | `prepare_image_upload` → 사용자가 창에서 올림 → `get_upload_result` | 모델은 `select_model`로 고르게 함 |
| 그 밖 | 이름에 `generate_image`·`text_to_image`·`image_generate`·`create_image`가 들어간 도구 | 이름에 `cost`·`credit`·`balance`·`quote` | 이름에 `upload` | 스키마를 읽고 쓴다 |

고르는 법
- 하나만 보이면 그걸 쓴다. 여러 개면 **한 번만** 물어본다(「매그니픽·폴로가 연결돼 있어요. 어느 쪽으로 뽑을까요?」).
  고른 뒤 `route.py set mcp --tool <생성 도구 전체 이름> --model <모델>` 으로 저장한다.
- 모델은 그 서비스 목록에서 **레퍼를 잘 따르고 평면 일러스트가 깨끗한 이미지 모델**(예: 나노바나나 계열, GPT 이미지 계열)을 고른다. 목록에 없는 이름을 지어내지 않는다.
- 해상도는 그 도구가 받는 값 중 1K(1024 안팎)에 가장 가까운 것, 비율 1:1, 장수 1.
- 결과 주소를 받으면 `curl -L -o raw_N.png "<주소>"`로 받는다(주소·서명은 사용자에게 보여 주지 않는다).

## ③ 구글 플로우 (브라우저 자동화)

①·②가 없을 때. 에이사이드 같은 특정 브라우저가 꼭 있어야 하는 건 아니고, **브라우저를 대신 눌러 줄 도구**만 있으면 된다.
- 클로드 코드: 공식 크롬 확장 「Claude in Chrome」(사용자 크롬에 로그인된 그대로) 또는 플레이라이트 MCP(처음 한 번 구글 로그인).
- 코덱스: 내장 브라우저 사용 도구.

순서
1. 플로우를 연다(`flow.google.com`, 안 열리면 `labs.google/flow`). 구글 로그인이 안 돼 있으면 **사용자가 직접 로그인**하게 하고 기다린다(비밀번호를 대신 넣지 않는다).
2. 새 프로젝트 → 이미지 만들기. 모델은 나노바나나 계열. 「에이전트」 같은 자동 모드 토글이 있으면 끈다.
3. 레퍼 사진 1장 추가 → `prompt.txt` 전문 붙여넣기 → 비율 1:1 → 1장 생성.
4. 결과를 원본 크기로 내려받아 `raw_N.png` 로 저장한다.

주의
- 플로우 화면은 자주 바뀐다. 버튼을 못 찾으면 화면을 캡처해 보고 판단하고, 두 번 막히면 ④로 넘어간다.
- 결과 오른쪽 아래 구석에 별 모양 표시가 찍힌다. 배경 위에 따로 떨어진 표시라 `make_icon.py`의 「가장 큰 덩어리만 남기기」에서 지워진다. 확인판에서 지워졌는지 본다.
- 구글 계정 사용량 한도가 있을 수 있다(초과 시 플로우가 안내).

## ④ 사용자가 직접

1. `prompt.txt` 내용과 레퍼 사진을 보여 준다.
2. 「ChatGPT·Gemini 앱 등 쓰는 곳에 사진을 올리고 이 문장을 붙여 넣어 1장 뽑아 주세요. 정사각형으로요.」
3. 받은 그림을 `~/Pictures/folder-icons/<이름>/` 에 넣어 달라고 하고, 들어오면 4단계(다듬기)부터 자동으로 이어 간다.
   - 앱 워터마크가 구석에 있어도 대개 다듬기에서 지워진다.
