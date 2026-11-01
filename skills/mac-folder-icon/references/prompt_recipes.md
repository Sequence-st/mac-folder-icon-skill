# 주문서 레시피 (영어 본문)

`{ }` 칸만 채운다. 블록 F·D·W는 통과한 문장이니 되도록 그대로 둔다.
그림 한 장 = 레퍼 1장 + 아래 주문서 1개. 결과가 이상하면 장수를 늘리기 전에 맨 아래 「자주 생기는 문제」부터 본다.

---

## 공통 블록

**F1 — 폴더 모양 (내 캐릭터용)**
```
The icon: a classic rounded desktop folder seen straight from the front, about 1.25 times wider than tall. The folder itself is {NAME}. The back panel is {BACK_COLOR}, with a small rounded tab on its upper left, and its top edge is one straight line. The front pocket panel is {FRONT_COLOR} with gently rounded corners, and {NAME}'s two {EAR_DESCRIPTION} grow straight up from its top corners as one smooth continuous shape with the panel, with the outline running around panel and ears in one line, so the ears stand in front of the back panel. The front panel is a wide rounded rectangle like a real folder pocket, with straight left and right sides, a straight bottom edge and a straight top edge; only the two ears rise above that top edge. The front panel carries the whole face: {FACE_LAYOUT}. Every part shares the same outline.
```
- 귀가 없는 캐릭터면 귀 문장을 빼고 「only the top accessory rises above that top edge」처럼 바꾼다.
- 모자·리본 같은 소품: `The small {ACCESSORY} sits on the front panel's top edge, a little left of center, in front of the back panel.`

**F2 — 폴더 모양 (반려동물용)**
```
The icon: a classic rounded desktop folder seen straight from the front, about 1.25 times wider than tall. The folder itself is {NAME}'s face. The folder is {BASE_COLOR}; {NAME}'s {FUR_CAP_COLOR} cap of fur covers the top of the front panel with a soft wavy lower edge{CAP_MARK}; the two ears rise from the top corners of the front panel; the small face sits in the middle of the {LOWER_FACE_COLOR} front panel. The back panel has a small rounded tab on its upper left, and its top edge is one straight line.
```

**D — 앞판 그림자 (입체감)**
```
Depth: the front panel casts one soft drop shadow onto the back panel. Right above the front panel's top edge and behind the ears, the back panel turns gradually a little darker, about 6 percent darker, in a soft band about 8 percent of the folder's height, deepest right at the front panel's edge and fading smoothly upward, so the front panel clearly sits in front of the back panel. This band is the only soft shading added to the picture; every other area keeps clean flat color with crisp edges.
```

**W — 흰 배경·크기 (스크립트가 이걸 전제로 배경을 지움)**
```
Square 1:1 image. The folder sits centered and fills about 80 percent of the width, isolated on a pure flat white #FFFFFF background with plain white all around and crisp clean edges, like an app icon sticker. Crisp clean flat illustration made only of shapes and colors.
```
⚠️ 「transparent background」라고 쓰지 않는다. 체크무늬를 그려 넣는 모델이 있다.

---

## A. 내 캐릭터 (그림 파일 있음)

```
Create one cute desktop folder icon of {NAME}, {ONE_LINE_WHO}, drawn in the same style as the attached image.

Draw {NAME}'s face exactly as in the attached image: {FEATURE_LIST}.

{F1}

{D}

{W}
```
- `{FEATURE_LIST}` = 눈(모양·색·하이라이트 위치), 코, 입, 볼, 이마 무늬, 귀 안쪽 색, 소품, 테두리 색과 굵기, 털/피부 색. **색은 HEX로**(그림에서 스포이트로 재서), 「the same …」로 시작하는 짧은 구를 쉼표로 잇는다.
  예: `the same two glossy black oval eyes with a small white highlight at the upper left, the same coral-pink oval blush cheeks (#F8897E), the same thick warm-brown outline (#8C4414)`
- 캐릭터는 폴더보다 「머리 모양」 쪽으로 새는 경향이 있다. 예산이 되면 2~3장 중에서 고르는 게 낫다(장마다 비용 고지).

## B. 반려동물 (사진 있음)

```
Turn {NAME}, the {cat/dog/rabbit...} in the attached photo, into one cute desktop folder icon in a very simple, soft, pastel mascot doodle style.

Style: a round, squishy, mochi-like {animal} face drawn with very few lines. A thin, soft, slightly uneven {OUTLINE_COLOR} outline like a soft pencil. Small, simple facial features sitting close together in the middle of the face: {EYES}; a tiny {NOSE_COLOR} nose; a tiny "w" mouth; a small pale pink oval blush with three tiny diagonal lines on each cheek. Flat pale pastel colors, lots of soft white, and smooth flat fills with no fur texture and no shading.

{NAME}'s marks, each drawn as a tiny simple shape: {MARK_1}; {MARK_2}; {MARK_3}; {MARK_4}; the rest of the {lower face} {color}. Ears: {EAR_SHAPE}, {EAR_COLOR} with pale pink inside.

Face size, kept large and clear: each eye is an upright oval about 10 percent of the folder's width tall and 5 percent wide; the two eyes sit about 30 percent of the folder's width apart, center to center, at about 60 percent of the folder's height; the nose is about 9 percent of the folder's width wide.

{F2}

{D}

{W}
```
- `{EYES}` 는 **실제 눈 색**으로: `two small upright oval eyes, golden yellow with a dark round pupil and one round white shine at the top`. 「black bean eyes」처럼 쓰면 눈 색이 사라진다.
- 무늬(`{MARK_n}`)는 **4~5개만, 아주 작은 모양으로**: 
  - 치즈 태비 고양이: `three short orange stripes on the forehead`, `two thin orange stripes on each cheek`, `a white chin`
  - 강아지: `a thin white stripe from the forehead down to the nose`, `one brown ear on the viewer's left and one cream ear on the viewer's right`
  - 토끼: `a small gray patch around the eye on the viewer's left`, `a white tip on each ear`
- 좌우는 항상 **보는 사람 기준**(`on the viewer's left`)으로 쓴다.

## C. 말로만 (그림·사진 없음)

```
Create one cute desktop folder icon of {NAME}, an original character: {WHO_AND_LOOKS in 2-3 sentences, colors as HEX}.

Style: {simple flat sticker style with thick soft outline | soft pastel doodle with thin pencil outline}.

{F1}

{D}

{W}
```

---

## 자주 생기는 문제 → 주문서에서 고칠 곳

| 결과 | 원인 | 고치는 문장 |
|---|---|---|
| 그림이 사진처럼 사실적인 만화가 됨 | 무늬를 많이·자세히 썼거나 사진을 여러 장 붙임 | 그림체 문단을 앞에, 무늬는 4~5개 「tiny simple shape」로, 사진 1장 |
| 눈 색이 검정으로 바뀜 | 「black bean eyes」 같은 그림체 말 | 눈을 실제 색으로(위 `{EYES}` 예시) |
| 무늬가 좌우 반대 | 「left side of the face」는 누구 기준인지 모호 | `on the viewer's left`. 그래도 반대면 다시 뽑기 전에 사용자에게 알리고 고름 |
| 무늬가 넓게 번짐(예: 코 주변 무늬가 이마까지 올라감) | 「from between the eyes」처럼 시작점만 씀 | 시작과 끝을 같이: `starting below eye level, only around the nose` |
| 다시 뽑으니 얼굴이 쪼그라듦 | 크기 말이 없음 | 「Face size」 문단 숫자(눈 10%·5%, 간격 30%, 높이 60%, 코 9%)를 넣거나, 마음에 든 판에서 재서 바꿈 |
| 앞판이 통째로 머리 모양 | 「shaped like {NAME}'s head」 같은 말 | 「straight left and right sides, a straight bottom edge and a straight top edge; only the ears rise above」 |
| 뒤판 윗선이 울퉁불퉁 | 윗선 지시 없음 | `its top edge is one straight line` |
| 앞판·뒤판 경계가 납작 | 그림자 지시 없음 | 블록 D |
| 그림자가 귀 주변·얼굴에 뿌옇게 | 「soft shading」이 여러 군데 | D의 마지막 문장(「the only soft shading」) 그대로 |
| 털 위에 흰 선이 광택처럼 생김 | 흰 무늬를 가는 선으로 씀 | 그 문장을 빼거나 「a small white patch」처럼 면으로 |
| 폴더 옆면 테두리가 끊김 | 생성 그림의 선이 흐려짐 | `make_icon.py`가 10~250px 끊김은 자동 수리. 아주 길게 끊겼으면 다시 뽑는 게 깔끔 |
| 바탕이 흰색이 아님·그림이 꽉 참 | W 블록 빠짐 | 블록 W 그대로 |

## 여러 개를 한 세트로 만들 때 (꼭 지킬 것)

- 세트가 같이 나눠 갖는 건 **그림체뿐**이다(선 굵기·색감·볼 표현·면 칠하는 방식).
- 생김새·색·무늬는 각자 원래대로 둔다. 캐릭터는 원본 그대로, 동물은 「clearly looks like a real ○○」.
- 모두를 같은 틀(예: 하얀 얼굴 + 위쪽에 색깔 털 모자)에 끼워 넣지 않는다. 그러면 다 같은 머리가 되고, 캐릭터는 그 캐릭터답지 않게 된다.
- 앞판은 「그 아이 얼굴 전체가 원래 털색」으로 쓴다: `The front pocket panel is the ○○'s whole face in its own natural fur colors.`
- 캐릭터 그림체만 바꿀 때는 「Keep ○○ exactly the same character, with the same colors, the same marks and the same face, and change only the drawing style.」 다음에 지킬 특징을 하나씩 적는다.
