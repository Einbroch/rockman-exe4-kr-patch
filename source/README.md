# 작업 소스 (도구 · 번역)

록맨 에그제 4 한글 패치를 만드는 데 쓴 빌드·검증 도구와 한국어 번역 파일입니다.
**ROM 은 들어 있지 않습니다.** 빌드하려면 본인이 가진 원본 일본판 ROM(블루문 / 레드선 Rev 1)이 필요합니다.

## 구성

| 폴더 | 내용 |
|---|---|
| `tools/` | 빌드·검증 스크립트(Python)와 `tools/specs/` 의 주소·형식 명세 |
| `translations/` | 한국어 번역 파일. `story_korean/` 대사 배치, `menu_korean.json` 메뉴·라벨, `chip_*` 칩 이름·설명 등 |
| `docs/` | 작업 기록(`HANDOFF.md`, `WORK_LOG.md`)과 작업 폴더 설명서(`WORK_README.md`) |

`translations/story_source.jsonl` 은 대사 번역 대조용으로 원문 일본어 줄을 담고 있습니다.

## 빌드에 필요한 것(포함되지 않음)

- 원본 일본판 ROM 두 개(해시는 저장소 첫 화면 README 의 표 참고)
- [TextPet](https://github.com/Prof9/TextPet) 1.0.0 과 EXE4 플러그인
- 한글 글꼴 [Galmuri](https://github.com/quiple/galmuri) (Galmuri7 / 9 / 11, OFL 1.1)
- 메뉴 글자용 록맨 에그제 1 한국어판 ROM(글리프 추출용)
- 화면 확인용 Mesen 2

경로는 작업 PC 기준으로 적혀 있어 그대로는 돌지 않습니다(`C:\Users\<사용자>\...` 등은 자리표시).
