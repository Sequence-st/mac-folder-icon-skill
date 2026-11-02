# 폴더 아이콘 스킬 — 맥·윈도우 (Claude Code · Codex)

반려동물 사진이나 내 캐릭터 그림 한 장으로, 맥의 파란 폴더나 윈도우의 노란 폴더를 그 아이 얼굴 폴더로 바꿔 주는 스킬입니다.
맥과 윈도우 10·11에서 돼요. 맥에서는 바탕화면에 **새 폴더를 만들 때마다 자동으로** 그 아이콘이 입혀지게도 해 줘요.

| 스킬이 알아서 하는 것 | |
|---|---|
| 주문서 | 사진 속 그 아이만의 무늬·눈 색을 먼저 확인하고, 폴더 모양 그림 주문서를 써요 |
| 그림 뽑기 | 쓰고 있는 생성 도구를 찾아서 써요(코덱스 내장 · 클로드 코드에 연결된 이미지 서비스 · 구글 플로우) |
| 다듬기 | 끊긴 테두리 잇기 · 흰 배경 지우기 · 외곽선 비침 검사 · 폴더 크기에 맞추기 · 맥용 PNG와 윈도우용 .ico 같이 만들기 |
| 입히기 | 고른 폴더에 바로 입히고, 맥·윈도우가 실제로 보여 주는 아이콘을 되읽어 확인해요 |
| 덤 | 원래 폴더로 되돌리기 · 바탕화면 새 폴더 자동 변신(맥) |

## 설치

**클로드 코드나 코덱스에 이 문장을 그대로 붙여 넣으세요.**
```
https://github.com/Sequence-st/mac-folder-icon-skill 이 스킬 설치해줘
```

**zip으로 받기**: [mac-folder-icon.zip](https://github.com/Sequence-st/mac-folder-icon-skill/releases/latest/download/mac-folder-icon.zip)을 받은 뒤, 클로드나 코덱스에게 「다운로드 폴더에 받은 맥 폴더 아이콘 스킬 zip 설치해줘」라고 말하세요. 직접 하려면 압축을 풀고 맥은 터미널에서 `bash mac-folder-icon/install.sh`, 윈도우는 PowerShell에서 `powershell -ExecutionPolicy Bypass -File mac-folder-icon\install.ps1`.

### AI 에이전트가 설치할 때
이 저장소 주소를 받았다면 운영체제에 맞는 한 줄을 실행하세요.

맥(터미널) · 윈도우의 Git Bash
```bash
D="$(mktemp -d)" && git clone --depth 1 https://github.com/Sequence-st/mac-folder-icon-skill.git "$D/repo" && bash "$D/repo/skills/mac-folder-icon/install.sh"
```
윈도우(PowerShell)
```powershell
$D = Join-Path $env:TEMP ("mfi_" + [guid]::NewGuid()); git clone --depth 1 https://github.com/Sequence-st/mac-folder-icon-skill.git "$D\repo"; powershell -NoProfile -ExecutionPolicy Bypass -File "$D\repo\skills\mac-folder-icon\install.ps1"
```
- `install.sh`(윈도우는 `install.ps1`)는 스킬을 `~/.agents/skills/mac-folder-icon`(코덱스가 읽는 곳)에 복사하고, `~/.claude/skills/mac-folder-icon`(클로드 코드가 읽는 곳)에 연결한 뒤, 그림 도구(Pillow·numpy)를 확인합니다. 하나로 두 프로그램에서 다 써요.
- git이 없으면 위 zip 주소를 받아 풀고 같은 `install.sh`(윈도우는 `install.ps1`)를 실행하세요.
- 코덱스 내장 skill-installer로 깔아도 됩니다: `--repo Sequence-st/mac-folder-icon-skill --path skills/mac-folder-icon` (이 경우 `~/.codex/skills`에만 들어가서 클로드 코드에는 안 보여요).
- 끝나면 사용자에게 「새 대화에서 '우리 고양이 사진으로 폴더 아이콘 만들어줘'라고 말해 보세요」라고 안내하세요.

## 쓰는 법

그냥 말하면 됩니다.
```
우리 강아지 사진으로 폴더 아이콘 만들어줘   (사진을 끌어다 놓고)
내 캐릭터 그림으로 폴더 만들어서 '작업' 폴더에 입혀줘
바탕화면에 새 폴더 만들면 자동으로 이 아이콘 되게 해줘   (맥)
원래 폴더로 돌려줘
```
「눈을 더 크게」「무늬 위치가 반대야」처럼 보고 말로 고치면 돼요.

## 그림은 어디서 뽑나요
있는 걸 알아서 골라요. 뽑기 전에 비용을 먼저 알려 드려요(그 서비스 요금이에요).
1. 코덱스를 쓰면 코덱스가 직접 그려요.
2. 클로드 코드에 이미지 생성 서비스가 연결돼 있으면 그걸로 그려요.
3. 둘 다 없으면 구글 플로우를 브라우저로 대신 눌러서 그려요(구글 로그인 필요).
4. 그것도 어려우면 주문서 문장을 드려요. ChatGPT나 Gemini 앱에서 직접 뽑아 넣으면 나머지는 자동이에요.

## 알아 두면 좋은 것
- 만든 파일은 `사진(Pictures) > folder-icons > 이름` 폴더에 모여요.
- 처음 바탕화면 폴더를 바꿀 때 맥이 「접근 허용」 창을 띄울 수 있어요. 「허용」을 눌러 주세요.
- 맥 전체의 기본 폴더 모양은 바꿀 수 없어요(맥 보호 영역). 대신 자주 쓰는 폴더와 새 폴더에 입혀요.
- 윈도우는 파이썬 3이 필요해요(없으면 설치 방법을 알려 드려요). 폴더 안에 숨은 `folder-icon.ico`와 `desktop.ini`가 생기고, 되돌리면 원래대로 돌아가요. 문서·바탕화면 폴더의 원래 설정도 지켜요.
- 다른 사람의 캐릭터나 그림으로는 만들지 않아요. 내 반려동물, 내가 권리를 가진 캐릭터로 만들어요.

## 바뀐 점
- v0.3.1 (2026-11-02): 윈도우 탐색기에서 아이콘 테두리가 흐리게 끊겨 보이던 문제를 고쳤어요(윈도우용 큰 그림만 테두리를 살짝 두껍고 또렷하게).
- v0.3 (2026-11-02): 윈도우 10·11에서도 돼요. 같은 그림으로 윈도우용 .ico를 만들어 폴더에 입히고, 되돌리면 원래대로 돌아가요.
- v0.2 (2026-11-01): 연한 연필 선을 끊긴 선으로 잘못 보고 회색 띠를 덧그리던 문제를 고쳤어요. 파란 바탕화면에서 외곽선이 희끗하게 비치는지 검사하고, 비치면 그 그림의 선 색으로 메워요.
- v0.1 (2026-11-01): 첫 판.

## 이용 범위
- 이 스킬로 만든 아이콘 그림은 자유롭게 써도 돼요.
- 스킬 파일(문서·스크립트)을 다시 나눠 주거나 판매하는 건 안 돼요. 자세한 건 `LICENSE.txt`.

## 만든 곳
시퀀스스튜디오 · Instagram [@sequence_ai](https://instagram.com/sequence_ai)
