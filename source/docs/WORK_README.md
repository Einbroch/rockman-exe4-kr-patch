# 록맨 에그제 4 한글패치

레드 선 일본판 Rev 1과 블루 문 일본판의 전체 한글화를 목표로 한다.
현재는 오프닝·일부 메뉴·초기 폴더 칩10종과 도감·전투 칩 선택창·사용 대기 칩 이름을 한글로 표시하는
개발 단계다. 도감과 전투 선택창은294개 이름 초안을 지원하며, 실제 게임 화면에서 확인한
이름은 각각3종과4종이다. 전체 대사 번역, 다른 전투 표시와 설명, NAME 입력·저장·통신은 남아 있다.
완성판 또는 배포용 패치가 아니다.

최신 개발본은 `poc/output/*_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba`다.
2026-09-19 전투 선택창 설명10종 삽입과 재현 방법은 이 문서 마지막 절에 기록했다.

에그제 2에서 겪은 My Boy 메뉴 정지, raw 아카이브 후속 대사 누락,
heredoc 줄바꿈 손실을 조사 항목으로 반영했다. 일반 대사만 성공해도 메뉴까지
완성됐다고 판단하지 않으며, 에그제 2의 오프셋이나 CPU 훅을 그대로 이식하지 않는다.

## 입력과 경계

| 버전 | 코드/리비전 | 크기 | SHA-256 |
|---|---|---:|---|
| 블루 문 | B4BJ / 0 | 8,388,608 | f976a84ef226e47d4a65695052da09b415867b01586dd74bbb1c289a6f607b63 |
| 레드 선 | B4WJ / 1 | 8,388,608 | 1904692bc383fc2cb7e1d81e1c80bf2d8c616c0d1b1d396c689f71b49a2e3188 |

원본은 타이틀 폴더에서 읽기 전용으로 소비한다. 모든 작업물은 이 `_work/exe4-kr`에 둔다.
ROM, 추출 원문/그래픽/메모리, 외부 도구는 저장소 추적 및 배포 대상이 아니다.
game-translate 1.6.2에는 GBA 어댑터가 없으므로 그 파이프라인의 완료 상태를 사용하지 않는다.
create-kr-patch 스킬의 입력 식별, 무변경 왕복, Expected Write, 개발/배포 정책을 적용한다.

## 확인한 구조

- 각 버전의 TextPet 인덱스에 793개 아카이브가 있다. 압축 716개, raw 77개다.
- 직접 포인터 763개, 상위 `0x80000000` 비트를 가진 압축 포인터 324개를 실제 원본과 대조했다.
  5개 행은 포인터 주장 없이 남아 있으므로 재배치할 수 있다고 판단하지 않는다.
- 원문 TPL → MSG 변환은 양쪽 모두 793/793 해제 페이로드 바이트 동일이다.
- 첫 왕복에서는 각 버전 13개 아카이브가 실패했다. `F9 00 xx x4`의
  `printFolderName.entry` 정의를 4비트에서 8비트로 수정해 손실된 `0x10/0x20`을 보존했다.
  원본 플러그인은 `external/textpet-plugins-pristine/mmbn4.ini.orig`에 보존한다.
- 781개 페이로드가 버전 간 동일하고 12개가 다르다. 전역 오프셋 델타를 가정하지 않는다.
- 인쇄된 스크립트는 각 14,546개, 그중 문자열을 가진 것은 13,984개다.
  슬롯/별칭/빈 엔트리는 별도의 테이블에 보존하며 이 수치를 최종 번역 작업량으로 쓰지 않는다.
- 일반 대사 출력기는 IWRAM에 실행된다. `0x03006A48` 부근에서 glyph index × `0x60`,
  한 행 두 워드, 12행을 소비한다. 가변 폭은 별도 32비트 LE 테이블에서 읽는다.
- 일반 폰트는 블루 문 `0x695004`, 레드 선 `0x695224`다. 폭 테이블은 각각
  `0x51588`, `0x515B8`이다. 일반 폰트의 441개 원본 레코드와 폭 표의 유일한 일치로 대조했다.
  문자표의 마지막 `E4D5`가 442번째 일반 글리프라고 가정하지 않는다. 그 주소는 팔레트다.
- 별도 8×16 타일 출력기 `0x0300677C/0x030067F0`가 있다. 폴더/저장은 블루 문
  `0x68E004`, PET 상태창은 `0x6C699C`를 읽는다. 레드 선은 각각 `0x68E224/0x6C6E60`이다.
  두 원본 글꼴은 픽셀과 배경/잉크/그림자 색 인덱스가 다르다.
- 원문은 single `00..E3`, lead `E4`로 인덱스를 선택한다. 제어 영역은 `E5`부터 시작한다.
  일반 대사에는 새 `F9 FC + uint16 LE` 한글 코드를 추가했다.
  코드 뱅크 적재와 모든 디코더를 전수 확인한 것은 아니다.
- 관측한 일반 출력기는 IWRAM `0x03005800..0x03006FCB`의 6,092바이트가
  블루 문 ROM `0x212700..0x213ECB`와 완전히 동일하다. 이 구간은 비압축 직접 저장이다.
  다른 코드 뱅크와 메뉴 경로까지 같은 방식이라고 일반화하지 않는다.

선언된 스크립트 슬롯은 각 88,902개이며, TPL에 별도 인쇄되지 않은 74,356개도
16비트 LE 원본 포인터 표로 보존한다. 별칭/빈 엔트리/후속 영역의 소비자 분류는 미완료다.
이 793개는 인덱스 내부의 정확한 모집단이지만 게임 전체 텍스트의 하한이다.
인덱스 밖 문구, raw 아카이브 후속 영역, 이름 입력, 칩 이름/설명, 전투/통신,
별도 폰트와 이미지 문구의 소비자 전수 확인이 남아 있다.

## 번역과 개발 ROM

`translations/opening_korean.json`은 양쪽 공통 오프닝(아카이브 442)의
26개 스크립트, 59개 문구/페이지 단위 번역 초안이다. 상태는 `needs_review`다.
용어 선택은 `translations/glossary.tsv`에 기록한다.

`poc/output/*_opening_visibility_poc.gba`는 서문 5페이지/65글자 시험이다.
`poc/output/*_opening_korean_development.gba`는 오프닝 26개 스크립트/222글자 개발본이다.
위 두 종류는 기존 글자 칸을 재배정했던 **과거 시험본**이다.
과거 재현은 같은 빌더에 `--encoding temporary`와 해당 `--selection centered/opening`을
명시한다. 기본값은 현재의 `opening/extended`로 바꿨다.
**모두 NON-DISTRIBUTION**이다. 임시 글자 재배정이 오프닝 밖 일본어를 손상시키며,
별도 타일 메뉴 폰트는 원문 그대로다. 이 ROM으로 전체 게임을 플레이하거나 배포하지 않는다.
Galmuri11 2.24.29 BDF는 12픽셀 높이 경로를 검증하기 위한 기존 폰트 후보이며
최종 서체의 인간 승인이나 전체 한글 글리프 공급을 뜻하지 않는다.

원본 압축 바이트는 그대로 보존하고 수정한 오프닝만 ROM 끝으로 재배치한다.
25개 미선택 스크립트는 5페이지 시험에서 원본 바이트를 보존한다.
오프닝 전체 개발본은 타이머/이벤트/대기/점프/초상 제어 구조를 보존한다.
센터 정렬의 가로 예산 5개만 번역의 픽셀 폭에 맞춰 조정한다.
오프닝 일반 대화는 관측된 텍스트 시작 x=51에서 가로 180픽셀/3줄 이내로 검사한다.
매 빌드는 원본 기대 바이트, 쓰기 중첩, 전체 차분, append/FF 확장, 한글 매핑,
컴파일된 번역 바이트를 검사한다. 과거 시험본은 CPU 코드를 변경하지 않았다.

## 일반 대사 확장 기준선

`poc/output/*_opening_korean_extended_development.gba`가 현재 개발 기준선이다.
`F9 FC` 다음 두 바이트는 `U+AC00`부터의 한글 음절 번호(0..11171), little endian이다.
기존 일본어 문자표/글꼴/폭/팔레트를 보존하며, 확장 ROM에 원본 인덱스 호환 뷰와
한글 11,172개 96바이트 글리프 및 폭 테이블을 추가한다.
원본 인덱스 441은 글리프가 아니라 팔레트 별칭이므로 원래 읽던 96바이트와 폭 값도
호환 뷰에 그대로 복제하고, 한글 렌더 인덱스는 442부터 시작한다.

일반 대사 F9 디스패치와 누적 폭 F9 디스패치, IWRAM 출력기의 글꼴/폭 리터럴만
원본 기대 바이트와 대조해 연결한다. 기존 F9 하위 명령은 원래 처리기로 넘긴다.
ARM7TDMI ARMv4T Thumb-1으로 조립/독립 역어셈블 및 최종 배치 왕복 검사를 수행한다.
저장 형식, 메뉴 디코더와 별도 타일 글꼴은 변경하지 않았다.

각 버전의 모든 한글 글리프를 BDF의 실제 잉크/그림자 픽셀과 독립 대조했고,
제어 바이트를 포함한 11,172개 코드의 해석·스트림 전진·스택 복구를 제어된 CPU
fixture에서 실행했다. 이 fixture는 실제 게임 전체 검증을 대신하지 않는다.
두 원본의 인덱스 793개 전체에는 `F9 FC` 바이트 쌍이 없지만, 인덱스 밖/외부 문자열과
다른 카운트/선읽기 소비자까지 충돌 없는 새 코드라고 확정하지 않는다.

| 현재 확장본 | SHA-256 |
|---|---|
| 블루 문 | db3fb04fa3636d2f75b619293840d5ca6c1f3e6856b92bf4347e400ceb823351 |
| 레드 선 | 0c6c0425c36f55fda4f8167b11a865bb4bea95dda69d0de7316788000022b2b3 |

두 버전 모두 콜드부팅/일반 입력 70단계가 완료됐고, 오프닝 59문구와 마지막 응답,
넷토 방의 원래 일본어 대사를 확인했다. 실행 중 확장 글꼴의 정확한 222개 음절을
원래 IWRAM 출력기에서 읽은 기록도 확보했다.
별도 `*_hangul_boundary_visibility.gba`는 이야기 번역과 분리한 기능 시험이다.
첫/마지막 음절 `가/힣`, `E5/E8/FF/00`을 인자 바이트로 포함하는 음절, 복잡한 받침과
영문/숫자/줄바꿈을 두 버전 모두 실제 화면에서 확인했다. 다른 25스크립트는 원본 바이트다.

현재 무결성/실행 귀속은 `analysis/extended_verification.json`과
`analysis/boundary_verification.json`, 문구별 시각 판정은 `analysis/EXTENDED_RUNTIME_QA.json`이다.
새 TPL ↔ MSG도 바이트 왕복 및 작성한 문구의 정확한 재추출을 빌드에서 강제한다.
확장본 또한 **NON-DISTRIBUTION**이며 전체 게임 플레이/배포 완료를 뜻하지 않는다.

일반 대사 기준선의 메뉴는 원문이다. 아래 추가 개발본에서 관측한 두 타일 글꼴에
한글을 공급했지만, 전투/이름 입력을 포함한 모든 타일 소비자의 분류는 미완료다.

## 메뉴 추가 개발본

`poc/output/*_opening_menu_korean_development.gba`는 일반 대사 기준선에 메뉴 시험을
추가한 **NON-DISTRIBUTION** ROM이다. 오프닝 바이너리/글꼴/정상 대사 훅은 같은 구성이다.
메뉴 번역 초안 `translations/menu_korean.json`은 11스크립트다. 두 저장 화면 변형의
플레이 시간/데이터 도감/배틀칩/소지금 네 항목, 폴더1/2, 넷토의 방 장소 이름을 포함한다.
각 버전 원본의 ID/문구/페이로드 해시를 확인하고, 네 raw 아카이브의 미선택 스크립트
바이트와 EOF를 가리키는 빈 슬롯/별칭을 보존했다. TPL↔MSG 왕복과 정확한 문구 재추출도 검사한다.

각 버전의 인덱스에는 `mmbn4s` 스크립트 2,021개가 76아카이브에 있고,
그중 텍스트 스크립트는 1,806개/문자열 1,828개다. 게임 전체의 메뉴 수치는 아니다.
PET 상태 문자열의 런타임 주소 `0x6E73BC..`는 아카이브13의 240~243번으로 대조됐다.
처음 주소를 파일 이름만으로 찾지 못해 인덱스 밖이라고 추정했지만 실제로는 추출 목록 안이다.

8픽셀 셀에 9픽셀 잉크의 Galmuri9를 손실 없이 넣을 수 없으므로 Galmuri7 2.24.29를
기능 후보로 변환했다. 한글 4,363개를 두 원본 색상 방식에 맞춘 64바이트 글리프로 공급한다.
BDF 잉크 전부와 아래 방향 그림자를 8×16 셀에 보존한다. 최종 서체/배치의 인간 승인은 미완료다.
한글 번호 11,172개를 지원 여부 테이블에 연결하며 없는 글자는 FFFF다.
번역 수요 중 공급되지 않는 음절이 있으면 컴파일/ROM 쓰기 전에 빌드를 거절한다.
실행 중 미지원 번호/글꼴 뱅크는 명시적인 정지 루프로 차단하며 빈칸 대체를 하지 않는다.
이는 개발용 실패 차단이며, 다른 소비자의 글꼴을 모두 지원했다는 뜻이 아니다.

원본 IWRAM 소스의 F9 슬롯(`0x213650`)만 새 Thumb-1 처리기로 연결한다.
새 코드는 한글을 네 바이트로 해석하고 타일 한 개/문자 수 한 개를 전진시킨다.
FC가 아닌 F9의 다음 바이트는 기존 1바이트 printShortString 처리기로 넘긴다.
이전 작품의 오프셋을 이식하지 않았으며 두 버전 소스/글꼴을 각각 대조했다.
4,363×2색상×2버전의 제어 CPU 시험은 실제 원본 타일 출력 코드를 실행한다.
독립 픽셀 대조, 숫자/기존 명령 보존, 색상 가산과 미지원 번호/서체 차단도 검사한다.

| 메뉴 개발본 | SHA-256 |
|---|---|
| 블루 문 | 40b49cf6ac463f3a5e6d02d070f3ea367456188bed9c7f3e2ff6d98697b85acd |
| 레드 선 | 164433a06a42d5de30cf280ea1ed3d16314e89ebdab00a84a9c30891714b7b47 |

벤치 검사는 `analysis/menu_verification.json`, 제어 CPU 시험은 `analysis/menu_bench.json`이다.
두 버전 모두 순차 콜드부팅/일반 버튼107단계107캡처/종료0으로 완료했다.
PET 장소 이름, 폴더1, 저장 네 항목을 직접 시각 검토했고, 두 타일 뱅크의 실제21레코드
읽기와 입력 스트림/버퍼/글꼴 인자를 대조했다. 일본어 칩 이름, 숫자, NAME 짧은 문자열,
저장 질문과 아이콘도 관측한 화면에서 유지됐다.
`analysis/MENU_RUNTIME_QA.json`과 `analysis/visual_qa/menu_two_versions.png`에 기록했다.
폴더2/두 번째 저장 변형이 실제 화면에서 표시됐다는 주장이나 전체 메뉴 검증은 하지 않는다.
첫 블루 문 장시간 실행은104/107캡처 뒤 timeout으로 끝났으며 완료 실행으로 사용하지 않는다.
원본 글꼴과 팔레트는 변경하지 않고 새 데이터/기계코드/재배치 raw 메시지를 끝에 추가했다.
배포 조건으로는 다른 메뉴/전투/이름/카운트/선읽기 경로와 창별 버퍼 확인이 남아 있다.
정렬된 ROM 워드의 참조 조사에서는 두 글꼴 주소가 각각40/34곳, IWRAM 진입 주소가
한 곳에 있었다. 네 raw 아카이브의 추가 base 참조는 발견되지 않았고, 일부 내부 주소
후보는 버전마다 달랐다. 이는 포인터/명령 후보이지 소비자 완전성 증명이 아니다.
원본 raw 메시지를 남겼으며 내부 후보는 의미를 확정하기 전에는 재배치하지 않는다.
결과는 `analysis/menu_reference_census.json`에 있다.
일반 대사의 기존 F9 폴더 출력은 이름을64바이트 임시 버퍼에 복사하고 대사/폭 스캔의
스트림을 그 버퍼로 바꾼다. 메뉴7개 제어 시험에는 두 새 이름의 기존 native 전달 경로와
폭 스캔 버퍼도 포함한다. 복사 helper만 fixture로 대체했으며 실제 화면 전체 소비자 QA와 다르다.
원문 쉼표 누락 실패는 `analysis/rejected_menu_comma_reproduction`에 별도로 재현/보존했다.
컴파일 종료0이어도 원본15바이트/14스크립트 스팬이 손실돼 무변경 왕복/미선택 보존 검사가 필요했다.

## 과거 임시 코드 시험의 실행 확인

두 수정본을 각각 콜드부팅해 일반 버튼 입력 64단계를 순차 실행했다.
동일 ROM에서 자연 진행한 체크포인트만 해시로 연결해 마지막 응답과 장면 전환을 확인했다.
각 버전의 오프닝 59개 문구가 표시되는 캡처를 검토했고, 잘림이나 팔레트 색 블록은
관측되지 않았다. 이어지는 넷토의 방 대사는 일본어로 남아 있다.
독립 언어 검수, 전체 게임 및 실기 검증은 미완료다.

| 개발본 | SHA-256 | 검증 범위 |
|---|---|---|
| 블루 문 | 9d987469c3e55e43a51a0939302e92c3e825dd557876834e263ba6ee1ca15a8d | 오프닝 표시·마지막 응답·방 장면 전환 |
| 레드 선 | 23ef15f9c64340913c520876fde6ef340998bbfd1b9dd194a3409b6623422810 | 오프닝 표시·마지막 응답·방 장면 전환 |

문구별 캡처와 실행 해시는 `analysis/OPENING_RUNTIME_QA.json`,
원본/쓰기 계획/팔레트/실행 귀속 검사는 `analysis/project_verification.json`에 기록한다.
`analysis/visual_qa`의 네 접촉 시트는 최종 실행 캡처를 원래 해상도로 배열한 검토 자료다.

## 재현

Python 3.14, TextPet v1.0.0, Pillow 및 Capstone 5.0.7을 사용했다.
TextPet 인덱스/플러그인 근거: Prof9/TextPet commit
`6c6d70561290b42d8261f6d76b03051d534c7032`.
인덱스는 `exe4bm-v10.tpi`, `exe4rs-v11.tpi`이며 외부 도구/폰트의 경로와 해시는
산출물 manifest 및 `analysis/dependencies.json`으로 고정한다.
ARM 도구는 에그제 2에서 사용한 Keystone 0.9.2/Unicorn 2.1.4와 현재 Capstone 5.0.7을
`external/arm_debug_python`에 고정했다. 이 경로는 저장소/배포에 포함하지 않는다.
설치 재현 명령과 실제 라이브러리/바인딩 해시는 dependency 기록에 있다.
Thumb-1 인코딩 감사는 정의된 16비트 명령과 모든 명령/주소 지정 계열을 열거했고,
BL은 각 필드의 전체 값과 반대 필드 경계를 교차 검사했다. 22비트 모든 조합을 검사한 것은 아니다.
Keystone의 수치 전방 분기 경계 문제는 심볼 레이블 문법으로 처리하며 실제 훅도 내부 레이블을 쓴다.

```powershell
python tools/analyze_project.py --rom-dir "<원본 두 ROM 폴더>"
python tools/build_opening_poc.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --selection opening --encoding extended
python tools/build_opening_poc.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --selection centered --encoding extended --font-probe
python tools/test_dialogue_extension.py
python tools/audit_thumb1_toolchain.py
python tools/run_extended_qa.py --mesen "<Mesen.exe>"
python tools/run_extended_qa.py --mesen "<Mesen.exe>" --font-probe
python tools/verify_extended.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>"
python tools/verify_extended.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --font-probe
python tools/make_runtime_contact_sheets.py --run-suffix extended_v2_final
# 캡처를 직접 검토한 뒤에만 시각 판정 기록을 갱신한다.
python tools/record_extended_visual_qa.py
python tools/survey_menu_consumers.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri7.bdf>"
python tools/survey_menu_references.py --rom-dir "<원본 두 ROM 폴더>"
python tools/build_opening_poc.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --menu-font "<Galmuri7.bdf>"
python tools/record_menu_bench.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri7.bdf>"
python tools/run_menu_qa.py
python tools/verify_extended.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --menu-font "<Galmuri7.bdf>"
python tools/make_menu_contact_sheet.py
# 실제 두 버전 캡처를 직접 검토한 뒤에만 기록한다.
python tools/record_menu_visual_qa.py
python tools/record_artifacts.py
```

TextPet는 오류에도 종료 코드 0 또는 부분 파일을 남길 수 있으므로 로그와 출력 바이트를 검사한다.
Mesen은 `--testRunner --noAudio --doNotSaveSettings --preferences.singleInstance=false`와
일반 버튼 입력을 사용한다. 버전별 마지막 실행은 순차 실행하며 ROM 헤더/글리프/재배치 데이터
기대 바이트를 실제 로드된 ROM에서 검사한다. CJK Windows 경로를 Lua가
열 수 없어 출력 폴더 자체에 임시 SUBST 드라이브를 연결하고 종료 시 해제한다.
첫 상대 경로 시험이 Mesen 실행 폴더에 남긴 우리 산출물은 정확한 이름으로 이 프로젝트에 회수했다.
기본 실행은 과거 작품의 세이브/상태를 사용하지 않고 콜드부팅한다.
`opening_end`와 `opening_exit`는 직전 같은 ROM의 완료된 입력 실행 상태를 이어간다.
원본 실행 영수증, ROM 해시, 상태 해시와 에뮬레이터 구성 해시를 대조한다.
이미 증거가 있는 출력 폴더는 덮어쓰지 않으므로 재실행은 별도 프로젝트 복사에서 수행한다.
`--resume-only`와 `--exit-only`는 이미 완료된 앞 단계의 상태를 이용하는 재개 옵션이다.

전체 오프닝의 첫 시험에서는 442번째 레코드로 팔레트를 덮어 일반 대화가 색 블록이 됐다.
`*_opening_rejected_palette.gba`는 그 실패 기준선이며 현재 사용하지 않는다.
수정본은 441개 레코드 뒤 0x100바이트 팔레트 영역을 원본과 완전히 동일하게 보존한다.
첫 장시간 메모리 덤프 시험의 timeout과 거절된 시험본 실행 중단도 실패/부분 증거로 남겼다.
동시 실행의 종료/파일 생성 시점이 불명확한 `opening_palette_fixed` 증거는 최종 판정에서 제외했다.
과거 임시 코드 시험에서 수용한 실행은 `opening_final`, `opening_end`, `opening_exit`다.
위 실행은 과거 임시 매핑의 증거다. 일반 대사 기준선의 수용 실행은
`extended_v2_final`와 `boundary_final`, 메뉴 추가 개발본은 `menu_final_02`이며
각 버전에서 순차 콜드부팅했다.
첫 확장 시험의 폭 처리기가 `BX LR`로 짝수 Thumb 복귀 주소를 받아 ARM 상태로 바뀌었고,
첫 글리프 뒤 PC가 낮은 잘못된 주소로 빠졌다. 이 시험본은 `*_extended_rejected_return.gba`,
실행 추적은 `blue_moon_extended_return_trace`에 보존한다.
원래처럼 `MOV PC, LR`로 복귀하도록 수정했고 제어된 CPU 회귀 시험에 포함했다.
단일 MSG의 왕복에서는 폴더 출력 지정을 실패로 감지해 빌드를 중단했으며,
TPL/MSG 출력 파일을 각각 명시하는 계약으로 고쳐 바이트 왕복이 통과했다.

## 다음 완료 조건

2026-09-16 후속 조사: 초기 폴더를 두 버전 각각31단계/31캡처/종료0으로 끝까지 스크롤했다.
칩 이름 아카이브41의10종, 서로 다른 호출 인자58개씩을 실제 스트림/원문/ROM SHA와 대조했다.
BLUE `0802F4AC`, RED `0802F4E4`는 일반 메뉴 래스터 출력기와 다른 BG 타일맵 출력기다.
`F9`를 종료로 취급하므로 현재 한글 코드를 바로 넣으면 이름이 비거나 접두사만 남는다.
원래 함수 전체를 실행한 양쪽 ARMv4T fixture에서 이 동작을 재현했다.
채택한 `exe4_consumer_contracts_v1.json`은 현재 지원11개 스크립트만 허용하고 다른
짧은 문자열 소비자 선택은 컴파일/출력 폴더 생성 전에 거절한다. 폴더 이름의64바이트
인코딩 한계도 글자 셀 수와 별도로 검사한다. 대사6/메뉴7/소비자4 시험이 통과했다.

`translations/chip_names_korean_draft.json`에는 에그제2의 캐논·소드·리커버리10 용어를
참고한10종 초안이 있다. 최초 조사에서는 칩 화면의 VRAM 예약/적재가 미구현이라 제외했다.
후속 폴더 전용 개발 구현은 아래 절에 기록한다. 두 버전 실제 VRAM에서 원래 글꼴0..159의
10,240바이트가 `06004000`에 일치하는 것까지 확인했다. 다른 VRAM 사용의 분류가 남았다.
NAME는 실제 PET에서32비트 `00828282`를 세 번의 바이트 인덱스로 표시했다.
두 버전/두 스타일 fixture에서도4바이트 한글 스트림을 지원하지 않는 것을 확인했다.
이름 입력 `archive/418/script/11`의3개 옵션은 source-only 근거이며 실제 입력/저장 시험은 아니다.

조사 보고서는 `analysis/remaining_consumer_survey.json`, 다음 구현 조건은
`analysis/CHIP_EXTENSION_PLAN.md`에 있다. `*_battle_survey_01..04`는 방 안 이동 조사에
머물렀으며 전투 화면 도달/전투 QA로 인정하지 않는다. 새로운 빌드 검사를 적용해 재생성한
기존 두 메뉴 ROM의 SHA는 동일하고, 기존 완료107단계 실행과 독립 픽셀/차분 검사가 계속 유효하다.

```powershell
python tools/survey_remaining_consumers.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri7.bdf>"
python tools/test_consumer_contracts.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri7.bdf>"
python tools/make_chip_survey_contact_sheet.py
# 6개 실제 이미지를 직접 검토한 후에만 수동 시각 기록을 갱신한다.
python tools/record_chip_consumer_visual_qa.py
```

1. 일반 대사 확장 코드의 인덱스 밖/외부 문자열 충돌과 추가 디코더/폭/카운트/선읽기 소비자 전수 확인.
2. 두 관측 스타일 밖 메뉴 글꼴/전투/이름 입력 디코더, 셀/버퍼/적재 경로 전수 분류.
3. 인덱스 밖 및 후속 스크립트 모집단 확정, 전수 추출.
4. 공통/버전별 전체 번역과 독립 언어 검수, 창별 레이아웃 QA.
5. 완전한 통합 ROM의 자연 진행/저장/새 부팅/버전별 분기 및 기기 QA.
6. 원본과 전체 ROM을 포함하지 않는 차분 패치와 검증된 적용기 제작.

## 2026-09-16 후속: 폴더 전용 칩 이름 개발본

`--chip-folder`는 일반 대사·메뉴 확장 위에 초기 폴더의10종 칩 이름을 추가한다.
원래 아카이브41과 다른7개 참조는 그대로 두고 폴더 선택기의 포인터1개만 복제본으로 바꾼다.
다른 소비자에 같은 번역 아카이브를 자동 재배치하지 않는다. 초안은 `needs_review`이며
에그제2의 캐논·소드·리커버리10 용어를 참고했다. 최종 서체/독립 언어 검수는 미완료다.

원래 글꼴은 `06004000..060067FF`, 칩 아이콘7개는 `06006800..06006B7F`를 사용한다.
처음 후보였던 아이콘 구간은 제외했다. 실제 폴더/편집/재진입 조사에서 새 복사와 겹치지 않은
`06006B80..06006FFF`의18음절과 `06007360..060074DF`의6음절에 총24음절/1536바이트를 적재한다.
원래160글리프와 새 두 구간의 복사를 폴더 초기화 때 함께 요청한다. 전체4363글리프를
VRAM에 상주시킨다는 의미가 아니다. 예상 원본 쓰기3개와 최종 배치 ARM7TDMI 바이트를 검증한다.

개발 ROM은 `poc/output/*_opening_menu_chip_folder_korean_development.gba`이다.
BLUE SHA256: `44c338623fb644edde81344da28b609cbc2d3dfce41141cb82af4e7f2818c2f5`
RED SHA256: `938d3893cb01d869953fcdcaa7c782d32524104a4a87a647e1091efe8b4cf493`
기존 메뉴 ROM SHA는 유지된다. 원본과 전체 개발 ROM은 NON-DISTRIBUTION이며 배포 패치가 아니다.

```powershell
python tools/build_opening_poc.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --menu-font "<Galmuri7.bdf>" --chip-folder
python tools/record_chip_bench.py
python tools/run_chip_folder_qa.py --key blue_moon
python tools/run_chip_folder_qa.py --key red_sun
python tools/verify_extended.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --menu-font "<Galmuri7.bdf>" --chip-folder
python tools/make_chip_folder_contact_sheets.py
```

이미 있는 실행 폴더는 덮어쓰지 않는다. 재시험은 실행 이름을 새로 선언한다.
CPU 시험은 양쪽 원래 폴더 함수 전체에서256항목 중 미선택 출력 보존,10개 새 이름,
실제 복사 큐 함수의3개 요청, 없는/범위 밖 음절/9번째 셀의 정지와 범위 밖 쓰기 방지를 검사한다.
두 버전 모두107/107 콜드부팅과38/38 폴더 검사/종료0을 완료했다. 각31개 폴더 캡처에서
이름 버퍼와 BG 타일맵이 일치했고, 편집/재진입을 포함한33개 캡처의24음절 캐시가 ROM과 일치했다.
18개 캡처에서10종 칩 이름, 원래 아이콘/코드/용량 숫자, 편집의 원래 설명, PET 복귀를 직접 확인했다.
실제 실행/캡처/ROM 해시의 판정은 `analysis/chip_verification.json`과
`analysis/CHIP_FOLDER_RUNTIME_QA.json`을 따른다. 전투·도감의 칩 이름, 새 이름 입력,
나머지 칩 이름·전체 번역·저장 구조·기기 QA는 아직 완료하지 않았다.

## 2026-09-16 후속: 전체 이름 초안과 도감 소비자 조사

source pool41..44의391개 항목을 두 버전에서 대조했다. folder chooser의 원본 ROM 경로는
chipID0..310이며311부터 RAM 특별 문자열을 읽는다. 이 경로의 reserve/empty를 제외한294개
이름 초안을 `translations/chip_catalog_authored.tsv`와 파생 `chip_catalog_korean_draft.json`에 작성했다.
전투용 내부 이름이 섞여 있어294개를 플레이어가 장착할 수 있는 칩 수로 취급하지 않는다.
또한 도감 표시 번호와 source chipID가 다르다: 실제5번 표시는 source15의발칸1이었다.

EXE2 용어집의22개 정확한 일치를 유지하고 기존10종 문구도 보존했다. 모든 이름8칸 이내,
Galmuri7 한글 수요204음절/누락0이며, 두 아카이브를 양쪽 각각 컴파일해 MSG 바이트 왕복과
미선택 원문 스팬 보존을 검증했다. 최초 분석 산출물은 ROM을 만들지 않는 research compile이었고,
이후 아래의 도감 전용 7행 소비자에만294개 복제본을 넣었다. 언어 검수는 여전히 needs_review다.

실제 도감 source6단계/BG8단계/PPU2단계의 각 완료/종료0과 원래 파서 전체 CPU 검증을 수행했다.
도감은136글리프,7개 아이콘 및7400의라벨을 쓰므로 폴더와 같은 캐시 배치를 적용할 수 없다.
6580..73FF의58글리프 후보는 관측 활성 복사와 겹치지 않았고, 기본 탭 PPU 상태의4개BG 전체
4096개 타일맵 엔트리에서도 기존 참조0개였다. 이 중6580..737F를7행×8칸56글리프 슬롯으로 채택했고,
다른 호출은 원문을 유지한다. 구현·검증 결과는 `analysis/LIBRARY_EXTENSION_PLAN.md`에 있다.

```powershell
python tools/prepare_chip_catalog.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri7.bdf>" --glossary "<EXE2 translations/glossary.tsv>"
python tools/analyze_library_consumer.py --rom-dir "<원본 두 ROM 폴더>"
python tools/make_library_contact_sheet.py
# 실제6개 캡처를 직접 본 후에만 기록한다.
python tools/record_library_visual_qa.py
```

## 2026-09-16 후속: 도감294종 전용 개발 구현

`--library-chips`는 `--chip-folder`와 `--menu-font` 위에서만 켤 수 있다. 원본 archive41/42의
모든 포인터는 유지하고, 실제 도감7행 버퍼 `02016600`의 정렬된 호출에서만 private clone을 고른다.
BLUE `08037F58`, RED `08037F8C`의12바이트 창은 원본 해시와 함께 고정했으며, 공용 파서나 다른
5행/특수 소비자를 바꾸지 않는다. 294개 초안은 개발 도감 삽입만 허용되고 다른 소비자는 제외된다.

각 셀은 `06006580..0600737F`의56개64바이트 슬롯을 사용한다. 화면에 필요한 글리프만 기존
`0800098C` CpuSet 래퍼로 Galmuri7 전체 ROM bank에서 직접 복사한다. 타일은 원래 `E200`의
팔레트 상위 비트를 보존하고, 네이티브 단일바이트와0 padding도 유지한다. 누락/범위 밖/9번째 셀은
대체 문자 없이 명시적으로 정지한다. 폴더 화면이 같은 VRAM 일부를 덮어도 도감 재진입 때 다시 채운다.

개발 ROM과 SHA256은 다음과 같다. 원본과 개발 ROM은 NON-DISTRIBUTION이며 배포 패치가 아니다.

- BLUE: `poc/output/blue_moon_opening_menu_chip_folder_library_korean_development.gba`
  `b10f56a147ec5e025c80bf8e0b84d2ab152e1a0232b79afcd15234d5950db09e`
- RED: `poc/output/red_sun_opening_menu_chip_folder_library_korean_development.gba`
  `13ee7822bc281f9717dce0029ca20f13cbc5013b4e522c9a1b3a7394b762dd6e`

```powershell
python tools/build_opening_poc.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --menu-font "<Galmuri7.bdf>" --chip-folder --library-chips
python tools/record_library_bench.py
python tools/run_library_qa.py --key blue_moon
python tools/run_library_qa.py --key red_sun
python tools/record_library_runtime_qa.py
python tools/verify_extended.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --menu-font "<Galmuri7.bdf>" --chip-folder --library-chips
```

CPU 시험은 두 판본의 ROM ID0..310 전부, 번역294개,7개 행, 실제 copy wrapper의 CpuSet 의미,
원문 fallback과 세 오류 정지를 검사한다. 두 판본은 새 제품 해시로 각각107/107 콜드부트와25/25
도감·메가탭·폴더·재진입을 완료했다. 실제 저장 데이터에서 등록된 sourceID1/4/15만 자연 표시할 수
있으므로 화면에서는 캐논·에어슛·발칸1을 확인했고,294개 전부 자연 화면에서 봤다고 주장하지 않는다.
`analysis/LIBRARY_RUNTIME_QA.json`과 `analysis/library_verification.json`이 채택 증거다. RAM 특별
ID311 이상, PA/soul/special의 나머지 소비자, 전투·이름 입력·통신·전체 게임·기기 QA와 독립 언어 및
최종 서체 승인은 남아 있다.

## 2026-09-17 후속: 전투 칩 선택창 이름 표시

블루 문 `0801FB64`, 레드 선 `0801FBA0`의8바이트 호출 준비 부분만 바꿔,
Custom Screen에서 강조된 칩의 이름을 기존 private archive41/42에서 선택한다.
기존 메뉴 Galmuri7 렌더러가 원래512바이트 버퍼 `0203E590`을 채우고,
원래 전송 경로가 `06009380`에 복사한다. 새 VRAM 공간은 할당하지 않는다.
다른 전투 이름·설명·공용 원문 아카이브는 이 옵션의 번역 대상이 아니다.

`--battle-caption`은 `--library-chips` 위에서만 켜며294개 초안의 문구와 needs_review 상태를
유지한다. 도감용 입력 계약을 자동으로 모든 소비자에 적용하지 않고, 별도의
`tools/specs/exe4_battle_caption_v1.json`에 이 호출 지점의 원본 바이트·문맥·글꼴을 고정했다.

- BLUE SHA256: `630bd9b425f4f0b0b2c6ffc5b17b2413bf50b4dabc2708b20521246772420a1f`
- RED SHA256: `44c85aba141fa37083a3c0489bc0eea25d2d9dd8398d9f329217bc6332c68a26`

양쪽 원본 대비 예상 쓰기, 중복/미계획 쓰기 부재, 최종 ARM7TDMI 바이트를 검증했다.
이전 도감 개발본과 달라진 곳은8바이트 호출 훅과 뒤에 추가한 선택 함수뿐이다.
CPU 시험은 각 ID0..310 전체,294개 번역의 정확한 글자/tint8/빈칸, 나머지17개 원문 출력,
버퍼 경계와 레지스터 보존을 검사했다. CPU의 마지막 DMA 큐 전송은 시험용 대체 함수였으므로
실제 전송은 아래의 에뮬레이터 RAM/VRAM 대조로 별도 확인했다.

두 판본 모두 새 ROM 콜드부트에서 일반 입력으로 첫 전투까지 진행했다. 최초263입력/17캡처
묶음은 체크포인트 경로와 이동 결과가 달라 부엌에서 끝났으며 전투 도달 증거로 취급하지 않는다.
같은 ROM의 검증된 체크포인트에서 route02..04의30입력으로 오븐에 접속하고,
ready01의35입력으로 칩 선택창에 도달했다. 최종6단계와 별도 호출 조사6단계에서
캐논(ID1)·미니봄(29)·소드(48)·리커버리10(107)을 확인했다. 두 판본 총12캡처에서
독립적으로 재구성한512바이트 글자 데이터, 실제 RAM, 실제 VRAM이 모두 일치했다.
칩 그림·코드·수치와 커서 이동도 직접 확인했다.294개 전체의 자연 획득/표시는 검증하지 않았다.

```powershell
python tools/build_opening_poc.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --menu-font "<Galmuri7.bdf>" --chip-folder --library-chips --battle-caption
python tools/verify_battle_caption.py --rom-dir "<원본 두 ROM 폴더>"
# 실행 폴더가 없는 새 재현 환경에서 두 판본에 각각 실행한다.
python tools/run_battle_caption_qa.py --key blue_moon
python tools/run_battle_caption_followup.py --key blue_moon
python tools/run_battle_caption_qa.py --key red_sun
python tools/run_battle_caption_followup.py --key red_sun
# 두 판본 final01의12개 캡처를 직접 확인한 후 기록한다.
python tools/record_battle_caption_qa.py
python tools/record_artifacts.py
python tools/verify_artifact_manifest.py
```

채택 근거는 `analysis/battle_caption_verification.json`, `analysis/BATTLE_CAPTION_RUNTIME_QA.json`,
`analysis/visual_qa/battle_caption_two_versions_01.png`다. 과거 `battle_route_05..42`의
이동 탐색은 전투 QA가 아니다. 다음은 선택창 밖의 사용 중 칩 이름과 칩 설명 소비자 조사다.
다른 전투/PA/soul/special/RAM311+/NAME/저장/통신, 전체 번역, 독립 언어·최종 서체·기기 QA는 남아 있다.

## 2026-09-17 후속: 전투 중 사용 대기 칩 이름과 설명 초안

`--battle-active`는 `--battle-caption` 위에 전투 화면 왼쪽 아래의 사용 대기 이름을 추가한다.
BLUE `08015030`, RED `08015064`의8바이트 창에서만 기존 private 이름 복제본을 선택한다.
선택창과 같은512바이트 버퍼/VRAM/글꼴을 사용하되, 원래 전투용 tint0을 유지한다.
원래 호출자는 반환된 글자 수를 공격력 숫자 배치에 쓰므로 모든294개 번역에서 바이트 수가 아닌
글자 수를 반환하는지도 검사했다. 숫자와 그리기/지우기 함수는 원래 경로를 사용한다.

- BLUE SHA256: `e9ce575ce682cf23f460671c37d46a032d2b0875ec55729817833e6cac96fa65`
- RED SHA256: `bbf5aec22e26dedb086c717a9bd36d4f51ef9217e0657082337b39cb4a177d73`

기존 선택창 개발본과의 전체 차이는 새8바이트 훅과 추가 선택 함수뿐이다. 예상 원본 쓰기,
최종 ARM7TDMI 코드,311개 ID/번역294개/원문17개/버퍼 경계/레지스터/글자 수 검사를 통과했다.
각 새 ROM의 콜드부트부터 첫 전투까지 같은 ROM 해시의 체크포인트로 재현했다.
실제 전투에서는 캐논40과 미니봄50을 확인했다. 두 판본의12개 이름 캡처에서 ROM 글리프와
RAM/VRAM512바이트가 일치하고, BG3 상하 타일맵의 이름과 숫자 위치도 일치했다.
6개 소비 후 캡처에서는 해당16칸×2행이 지워졌고, 선택창 복귀 후 다음 칩 이름이 다시 표시됐다.
실제294개 전체 획득/표시, 모든 전투 경로 또는 완성된 한글패치를 뜻하지 않는다.

```powershell
python tools/build_opening_poc.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --menu-font "<Galmuri7.bdf>" --chip-folder --library-chips --battle-caption --battle-active
python tools/verify_battle_active.py --rom-dir "<원본 두 ROM 폴더>"
# 새 재현 환경에서 실행. 기존 실행 폴더는 덮어쓰지 않는다.
python tools/run_battle_active_qa.py --key blue_moon
python tools/run_battle_active_followup.py --key blue_moon
python tools/run_battle_active_qa.py --key red_sun
python tools/run_battle_active_followup.py --key red_sun
# 실제 캡처를 직접 확인한 뒤 기록한다.
python tools/record_battle_active_qa.py
```

검증 기록은 `analysis/battle_active_verification.json`, `analysis/BATTLE_ACTIVE_RUNTIME_QA.json`,
`analysis/visual_qa/battle_active_two_versions_01.png`이다. 원본과 이전 개발본을 보존했다.

칩 설명도 별도로 준비했다. BLUE 선택창에서 R을 누르면 archive54/script1을 선택하고
일반 대사 출력기 `03006A48`로 캐논 설명20글자를 그리는 것을 관측했다. raw archive54는
두 판본 각각256개 스크립트/4개 참조가 있으며, 나머지3개 참조의 실제 소비자는 아직 미분류다.
초기10종 설명을 수작업 번역하고 기능 수치·줄바꿈·제어 명령·양쪽 원문 바인딩을 보존했다.
Galmuri11 수요71음절에 누락이 없고, 양쪽 MSG 바이트 왕복/정확한 문구 재추출과 미선택246개
스크립트 보존을 확인했다.132픽셀/3줄은 현재 연구용 예산이며 실제 한글 설명 화면 검증은 남아 있다.

`translations/chip_description_authored.json`, `translations/chip_descriptions_korean_draft.json`과
`analysis/chip_description_analysis.json`은 **연구용 초안**이며 새 ROM에도 삽입하지 않았다.
재현 도구는 `python tools/prepare_chip_descriptions.py`다. 다음 작업은 선택창 설명의 소비자 계약과
한글 설명 삽입·창 열기/닫기/스크롤 검증이다. 설명 번역과 전체 게임·독립 언어·기기 QA는 미완료다.

## 2026-09-19 후속: 선택창 설명10종 개발 삽입

`--chip-descriptions`는 `--battle-active` 위에서 켠다. 초기10종 설명을 포함한 archive54 복제본을
추가하고 BLUE `1FCE4`, RED `1FD20`의 설명 선택창 포인터 하나만 바꾼다. 실행 코드 변경은 없다.
원본 archive54와 다른3개 참조는 유지한다. 입력 문구의 needs_review 상태도 유지하며,
별도 `exe4_description_v1.json` 계약이 허용하는 개발 소비자에서만 초안을 사용한다.

- BLUE SHA256: `342642391ead8f10ac1ad99369ed35be3acbb2f1c16033c5fa3f9d654cf540d8`
- RED SHA256: `c622fb0768f4b3daaaeda3ad8d0bc0f440af50a1df38d0e687e73f6a9443273d`

전체 차분은 포인터4바이트와 복제본 추가에 한정된다. 실제 원본 선택 코드의 끝부분을
각514개 입력으로 실행해 선택 인덱스와 반환 동작을 대조했다.256개 스크립트 전부를 검사해
번역10개가 정확한 문구와 원래 제어 명령을 담고, 미선택246개는 원문 바이트를 보존함을 확인했다.
10개 설명의 한글 수요는71음절이고 가장 긴 줄은123픽셀이다.132픽셀/3줄은 보수적인 작성 예산이며
게임 창의 전체 물리적 한계라고 주장하지 않는다.

두 판본의 새 ROM을 콜드부트해 선택창까지 자연 진행했다. 각각16단계 화면/메모리 검사와
같은 체크포인트에서 별도16단계 글꼴 읽기 검사를 수행했다. 캐논·미니봄·소드·리커버리10을
직접 확인했고 소드 설명은 다시 열어 확인했다. 합계10회 창 열기/닫기에서 한글 글리프 집합이
정확히 일치했으며, 앞선 설명의 잔상이나 잘림을 관측하지 않았다. 기존 칩 이름 VRAM512바이트는
설명 창을 열기 전·열린 중·닫은 뒤 모두 같았다. 나머지6종의 자연 표시와 다른3개 참조 경로의
한글 설명은 아직 검증하지 않았다.

```powershell
python tools/prepare_chip_descriptions.py
python tools/adopt_description_contract.py
python tools/build_opening_poc.py --rom-dir "<원본 두 ROM 폴더>" --font "<Galmuri11.bdf>" --menu-font "<Galmuri7.bdf>" --chip-folder --library-chips --battle-caption --battle-active --chip-descriptions
python tools/verify_descriptions.py --rom-dir "<원본 두 ROM 폴더>"
# 기존 실행 폴더가 없는 새 재현 환경에서 실행한다.
python tools/run_descriptions_qa.py --key blue_moon
python tools/run_description_reads.py --key blue_moon
python tools/run_descriptions_qa.py --key red_sun
python tools/run_description_reads.py --key red_sun
# 실제 final01 캡처를 직접 확인한 후 기록한다.
python tools/record_descriptions_qa.py
python tools/record_artifacts.py
python tools/verify_artifact_manifest.py
```

채택 근거는 `analysis/descriptions_verification.json`, `analysis/DESCRIPTIONS_RUNTIME_QA.json`,
`analysis/visual_qa/descriptions_two_versions_01.png`다. 앞 절의 연구용 설명 컴파일 기록과 달리,
이 옵션의 제품에는 전용 복제본이 삽입된다. 이전 개발본과 원본은 그대로 보존한다.
다음은 폴더·도감 등 나머지 설명 참조의 소비자를 조사하는 것이다. 전체 설명·대사 번역,
다른 전투/NAME/저장/통신·독립 검수·기기 QA는 여전히 남아 있다. 완성판이나 배포용 패치가 아니다.

## 2026-09-20 후속: 폴더·도감 설명10종 개발 삽입 (9칸 재작성)

`tools/build_menu_descriptions.py`는 앞 절의 `--chip-descriptions` 제품을 기준본으로 받는다. 같은 archive54의 설명을 폴더 편집
화면과 도감7행 화면에도 연결한다. BLUE `106AC4`(폴더)·`1098A8`(도감), RED `106B34`·`109918`의
포인터 각4바이트만 바꾸고 전용 복제본을 덧붙인다. 실행 코드 변경은 없다. 네 번째 참조
BLUE `106DAC` / RED `106E1C`는 소비자를 분류하지 못했으므로 원문 포인터를 그대로 둔다.

- BLUE SHA256: `770836ad7ed268c766f1d8cb56790dc109aede3258250cea0ebcad52d015db7d`
- RED SHA256: `ec7aea0fc00c318581fe3476d69525e6885c0f85c0405f8b84b03bac6ee0e7e7`

전체 차분은 두 판본 모두10,368바이트이고 복제본 추가와 포인터8바이트뿐이다. 256개 스크립트를
전부 검사해 번역10개만 정확한 문구로 바뀌고 미선택246개는 원문 바이트를 보존함을 확인했다.
두 실제 선택자를 각311 ID로 실행해 인덱스·반환·스택을 대조했고,10개 설명이 네이티브 파서에서
정확히1,920바이트를 만드는 것도 확인했다. 한글 수요는67음절이다.

**칸 한도는9다.** 네이티브 파서는 한 줄에10칸을 채우지만 OAM에는 줄마다8×16 스프라이트가
9개만 올라간다. 열 번째 칸의 글자는 버퍼에는 있어도 화면에 제출되지 않는다. 10칸 기준으로
쓴 앞선 제품(BLUE `2b48d2b7…`, RED `55d4b27d…`)은 이 이유로 거절하고
`analysis/rejected/menu_descriptions_10cell/`에 근거와 함께 보존했다. RAM=VRAM 일치는
표시된 문구가 온전하다는 증거가 아니다. 현재 문구는 모든 줄이9칸 이하이고, 기록기는
열 번째 칸이 빈 칸(`0x11` 64바이트)인지도 매 캡처에서 단언한다.

두 판본의 새 ROM을 콜드부트해 폴더 편집과 도감까지 자연 진행했다. 각51단계 캡처에서
폴더10종과 도감 등록3종(ID 1·4·15)의 설명을 검사했고, 각 캡처마다 예상 타일1,920바이트가
EWRAM 버퍼와 VRAM에 동일한지, 줄마다 아홉 개의 OBJ 셀이 정확한 타일/좌표/팔레트로 올라갔는지,
그리고 화면 픽셀3,456개의 잉크 기하가 글리프 비트맵과 일치하는지 대조했다. 미등록 항목과
메가 클래스 탭(3단계)에서는 설명 사각형이 단색이어서 앞 설명의 잔상이 남지 않음을 확인했다.
폴더로 돌아온51단계에서 설명이 복구되는 것도 확인했다. 두 판본 합계30개 캡처다.

```powershell
# 기준본은 앞 절의 --chip-descriptions 제품이다. 이 단계는 별도 빌더로 그 위에 얹는다.
python tools/prepare_menu_chip_descriptions.py
python tools/adopt_menu_description_contract.py
python tools/build_menu_descriptions.py
python tools/verify_menu_descriptions.py
# 기존 실행 폴더가 없는 새 재현 환경에서 실행한다.
python tools/run_menu_descriptions_qa.py --key blue_moon --stage cold
python tools/run_menu_descriptions_qa.py --key blue_moon --stage final
python tools/run_menu_descriptions_qa.py --key red_sun --stage cold
python tools/run_menu_descriptions_qa.py --key red_sun --stage final
# 실제 final_02 캡처4장을 직접 확인한 후에만 기록한다.
python tools/record_menu_descriptions_qa.py
python tools/record_artifacts.py
python tools/verify_artifact_manifest.py
```

채택 근거는 `analysis/menu_descriptions_verification.json`,
`analysis/MENU_DESCRIPTIONS_RUNTIME_QA.json`,
`analysis/visual_qa/*_menu_descriptions_{folder,library}_02.png`다.
네 번째 참조의 소비자, 나머지 카탈로그 설명, 도감10항목의 자연 표시, 독립 언어·서체 검수,
전체 게임과 기기 QA는 여전히 남아 있다. 완성판이나 배포용 패치가 아니다.

### 네 번째 참조 정적 조사 (2026-09-20)

`tools/survey_fourth_description_reference.py` → `analysis/fourth_description_reference_survey.json`.
설명 아카이브 주소와 같은 정렬 워드4개를 원본에서 다시 세고, 각각을 실을 수 있는 명령을 훑는다.
Thumb PC상대 LDR·ARM 리터럴 LDR·Thumb ADR과 그 주소를 가리키는 정렬 워드를 본다.

| 참조 | BLUE | RED | 직접 적재 | 그 주소를 가리키는 워드 |
|---|---|---|---|---|
| 전투 선택창 | `1FCE4` | `1FD20` | 0 | **1** (표 기준점) |
| 폴더 편집 | `106AC4` | `106B34` | **1** | 0 |
| 도감7행 | `1098A8` | `109918` | **1** | 0 |
| 미분류 | `106DAC` | `106E1C` | 0 | 0 |

미분류 참조는 폴더 풀과 **모양이 같은5워드 블록**의 첫 워드다(아카이브54·55, VRAM `06011600`,
폰트, 목적지 `02017800`). 폰트 워드만 메뉴 폰트가 아니라 일반 대사 폰트(BLUE `08695004`)다.
그 다섯 워드 전부 적재하는 명령이 없고, 바로 앞40바이트 루틴은 폴더 쪽 쌍둥이와 **3바이트만
다르며**(한 필드 오프셋과 BL 인코딩, BL 대상은 서로 다른 함수) BL 호출자가 없다. 두 판본 동일하다.

**이것으로 "안 읽힌다"고 결론 내리지 않는다.** 같은 표에서 전투 선택창 참조도 직접 적재가0인데
실제 소비자다 — 표 기준점 워드로 닿는다. 조사가 훑은 것은 아는 주소지정 형태뿐이고
([[exhaustive-is-not-complete]] 부류), 호출자 0건은 진입점을 4바이트만 틀려도 나온다.
그래서 조사 도구는 분류된 두 참조의 단일 적재와 관측된 두 루틴의 BL 호출자를 **양성 대조로
먼저 통과**시키고, 실패하면 음성 결과를 기록하지 않는다. 판정은 `0x08106DAC`/`0x08106E1C`에
읽기 BP를 건 런타임 조사가 해야 한다.

## 2026-09-20 착수: 본편 대사 모집단·조판 예산·전수 추출

지금까지는 화면 하나씩 소비자를 계약으로 고정해 왔다. 본편 대사는 그와 다르다 —
일반 대사 렌더러의 F9FC 확장이 이미 구현·런타임 검증돼 있고, 그 공급 **11,172자는
현대 한글 음절 블록 U+AC00..U+D7A3 전체**다. 즉 본편 대사 경로에는 **글리프 예산 문제가 없다.**
남은 것은 모집단 확정, 조판 예산, 번역, 빌드, 검증이다.

### 모집단 (`tools/survey_dialogue_population.py` → `analysis/dialogue_population.json`)

| 항목 | 값 |
|---|---|
| 색인된 아카이브 | 793 (두 판본) |
| 이름 붙은 계약이 소유한 아카이브 | 41·42·54·55·418·442 + 채택된 메뉴 11스크립트의 아카이브 |
| 이야기 후보 아카이브 | 710 |
| 일본어를 담은 id | 25,302 |
| 두 판본 원문이 같은 id | 25,186 (99.5%) |
| 판본별로 갈리는 id | 71 (+ 한쪽에만 45/48) |
| 서로 다른 일본어 줄 | 18,847 |

두 판본의 원문이 99.5% 같으므로 **번역 한 벌이 양쪽을 덮는다.**

### 조판 예산 (`tools/survey_dialogue_layout.py` → `analysis/dialogue_layout_budget.json`)

폰트는 비례폭이다. 글자 수로 세면 예산이 부풀거나 줄어들므로, **렌더러가 적재하는 폭 표**
(BLUE `0x51588`, RED `0x515B8`, 442칸 × 4바이트, 실제 값은 8과 11 두 가지)로 모든 줄을 쟀다.
한글은 확장이 넣는 고정 **12픽셀**이라 픽셀 예산이 곧 음절 수다.

- 리터럴의 줄 수는 게임 전체에서 **최대 3줄**이다(1줄 9,538 / 2줄 9,290 / 3줄 7,511).
- 이야기 아카이브 710개의 **자기 최장 줄**: p50 173px · p90 176px · p99 195px.
- 일반 대사 중 가장 넓은 줄은 198px. 그보다 넓은 7개 아카이브는 **다른 창**이다 —
  BBS 목록 5종(241px), 미스터리데이터 목록(244px), 엔딩 크레딧 한 줄(447px).
- 채택: **한 줄 180px = 한글 15자, 한 쪽 3줄.** 180px는 이미 런타임 검증된 오프닝 빌드가
  강제하는 값이고, 이야기 아카이브 p90 위·관측된 최장 일반 대사 아래다.
  이것을 **물리적 창 폭이라고 주장하지 않는다**(관측 상한일 뿐이다).

### 전수 추출 (`tools/extract_story_text.py` → `translations/story_source.jsonl`)

계약이 소유한 아카이브를 뺀 **23,758 레코드**. 원본은 스크립트 언어로 두 종류를 구분하는데,
이 둘은 서로 다른 작업이다:

| 분류 | 레코드 | 아카이브 | 서로 다른 줄 | 일본어 글자 |
|---|---|---|---|---|
| `story` (mmbn4, 대사창) | 22,919 | 694 | 17,184 | 489,595 |
| `short` (mmbn4s, 라벨·크레딧) | 839 | 32 | — | — |

**`short`는 이야기 번역에 넣지 않는다.** 짧은 라벨은 각자 소비자가 따로이고, 그중 일부는
대사 인코더의 선두 바이트에서 종료한다(아카이브41이 그랬다). 소비자 계약을 하나씩 받아야 한다.
레코드마다 원본 payload/TPL 해시를 묶고, 원문 각 줄의 실제 픽셀 폭을 함께 적는다 —
일본어일 때 이미 창 끝에 닿아 있던 줄은 늘릴 자리가 없다. `story` 중 원문이 180px를
넘는 것은 10건뿐이다.

### 게이트 (`tools/check_story_translation.py`, `tools/test_story_gate.py`)

배치를 컴파일러에 넣기 전에 거른다: 시트에 없는 id, 원본 바인딩 이동, `short` 분류,
4줄 이상, 180px 초과, 인코딩 불가 문자(자모 낱자 포함), 번역 안 된 가나·한자 잔류,
중복 id, 판본이 갈리는데 한쪽 문구만 쓴 경우. 진척도 함께 보고한다.
**게이트가 실패할 수 있음을 먼저 증명한다** — `test_story_gate.py`가 실제 시트 레코드로
항목마다 한 가지씩 깨뜨려 12건을 검사하고, `record_story_bench.py`가 그 로그를 묶는다.
게이트는 12건 PASS다.

```powershell
python tools/survey_dialogue_population.py
python tools/survey_dialogue_layout.py
python tools/extract_story_text.py
python tools/record_story_bench.py
python tools/check_story_translation.py
python tools/record_artifacts.py
python tools/verify_artifact_manifest.py
```

아직 한 줄도 번역하지 않았고 ROM에 넣지도 않았다. 다음은 (1) 배치 번역, (2) 아카이브
하나만 고치던 기존 빌더를 전 아카이브 재삽입으로 확장, (3) 자연 진행 런타임 QA다.
이 조사들은 **이 아카이브들이 일반 렌더러에서 그려지는 것을 관측했다고 주장하지 않으며**,
색인된 아카이브가 ROM의 모든 텍스트라고도 주장하지 않는다.

### 구두점 제약 (본편에서 오프닝의 수를 못 쓴다)

폰트 표에 있는 문장부호는 28종뿐이다. 없는 것 중 둘이 중요하다.

- **ASCII 쉼표 `,` 글리프가 없다.** 오프닝 빌드는 표의 `、` 항목을 `,`로 **바꿔치기**해서
  썼는데, 그러면 그 표로는 일본어 `、`를 인코딩할 수 없다. 오프닝은 아카이브 전체를
  번역했으니 문제가 없었지만, 본편은 번역문과 미번역 일본어가 **한 아카이브에 섞인다.**
  메뉴 단계에서 이 수가 실제로 거절됐다(`reproduce_menu_comma_rejection.py`:
  TextPet 종료 코드 0인데 15바이트/14스팬 누락). 그래서 본편 번역은 **`、`(U+3001)를
  쉼표로 쓰거나 쉼표를 쓰지 않는다.** 게이트가 ASCII 쉼표를 거절한다.
- **말줄임표 글리프가 없다.** 원문은 `・`(U+30FB)를 반복해 쓰는데, 그건 가나 영역이라
  "번역 안 된 가나" 검사에 걸린다. 한국어에는 `.`(U+002E) 세 개를 쓴다.

`、`·`。`·`「」`는 가나 영역 밖이라 그대로 쓸 수 있다.

### 배치 001 (`translations/story_authored/batch_001.json`)

오퍼레이션 배틀(통신 대전) 메뉴의 명인 설명. 아카이브 **3(Blue Moon)과 4(Red Sun)의
원문이 바이트 동일**이라 한 벌을 양쪽에 적용한다 — 두 판본이 같은 내용을 다른 슬롯에
넣은 사례다. 40 레코드 × 2 아카이브 = **80 엔트리, 게이트 0 problems.**

`tools/prepare_story_batch.py`가 작성본에 id와 원본 바인딩을 붙이고, 그 아카이브의
story 레코드가 **하나라도 빠지면 거절**한다. 작성 중 `script/17/literal/0`을 한 칸
어긋나게 매핑했는데, 그걸 계기로 **원문과 줄 수가 달라지면 거절**하는 검사를 넣었다
(의도한 경우 `line_count_change_ok`). 어긋난 번역은 대개 모양이 다르다.

```powershell
python tools/prepare_story_batch.py --batch 001
python tools/check_story_translation.py
python tools/record_story_bench.py
```

### 본편 배치를 ROM 에 넣는다 (`tools/build_story_batch.py`)

기준본(`*_menu_descriptions_v2_*`)에는 이미 **한글 11,172자 글꼴과 F9FC 핸들러**가 들어 있다.
그래서 이 단계는 **코드·글꼴·advance·VRAM 을 한 바이트도 건드리지 않는다.** 아카이브마다

1. 원본 TPL 에서 **선택한 리터럴만** 바꾼다(제어 명령·스크립트 경계·미선택 리터럴은 바이트 그대로),
2. 이 빌드가 쓰는 음절만 F9FC 항목으로 더한 표로 TextPet 컴파일,
3. **다시 추출해 문구를 대조**한다(TextPet 은 종료 0 으로 텍스트를 빠뜨린 이력이 있다),
4. LZ77 컨테이너로 감싸 ROM 끝에 4바이트 정렬로 덧붙이고,
5. **그 아카이브의 포인터 참조를 전부** 새 위치로 고쳐 쓴다(플래그 비트는 참조마다 따로 보존).

5번이 중요하다. 아카이브 12 는 참조가 **5곳**인데 처음엔 단일 참조만 받도록 만들어서 빌드가
거절했다. 하나라도 남기면 그 경로만 일본어 사본을 읽어 **화면마다 글자가 달라진다.**

`tools/verify_story_batch.py`는 빌드의 기록이 아니라 **제품 ROM 에서 아카이브를 다시 꺼내**
해제·재추출해 대조한다: 선택 리터럴은 배치 문구 그대로, **미선택 리터럴은 원문 보존**,
참조들이 **모두 같은 곳**을 가리키는지, 기준본과의 차분이 포인터 워드와 덧붙인 구간뿐인지,
한글 글꼴·advance 구간이 그대로인지.

TPL 편집에는 개행 함정이 있다. 파일은 CRLF 인데 파이썬 텍스트 모드가 다시 변환해
삽입한 줄바꿈이 **CR CR LF** 가 되고 TextPet 이 파싱을 거절한다 — 읽기·쓰기 모두 변환을 끈다.

### 조판 예산은 레코드 단위다

처음엔 "다른 창" 7개 아카이브에 아카이브 단위 예산을 줬는데 그건 틀렸다. 아카이브 008 은
평범한 대사와 **447px 엔딩 크레딧 한 줄**을 같이 담는다 — 아카이브 단위로 주면 447px 짜리
대사를 허용하게 된다. 규칙을 **레코드 단위**로 바꿨다: 기본 180px, 그런데 **자기 원문 줄이
이미 180px 를 넘는 레코드**는 그 폭을 예산으로 받는다(그 줄이 그려진다는 걸 게임이 증명한다).
그렇게 23,646 레코드가 180px, 112 레코드가 자기 폭을 쓰고, 예산 초과 레코드는 0 이 된다.
관측된 가장 넓은 일반 대사는 198px 라 180px 는 약 1.5자 보수적이다.

**시트는 일본어가 든 리터럴만 담는다.** ASCII 만으로 된 줄(엔딩 크레딧이 그렇다)은 빠져
있으므로 따로 판단해야 한다.

### 첫 본편 배치 4건과 실행 확인

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 001 | 3 / 4 | 오퍼레이션 배틀 메뉴의 명인 설명 | 80 |
| 002 | 12 | 내비 커스터마이저 프로그램 설명 | 46 |
| 003 | 443 | 오프닝 다음 넷토 방 아침 장면 | 8 |
| 004 | 230 | PET 획득 문구와 록맨의 첫 대사 | 3 |

아카이브 3 과 4 는 **판본마다 역할이 바뀐다** — Blue Moon 은 3 이 20스크립트 튜토리얼이고
4 가 내비커스 2스크립트 토막, Red Sun 은 반대다. 같은 문구를 양쪽 슬롯에 적용하면 두 판본이
덮인다. 게이트 0 problems, 진척 **137 / 22,919**.

채택 제품 `*_menu_descriptions_story_korean_development.gba` —
BLUE `1a1e2ae1c8140ec1a7591d40ccd9941422be9c1d84f1cc5c295631a4b0dd4bfd`,
RED `b026ddef2a77b8b9eba6e67bfadb20b9b0aabb24a9fea950a16ca8864840e8e6`.
기준본 대비 **+9,585바이트**, 차분은 포인터 9워드와 덧붙인 아카이브 5개뿐이다.

**실행 확인 (두 판본)** — 이미 검증된 콜드 경로 107단계를 그대로 재생했고 각 107/107 complete/rc0.
`tools/record_story_qa.py`는 캡처를 눈으로만 보지 않는다: **제품 ROM 안의 한글 글리프 비트맵으로
기대 줄을 렌더해 화면에서 그 잉크 패턴을 찾는다.** 잉크로 지정된 픽셀이 전부 한 색이고, 그 줄
상자 안 다른 어떤 픽셀도 그 색이 아닐 때만 일치로 친다 — 부분 출력·잘린 꼬리·비슷한 그림을
배제한다. 두 판본 각 **10개 메시지 16줄이 픽셀 단위로 일치**했고, 모든 줄이 기준선 격자
(y=108/122/136, 행간 14px)에 있으며 메시지를 여는 줄은 전부 왼쪽 여백 x=51 이다.

함정 둘. (1) 글리프 셀은 16열인데 조판 폭은 advance 다 — **공백 기록은 advance 8 뒤 14·15열에
잉크 6픽셀을 달고 있어서**, 자르지 않으면 공백이 든 줄은 하나도 안 맞는다. (2) 분할 메시지의
이어지는 리터럴은 왼쪽 여백에서 시작하지 않는다(`「PET」` 뒤에 붙는다). 여백 단언은 메시지를
여는 리터럴에만 건다.

근거는 `analysis/STORY_RUNTIME_QA.json`, `analysis/story_verification.json`,
`analysis/visual_qa/{blue_moon,red_sun}_story_room_01.png`다.
아직 **22,782 레코드가 미번역**이고, 짧은 라벨 소비자·PET 메뉴 라벨·나머지 화면은 그대로다.
완성판이나 배포용 패치가 아니다.

## 2026-09-20 후속: 본편 배치 005~011

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 005 | 8 | 록맨의 시스템 메시지(효과 종료·레일·잡음 대사·메일 2통·주회차) | 29 |
| 006 | 14 | 아빠의 내비 커스터마이저 강의 | 75 |
| 007 | 9 | 키 아이템·서브 칩 설명 | 188 (+보류 2) |
| 008 | 64 | 미스터리 데이터 결과 메시지 | 132 |
| 009 | 48 | 오퍼레이션 배틀 명령 프롬프트 | 196 |
| 010 | 301·303·305·307 | 이야기 데이터 어트랙션 4곳 | 350 |
| 011 | 10 | 같은 아이템들의 짧은 목록 표기 | 192 (+보류 2) |

진척 **1,299 / 22,919**. 제품 BLUE `30a85c2588f0e9e0d40bee004ee1ff2acda949af49dcb600cbeb13e5fb020024`,
RED `803bce766de1b893c15b690831e4b967a3e91dcf1b0bb71de833be1c07a03e19`.
아카이브 15개, 포인터 29워드, 기준본 대비 **+86,013바이트**. 실행 코드·글꼴·VRAM 변경은 없다.

### 작성 도구 두 가지

**원문 기준 작성(`by_source`)** — 아카이브 64는 132레코드가 22줄뿐이고, 48은 196레코드가
70줄뿐이다. 이런 곳은 경로마다 적는 대신 **원문 줄 → 번역**으로 쓴다. 배치 파일에는 여전히
id마다 원문과 번역이 다 실리므로 숨는 것은 없다. 경로별 지정이 항상 이긴다.

**명시적 보류(`deferred`)** — 아카이브 9와 10의 두 줄은 **뒤섞어 놓은 것이 곧 수수께끼**다
(거꾸로 읽기, 나선 읽기). 정답을 확정하지 못한 채 한국어 뒤섞기를 지어내면 풀리지 않는
수수께끼를 넣는 셈이라, 이유를 적고 원문으로 남겼다. 준비 도구는 **번역도 보류도 아닌
레코드가 하나라도 있으면 거절**한다.

### `by_source`가 조용히 틀릴 뻔한 자리

한 배치가 아카이브 301·303·305·307을 함께 덮는데, 네 아카이브가 **같은 경로
`script/18/literal/0`에 서로 다른 줄**을 담고 있었다. 처음 구현은 경로를 키로 풀어서
넷 모두에 첫 아카이브의 문장을 주었다. 결과물은 여전히 올바른 한국어이고 폭도 줄 수도
맞으므로 **게이트도 왕복 검사도 이걸 못 잡는다.** 잡은 것은 「작성한 줄이 아무 레코드에도
닿지 않으면 거절」이라는 검사 하나였다.

고친 규칙은 `prepare_story_batch.wording()`으로 떼어내고 `test_story_prepare.py`가
잠갔다 — 같은 경로의 서로 다른 원문이 각자 문장을 받는지, 그리고 **이 ROM에 실제로 그런
경로가 있는지**까지 검사한다(없어졌다면 그 시험은 더 이상 이 ROM을 설명하지 않는다).
벤치는 게이트 16건 + 해결 규칙 5건 = **21건**이다.

### 번역 규약 추가

- 아이템 획득은 **「X」획득!!** 로 통일한다. 이름이 삽입되는 자리라 한국어 주격·목적격
  조사를 고를 수 없다. 같은 이유로 「X」의 효력이 발휘됐다!!, 「X」 필요하다 처럼 조사를 피한다.
- 원문의 `・`(U+30FB)는 가나 영역이라 게이트가 미번역으로 본다. 말줄임표는 `.` 세 개,
  `L・R`은 `L/R`로 쓴다.

### 결함: 비압축 아카이브를 LZ77로 감싸 부팅이 죽었다

배치 005~011을 넣은 첫 제품은 **첫 프레임부터 화면이 검었다.** 원인은 빌더가 재배치하는
아카이브를 **전부 LZ77 컨테이너로 감싼 것**이다. 이 ROM의 793개 중 **716개는 압축,
77개는 비압축**이고, 이번에 덮은 것 중 아카이브 **8·12·48·64가 비압축**이다.
아카이브 8은 부팅 경로에서 읽히므로 헤더가 붙은 쓰레기를 받아 그대로 죽었다.

정적 검증은 전부 통과했다. 차분은 포인터와 덧붙인 구간뿐이었고 재추출한 문구도 정확했다 —
**검증기가 빌드와 같은 가정으로 LZ 해제를 했기 때문**이다(자기 가정을 확인한 셈이다).
게다가 앞선 4배치 제품에는 **아카이브 12가 이미 깨진 채** 들어가 있었는데, 그 화면을
지나가지 않는 경로라 드러나지 않았다. 이전에 기록한 실행 확인은 아카이브 443·230만
주장했으므로 그 주장 자체는 틀리지 않았지만, **제품에는 잠복 결함이 있었다.**

고친 것 셋:

1. 빌더는 원본 행의 저장 플래그를 읽어 **그대로 저장한다**(비압축은 페이로드 그대로).
2. 검증기는 **원본 행의 플래그로 되읽고**, 저장 형태가 바뀌면 거절한다.
3. `tools/boot_check.py` — 콜드 부팅 3캡처로 **화면이 단색인지**만 보는 1분짜리 검사를
   빌드 직후 정식 단계로 넣었다. 107단계 경로는 죽은 부팅을 알려 주는 데 40분이 걸린다.
   `tools/story_bisect.py`가 배치 부분집합으로 빌드해 이 검사를 돌려 범인을 좁힌다.

### 수정 후 실행 확인

저장 형태를 고친 제품 BLUE `d5dc5db911f575f722c7dba2db75517aff38f2fdfb920da015454936e2c77e20`,
RED `9ffc27648f97f85fecb4de3231d99cd6702d444a0ac3a7783ec1df106599759b`,
기준본 대비 **+83,645바이트**(LZ 컨테이너를 안 씌운 만큼 줄었다).
두 판본 부팅 검사 DRAWS, 콜드 경로 각 107/107 complete/rc0,
**11개 메시지 18줄이 ROM 글리프와 픽셀 일치**했다(배치 005의 메일 알림이 새로 포함됐다).
근거는 `analysis/STORY_RUNTIME_QA.json`, `analysis/story_boot_check.json`,
`analysis/visual_qa/{blue_moon,red_sun}_story_room_01.png`다.

```powershell
python tools/prepare_story_batch.py --batch 0NN
python tools/check_story_translation.py
python tools/build_story_batch.py
python tools/verify_story_batch.py
# 빌드 직후 1분짜리 부팅 검사. 죽은 부팅은 여기서 끝낸다.
python tools/boot_check.py --rom "<BLUE 제품>" --rom "<RED 제품>" --record analysis/story_boot_check.json
# 범인을 좁힐 때: python tools/story_bisect.py --keep 001,002,...
python tools/run_story_qa.py --key blue_moon --stage cold
python tools/run_story_qa.py --key red_sun --stage cold
# 실제 캡처를 직접 확인한 뒤 기록한다.
python tools/record_story_qa.py
python tools/record_story_bench.py
python tools/record_artifacts.py
python tools/verify_artifact_manifest.py
```

배치 012(아카이브 7, 소울 유니즌 해설과 스토리 메일 207건 + 보류 1)는 **작성과 폭 검사까지
마쳤고 준비·빌드는 다음 차례**다. 이번 라운드의 실행 증거가 11배치 제품에 귀속돼야 해서
준비 산출물은 되돌려 두었다.

## 2026-09-20 후속: 본편 배치 012~013

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 012 | 7 | 소울 유니즌 12종 해설、납치범의 도전장、스토리 메일 | 207 (+보류 1) |
| 013 | 268 | 셰로 카스티요 테마파크의 군중과 그 주변 이야기 | 180 |

진척 **1,686 / 22,919** (7.4%), 아카이브 17개. 제품
BLUE `1adedbe4abeaf36711bf5fee8be535c687c59a17d781a5f13cb8326725ef9e0b`,
RED `d7ef831d761441df941d4610f813bd5bf642d6fe015febc92e6438eecb138119`,
기준본 대비 **+117,537바이트**, 포인터 31워드. 두 판본 부팅 검사 DRAWS.

배치 013은 게이트가 180px를 넘는 줄 셋을 거절해 고쳤다. 게이트가 픽셀로 재므로
작성 단계에서 손으로 세지 않고 걸리는 것만 고치는 편이 빠르다.

### 원장 게이트 자기시험

부팅 검사를 원장 귀속에 넣었으니 그 게이트도 발화를 증명했다. `story_boot_check.json`에
「그리지 않은 제품」과 「실패한 보고서」를 하나씩 넣어 각각 rc=1
(`no passing boot check for this story product` / `story boot check did not pass`)을
확인하고 원본 해시로 복원했다. 교란할 때마다 원장을 다시 만들어야 의미 검사가
바이트/해시 검사에 가려지지 않는다.

## 2026-09-20 후속: 본편 배치 014~022와 메뉴 선택지 게이트

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 014 | 251 | 과학연구소 접수·곤충학도·메트올 연구 내비의 의뢰 | 188 |
| 015 | 278 | 아메로파 관광지의 외국인 NPC들 | 201 |
| 016 | 430 | 아메로파 필드: 언더넷 경로를 여는 오피셜、대회 스태프、풋봄 장인、넷 상인 | 218 |
| 017 | 622 | 넷배틀 동호회 노인들의 속담 퀴즈 10문제와 어깨 두드리기 | 153 |
| 018 | 226 | 아키하라 마을 사람들、예비 폴더를 주는 노파、서브 칩 상인 | 145 |
| 019 | 63 | 개발용 디버그 메뉴 — **보류**(아래 참조) | 146(작성만) |
| 020 | 76 | 록맨의 진행 안내 전부와 정크맨 사칭 사건 | 144 |
| 021 | 512 | 칩으로 빈칸을 채우는 이야기 데이터 네 편 | 137 |
| 022 | 224·225 | 아키하라 친구들과 이웃、레귤러 칩·바이러스 버스팅 설명、동호회 노인들 | 260 |

진척 **3,132 / 22,919** (13.7%), 아카이브 26개.

### 선택지는 180px를 받지 못한다

대사 게이트는 한 줄에 180px를 준다. **메뉴 선택지는 그 창을 혼자 쓰지 않는다** —
`positionOptionHorizontal` / `positionOptionVertical`이 한 행을 차지하고, 같은 행의
선택지들이 그 공간을 나눠 쓴다. 한글 음절은 12px, 가나는 11px이라
**같은 글자 수로 옮겨도 항상 넓어진다**. `아니오`(36px)가 `いいえ`(33px)를 덮어쓴
상태로 배치 010·014·015가 이미 빌드돼 있었다.

`tools/check_option_widths.py`를 새 게이트로 넣었다. 판정 기준은 렌더러 모형이 아니다:

* TextPet 플러그인은 `width`를 「텍스트 영역 오른쪽 끝에서 선택지 왼쪽 끝까지의 거리,
  한 글자 폭 단위」라고 적어 두었지만 **그 한 글자 폭이 몇 px인지는 어디에도 없다**.
  11·12·14·16px을 모두 시험했고 전부 ROM의 어떤 행에 의해 반증된다
  (가장 빡빡한 행은 아카이브 675 script 0의 126px / width 9).
* 그래서 예산은 **같은 배치 종류·같은 선언 폭에서 ROM이 실제로 그리는 가장 넓은 일본어 행**이다.
  `width`가 무슨 뜻이든 게임이 그 픽셀만큼은 그린다는 사실은 관측됐다.
  거기에 창 폭 180px을 독립된 상한으로 하나 더 건다.

측정 결과 ROM 전체 656행 중 번역된 235행, 문제 0건. 걸린 네 행은 이렇게 고쳤다:
`안 탄다!`→`안 타!`(301), `싫어요!`→`싫어!`·`깎아 줘요!`→`깎아줘!`(278),
`아니오`→`아뇨`(430 세로폭3), `돈가스카레`→`카츠카레`(76 세로폭5).

자기시험 `tools/test_option_widths.py` 9건을 `record_story_bench.py`에 묶었다
(총 30건). 그중 둘은 **게이트가 거절하는 것을 보인다**(한 음절 초과、인코딩 불가).
나머지는 이 ROM에 실제로 한 행 두 선택지가 있고(없으면 규칙이 공허하다),
행 끝이 줄바꿈을 든 리터럴에서 끊기며, 한글이 가나보다 넓다는 것을 못 박는다.

### 정답은 속담이 아니라 분기가 정한다

아카이브 622는 일본 관용구 퀴즈 10문제다. 정답은 내가 아는 속담이 아니라
**스크립트 자신의 `select` 타깃**이 정한다. TPL에서 읽어 확정했다:

| script | 선택지 | 정답 슬롯 |
|---|---|---|
| 5 | 개/돼지/고양이/말 | 3 (말) |
| 6 | 지렁이/참새/쥐/우렁이 | 1 (참새) |
| 7 | 개구리/민달팽이/도마뱀/지네 | 0 (개구리) |
| 8 | 배꼽/얼굴/가슴/머리 | 1 (얼굴) |
| 9 | 의자/모래/돌/얼음 | 2 (돌) |
| 10 | 발목/정강이/발끝/뒤꿈치 | 3 (뒤꿈치) |
| 11 | 창/검/막대기/망치 | 2 (막대기) |
| 12 | 날개/뿔/다리/허리 | 0 (날개) |
| 13 | 쥐/토끼/너구리/여우 | 3 (여우) |
| 14 | 개/고양이/원숭이/돼지 | 1 (고양이) |

기억으로 풀었다면 script 8을 `배꼽`(「へそで茶を沸かす」에 끌려)으로 틀렸을 것이다.
실제 정답은 `カオ` — 한국어 「얼굴에서 불이 난다」와 그대로 겹친다.
관용구가 겹치는 여섯은 그대로 옮기고, 겹치지 않는 넷은
**정답 슬롯이 든 낱말을 그대로 쓰는 다른 한국 속담으로 문제를 새로 썼다**
(개구리→우물 안 개구리, 돌→돌다리도 두들겨 보고 건너라,
뒤꿈치→발뒤꿈치도 못 따라간다, 고양이→고양이한테 생선 가게 맡긴다).
아카이브 76 script 128의 사칭 퀴즈도 같은 방법으로 확정했다(35점·카츠카레·세 번째는 함정).

### 포인터가 없는 아카이브 다섯

배치 019를 빌드하려다 `archive 63 has no pointer claim to follow`로 멈췄다.
전수 조사 결과 **793개 중 5개(43·44·56·57·63)가 포인터 클레임 0**이다.
빌더는 재작성한 아카이브를 ROM 끝으로 옮기고 그것을 가리키던 포인터를 다시 쓰는데,
가리키는 것이 없으면 다시 쓸 대상이 없다 — 한국어는 ROM 안에 들어가되 **아무도 읽지 않는다**.

`prepare_story_batch.py`가 이제 이 경우를 **작성 다음 단계에서 거절한다**
(`accept_unrelocatable`을 명시하지 않는 한). 원장 검증기도 게이트에 담긴 배치가
그런 아카이브를 덮지 않는지 확인한다. 배치 019는 작성·폭검사를 마친 채
`state: held`로 남겨 두었다 — 아카이브 63은 디버그 메뉴라 정상 플레이로 닿지 않는다.

### 배치 021·022 추가분

배치 021(아카이브 512)은 **플레이어가 칩으로 빈칸을 채우는 이야기** 네 편이다.
「 」 자리에 들어가는 것이 전부 칩 이름이라 **뒤에 조사를 붙일 수 없다** —
변하지 않는 `에`·`에서`·`때문에`·`목적으로`를 쓰거나 `그것을`·`그런 것이`로 문장을 다시 시작한다.
「けんえんのなか」는 한국어에도 그대로 있는 **견원지간**이다.

배치 022(아카이브 224·225)는 같은 거리의 두 시점이라 서로 겹치고,
배치 018(아카이브 226)의 폴더 노파와 서브 칩 상인도 그대로 되풀이한다.
**29줄을 `story_reuse.py`와 같은 규칙(그 원문에 한국어가 정확히 하나일 때만)으로
이미 내린 결정에서 가져왔다** — 다시 정하면 어긋난다.

## 2026-09-20 후속: 본편 배치 023~030과 사본군

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 023 | 429 | 아지나 인터넷 에리어、켄도맨 수련 규칙、정크 데이터 장수 | 130 |
| 024 | 17 | 록맨 개그 코너 — 말장난 넷、삼행시 둘、수수께끼 셋 | 168 |
| 025 | 67·70·73·75 | 아카이브 76의 사본 네 벌 | 497 |
| 026 | 302·304·306 | 배치 010이 덮은 투어 가이드 스크립트의 사본 세 벌 | 48 |
| 027 | 35·58·141~144·213·223·308·748·783 | 상점 틀、전투 중 안내、빈칸을 채운 이야기 데이터、마음의 거울 | 347 |
| 028 | 516 | 이야기 데이터 안내의 또 다른 사본 | 108 |
| 029 | 279·285 | 콜로세오 앞 군중과 아프리크 강마을 | 246 |
| 030 | 31~40·202~204·212·215·220·221·440·517 | 상점 다섯 곳의 틀、칩/버그피스 트레이더、시큐리티 큐브、뗏목 | 400 |

진척 **5,076 / 22,919** (22.1%).

### 사본군을 먼저 친다

아카이브 67·70·73·75는 **아카이브 76을 통째로 되풀이한다**. 497레코드 중
고유 줄은 112개이고 그중 107개가 배치 020에서 이미 결정돼 있어,
**새로 쓴 것은 다섯 줄**이다. 302·304·306은 배치 010의 사본이라 **새 줄이 0**,
516은 배치 021의 사본이라 다섯 줄이다.

그래서 남은 아카이브를 크기순이 아니라 **「레코드 수 ÷ 새로 써야 할 줄 수」** 순으로
훑는 절차를 도입했다. 재사용 판정은 `story_reuse.py`와 같은 규칙
— **그 원문에 한국어가 정확히 하나일 때만** — 을 쓴다. 경로로 풀면 안 되는 이유는
이미 아카이브 301/303/305/307에서 겪었다.

### 같은 원문이 넓은 자리와 좁은 자리에 함께 쓰인다

`いいえ`는 가로 배치의 넓은 행에도 있고 **세로폭 3(33px)** 자리에도 있다.
`by_source`는 원문 하나에 번역 하나이므로, **가장 좁은 자리에 맞춰 전역으로 통일**해야 한다.
`아니오`(36px)를 `아뇨`(24px)로 바꾸고 배치 001·009·010·015·016·026·027을 함께 고쳤다.
`たたかう!`도 같은 이유로 `싸워!`가 됐다.

선택지 게이트가 없었다면 이 충돌은 **아카이브 748 한 곳에서만 깨진 채** 나갔을 것이다.

### 아카이브 17: 언어유희는 옮기는 게 아니라 다시 만든다

| 원문 | 장치 | 한국어 |
|---|---|---|
| 「クチを…ねラウンダ!!」 | 狙うんだ + 바이러스명 ラウンダ | **그대로 성립** — 「노려라」 + 「라운다」 = 「노려라운다」 |
| 「デカオ」 삼행시 | で/か/お 3음절 | **그대로** — 데/카/오 |
| 「ねっと」 삼행시 | ね/つ/と 3음절 | 넷토는 **2음절**이라 성 「히카리」로 갈아타고 세 답을 히/카/리로 다시 씀 |
| やいと × おてら | 金/鐘 동음 | **종** — 절의 범종、부잣집의 종 |
| ギャグ × ソード | 「예리한 칼맛」 | 그대로 통함 |
| ロックマン × メットール | 「머리가 딱딱하다」 | 그대로 통함 |
| 「アジーナ/あじ〜なぁ」 | 지명 말장난(썰렁함이 핵심) | 아지나/아지랑이 — 넷토가 「같은 개그 반복하지 마」라고 받는 구조 유지 |

관서벤으로 말하는 개그 사부는 경상도 사투리로 옮겼다(〜기라/〜입니더/〜라예).

### 상점 다섯 곳은 말투로 갈라 둔다

아카이브 31·34·36·38·39는 **같은 상점 틀을 다섯 상인이 나눠 쓴다**.
일본어는 `いらっしゃいませ` / `いらっしゃい` / `いらっしゃいでマス!` /
`ヘヘ、ヨくキたな` / (표준) 으로 구분하는데, 한국어는 말높임과 어미로 갈랐다:
백화점 점원은 합쇼체, 노점 주인은 하게체, `〜でマス` 상인은 `〜습니당`,
수상한 상인은 늘어지는 말투, 표준 점원은 해요체.

`しゅう子`는 메일의 어머니라 **슈코**로 적었다.

## 2026-09-20 후속: 본편 배치 031~034

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 031 | 427 | 파크 에리어의 기자 넷、응원가、가고시마 관광객、셰로 카스티요 운영진 | 127 |
| 032 | 425 | 파크 에리어 내비들、포인트 수집、전뇌 소주 교환 | 119 |
| 033 | 419·423 | 파크 에리어 진입로와 내부、짝사랑 내비、전뇌 오징어 장수 | 231 |
| 034 | 18·531 | 데카오의 배틀 게시판、닥터 리갈의 소행성 브리핑 | 219 |

진척 **5,772 / 22,919** (25.2%).

### 사투리는 하나씩만 쓴다

관서벤·가고시마벤처럼 일본어가 방언으로 인물을 갈라 두는 곳이 여럿이라,
**한국어 방언을 인물마다 배정하고 겹치지 않게** 관리한다.
지금까지: 배치 024의 개그 사부 = **경상도**, 배치 031의 관광객 = **충청도**.
같은 방언을 두 인물에 쓰면 원문이 갈라 둔 것을 한국어가 도로 합쳐 버린다.

### 게시판도 대사창과 같은 폭이다

아카이브 18은 게시판(ケイジバン)이라 창이 다를 가능성을 먼저 재 봤다.
**일본어 최장 줄이 176px**로 180px 예산 안에 들어오고 `other_window` 도 전부 False라,
대사창과 같은 조판으로 다뤘다. 추출 시트의 예산이 `max(180, 최장 일본어 줄)`이므로
더 넓은 창이었다면 시트가 먼저 알려 준다.

### 아카이브 531은 본편 줄거리다

닥터 리갈이 소행성을 인공물이라 밝히고 넷토를 지명하는 장면이라,
**호칭과 말높임이 이후 전개와 맞물린다**. 리갈은 어른들에게 차갑게 격식을 차리고
넷토에게는 짐짓 부드러운 하게체를 쓴다(「넷토 군、처음 뵙겠네」).
히카리 박사는 아들에게 반말、공식 자리에서는 존대로 갈라 두었다.

## 2026-09-22 후속: 본편 배치 035~036

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 035 | 406·420 | 아키하라 인터넷 에리어、게시판 안내、전단지 배포、고장 난 프로그램과 건달 내비 | 208 |
| 036 | 409·416 | 타운 에리어의 부품 상인、전파탑、포인트 교환、아메로파 관광객 | 195 |

진척 **6,175 / 22,919** (26.9%).

### 방언 규칙 정정: 인물별이 아니라 원문 방언별

앞서 「인물마다 다른 한국어 방언」이라 적었는데, **원문 방언 하나에 한국어 방언 하나**가 맞다.
아카이브 420의 건달 내비도 관서벤을 쓰므로 배치 024의 개그 사부와 **같은 경상도**로 갔다.
인물별로 나누면 일본어가 하나로 묶어 둔 것을 한국어가 둘로 쪼개
**원문에 없는 구분을 만들어 낸다**.

현재 대응: 관서벤 → 경상도(배치 024·035), 가고시마벤 → 충청도(배치 031).

## 2026-09-22 후속: 본편 배치 037~038

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 037 | 412·415 | 타운 에리어1·3、납치 목격자、사무라이 퀴즈 마스터、경비 내비 | 197 |
| 038 | 247·248 | 전기가의 손님들、명인 견습 폴더、초음파 사건、패스워드 화면 | 198 |

진척 **6,570 / 22,919** (28.7%).

### 선택지 폭이 원작 정보를 깎는다

아카이브 412의 5지선다 퀴즈도 정답 슬롯을 `select` 타깃에서 읽어 확정했다(2/2/0/1/2).
셋은 그대로 옮겼지만(퍼스널 터미널、조몬 전기、타코야키집), 둘은 못 옮겼다.

* 나무 모양 문제: 정답 **기린**(2음절)은 살렸지만 오답 `ゾウ`가 **코끼리**(3음절=36px)라
  세로폭 3의 33px 예산을 넘는다. 오답 둘을 **사자/오리**로 갈았다.
* 히구레야 알바생 이름 문제: `ヒサコ/ナナコ/トキコ`가 한국어로 **전부 3음절**이라
  어느 것도 들어가지 않는다. 문제를 「넷토 아버지의 직업은?」으로 갈고
  정답 **학자**를 같은 슬롯 1에 두었다.

즉 **선택지 폭 상수가 미확정인 탓에 원작 정보를 버리는 번역이 생긴다**.
실기에서 선택지 행의 좌우 끝을 재면 상수가 고정되고, 이 두 문제는 되살릴 수 있다.

## 2026-09-24 후속: 본편 배치 039~040 — 30% 돌파

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 039 | 274·432 | 셰로 카스티요 층의 폭주 어트랙션과 요정 왕、언더넷 진입로와 슬라이더 장인 | 183 |
| 040 | 540·710 | 닥터 리갈의 정체 폭로와 월드 오브 다크 발동、카레 대결 | 177 |

진척 **6,930 / 22,919** (30.2%).

아카이브 540은 **본편의 전환점**이다. 리갈은 가면을 벗기 전까지 차갑게 격식을 차리고,
히카리 유이치로가 같은 하오체로 받아친다. 넷토만 반말로 남겨
**세 사람의 관계가 말높임으로 드러나게** 했다.

아카이브 710의 죽은 아내가 남편을 부르는 「おじいさん」은 **여보**로 옮겼다.
아이가 노인을 부르는 말이 아니라 아내가 남편을 부르는 말이므로 할아버지가 아니다.

## 2026-09-24 후속: 본편 배치 041~042

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 041 | 254·336 | 스타디움 대기열과 아쿠아맨 의뢰、조몬 전기 매장 캠페인 | 164 |
| 042 | 68·103 | 같은 대화의 양쪽 — 록맨이 넷토에게、넷토가 록맨에게 | 161 |

진척 **7,255 / 22,919** (31.7%).

### 같은 안내를 누가 하느냐가 어미로 갈린다

아카이브 68과 103은 **같은 진행 안내를 서로 반대 방향으로** 담고 있다.
68은 록맨이 넷토에게(〜자/〜해 줘), 103은 넷토가 록맨에게(〜한다/〜는 거다).
초상화가 없는 안내창에서는 **어미가 유일한 화자 표시**이므로 둘을 섞지 않았다.

## 2026-09-25 후속: 본편 배치 043~050

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 043 | 88·97·100·102·209·337·338·388 | 안내창 중복 묶음、셰로 카스티요 시큐리티 큐브、조몬 전기 CM송 | 329 |
| 044 | 32·206·433 | 히구레야 칩 주문 창구、파크 에리어 문 경고판、바닥 밑 장면 | 68 |
| 045 | 65·71 | 록맨이 넷토에게 주는 진행 안내(초반·토너먼트) | 142 |
| 046 | 246 | 덴산 시티 행인들의 잡담 | 74 |
| 047 | 107·181·435 | 넷토의 방(세이브·협박문)、불꽃 수수께끼、뼈 모퉁이 열쇠 찾기 | 108 |
| 048 | 111·219·382 | 히구레야 매장과 넘버 트레이더、관의 방、기상 안테나 | 86 |
| 049 | 417·786 | 타운 에리어4 소문과 습격당한 오피셜、눈밭과 횃불 비문 | 99 |
| 050 | 161·222·264·312·350·458·459·472·488·523 | HK 발화 장치 브리핑、수집 관문、예비 폴더 배포와 짧은 안내 8묶음 | 104 |

진척 **8,265 / 22,919** (36.1%).

### 중복이 많은 아카이브부터 치면 레코드가 싸진다

배치 043은 **329건을 넣는 데 새로 쓴 문장이 9개**다. 아카이브 88·97·100·102는
서로 거의 같은 안내창 묶음이고 337·338은 CM송의 마지막 한 줄만 다르다.
남은 613개 아카이브를 `레코드 수 ÷ 새 문장 수`로 세워 놓고 치니
043~046 네 배치가 613건을 덮는 동안 새로 쓴 문장은 148개뿐이었다.

이 할인은 여기서 끝난다. 배치 050 이후 남은 아카이브는 **레코드당 새 문장 0.5~0.7**로
평탄해져、앞으로는 아카이브 수가 아니라 **쓰는 분량**이 속도를 정한다.

### 머리 없는 조각은 조각으로 옮긴다

아카이브 111 스크립트 35는 `mugshotShow NumberMan` + `msgOpenQuick` 다음에
`かりです / 入力キャンセル` 두 줄만 있다. 앞머리가 이 아카이브 어디에도 없고
**이 스크립트를 부르는 곳도 없으며** 두 판본이 똑같이 갖고 있다.
없는 문장을 지어내지 않고 **보이는 꼬리의 표면 독해**로만 옮기고 배치 메모에 남겼다.

### 선택지 폭 규칙은 계속 발화 중

배치 048의 `롯트 넘버를 입력하시겠습니까?`(183px)와 내비커스 안내 네 줄(189px)은
**대사창 180px 한도에서 걸렸고** 줄을 다시 나눠 통과시켰다. 선택지 행 검사는
463행을 보고 0건 — `positionOption*`의 `width` 단위는 여전히 미상이고,
아카이브 412의 두 퀴즈가 보수적 예산 때문에 깎인 상태도 그대로다.

## 2026-09-25 후속: 본편 배치 051~056

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 051 | 74·99 | 중반부 진행 안내 양방향(록맨→넷토 / 넷토→록맨) | 156 |
| 052 | 298·571 | 전뇌 배트 퇴치 의뢰와 셰이드맨 피해、대회 납치 사건 | 154 |
| 053 | 437·590 | 5대 암흑칩 수호자 셋의 시련、팽이 장인 텐스케 | 152 |
| 054 | 403·436 | 아키하라 메인 스트리트와 내비 살해、보크탱 크로스오버 | 150 |
| 055 | 66·69·72·87·96·101·178·179·180·299·300·379·380·381 | 중복 안내 묶음·횃불 칩 추리·기상 안테나 | 456 |
| 056 | 79·114·265·295·315·528·691 | 소행성 종반、전파탑 콘솔、돔 청소 노인、두 번째 배트 문 | 162 |

진척 **9,495 / 22,919** (41.4%).

### 앞선 절의 "할인은 끝났다"는 틀렸다

직전 절에서 **"배치 050 이후 잔여는 레코드당 새 문장 0.5~0.7로 평탄해져 할인이 끝난다"**고
적었는데, 그건 **그 시점의 목록만 보고 일반화한 결론**이었다. 배치 055는
**456건을 새 문장 55개(0.12)로** 덮었다.

이유는 구조에 있다. 안내 아카이브는 **양방향 쌍과 판본별 사본으로 여러 벌** 존재하고,
한 벌을 게이트에 넣는 순간 나머지 벌의 비용이 0에 가까워진다. 즉 잔여 목록의 비율은
**고정된 성질이 아니라 직전 배치가 무엇을 덮었느냐에 따라 매번 다시 계산되는 값**이다.
그래서 **배치마다 순위를 다시 매긴다**는 절차만 지키면 되고, 남은 분량을 비율로
예측하는 문장은 쓰지 않는 게 맞다.

### 같은 제안을 세 목소리로: 아카이브 437

5대 암흑칩 수호자 셋은 **똑같은 시련 제안을 세 번** 한다. 원문은 1인칭과 어미로만
갈린다 — ワレ/そなた(고어), オレ/おマエさん(거친 반말), ワシ/おヌシ(노인).
한국어도 **그대·~노라 / 너·~다 / 자네·~일세**로 갈라 두었다. 어미를 통일하면
플레이어에게는 같은 내비가 세 번 말을 거는 것처럼 보인다.

### 작성 데이터를 스크립트에서 분리했다

배치 051(154문장)에서 Bash 힘드로큐먼트가 길이에서 깨졌다(`unexpected EOF`).
이후 배치는 한국어 표를 **`ko0NN.json` 데이터 파일**로 쓰고 작성 스크립트가 읽는다.
스크립트에는 역슬래시가 한 글자도 없고(`@`를 줄바꿈 기호로 씀), 표만 따로 검토할 수 있다.

## 2026-09-25 후속: 본편 배치 057~060

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 057 | 60·318·353·407·486·515 | 플러그아웃 거절、HP 상호 링크、아지나 사원 모금、롤 스토커 | 128 |
| 058 | 205·290·348·476 | 히구레야 창고 문·박스 라벨、종반 소행성 브리핑、메트올 마을 | 153 |
| 059 | 105·207·241·319·349·434·444·498·579·659·663·754·778 | 아키하라 공원 사물、사원코드 관문과 싸움꾼들、야이 전편 | 224 |
| 060 | 59·140·201·210·211·275·354·603 | 소나·하천 관리 시스템、요리 도장、테마파크 군중、아프리크 시험 | 179 |

진척 **10,179 / 22,919** (44.4%).

### 중복 할인은 이번엔 정말로 바닥났다

배치 055가 0.12까지 내려갔던 것과 달리, 배치 060 이후 남은 525개 아카이브는
**전부 0.70~0.76** 구간에 몰려 있다. 다만 이것도 **"지금 목록이 그렇다"**는 관찰이지
성질이 아니다 — 앞으로도 배치마다 다시 센다.

### `・`는 일본어로 분류된다

아카이브 105의 낙서 단서는 원문이 `「で・ぱ・・・・脳2」`처럼 **글자를 `・`로 가려 둔** 형태다.
한국어에 `・`(U+30FB)를 그대로 쓰면 게이트가 **`japanese left`로 막는다**.
기존 결정이 `・・・`를 `...`로 옮겨 왔으므로 같은 규칙으로 `.`을 썼고,
**가려진 글자 수와 모양은 그대로 유지**했다(`「백.화....뇌2」`). 단서를 복원해 주지 않는다.

## 2026-09-25 후속: 본편 배치 061~064

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 061 | 327·385 | 셰로 카스티요 HP 내비와 공원 내비들、풋봄 도전자와 룰 설명 | 112 |
| 062 | 139·328·384·545·701 | 해외 사건 뒤 공원、여신상 조명 내비、**듀오 대치**、아츠키 등장 | 166 |
| 063 | 138·214·233·339·438·728 | ANSA 전시、아프리크 지식 관문、메일과 롤 구출、블랙 어스 관문 | 172 |
| 064 | 104·117·340·341·722·746·781 | 언더넷 호위 경로、스타디움 라커룸、라울·명인·엔잔 3연전 | 123 |

진척 **10,752 / 22,919** (46.9%).

### 방언 원장: 세 번째 배정

`火村アツキ`는 도호쿠벤(`オラ`/`〜だ`/`〜べ`/`まんずまんず`)이라 새 방언이 필요했다.
이미 **경상도 = 관서벤 화자**(개그 사부 외), **충청도 = 가고시마 관광객**이 쓰였으므로
아츠키는 **전라도**로 배정했다.

| 한국어 방언 | 배정 | 처음 쓴 배치 |
|---|---|---|
| 경상도 | 관서벤 화자 전반 | 024 |
| 충청도 | 가고시마 관광객 | 031 |
| 전라도 | 호무라 아츠키(火村, 원문 후리가나 ほむら — 062의 「히무라」는 2026-09-26 정정) | 062 |

배치 063의 타코야키 광 둘도 관서벤이라 **경상도를 다시 썼다**. 규칙은
「인물마다 하나」가 아니라 **「일본어 방언 하나에 한국어 방언 하나」**다 —
원문이 그 둘을 서로 구분하지 않으므로 한국어도 구분하지 않는 게 맞다.

### 조사만 있는 줄은 비운다

아카이브 214/4/1은 첫 줄이 ` を`뿐이다. 앞의 명사를 엔진이 끼워 넣기 때문인데,
**한국어 조사는 받침에 따라 갈리므로 를/을 중 하나를 못 고른다**.
기존 규칙대로 조사를 버리되, 이 레코드는 조사가 줄 전체라서 **그 줄을 비웠다**.
원문도 거의 빈 줄이라 화면상 차이가 작다.

## 2026-09-25 후속: 본편 배치 065~068

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 065 | 128·217·218·408·465·672·756 | 불꽃 사물、엔잔 열쇠 찾기、해외 습격 뒤 아키하라 관문、늦잠 아침、타마코·포레포레전 | 129 |
| 066 | 132·321·477·487·711 | 아프리크 마을 사물、데카오 HP 내비와 배틀 연구회、인형 로봇 폭주、아지타전 | 125 |
| 067 | 320·322·688·770·790 | 배틀 정보 게시판、시장 연설 난입、라이카전、진실의 거울 | 132 |
| 068 | 112·286·383·697 | 덴산 시티 간판 거리、샤로 우주 센터、대불 수호자、아키하라 화재 | 136 |

진척 **11,274 / 22,919** (49.2%).

### 말버릇은 버리지 않는다

이 구간에는 **말버릇 하나로 인물을 세우는** 장면이 몰려 있었다. 전부 한국어에 남겼다.

| 원문 | 한국어 | 인물 |
|---|---|---|
| `〜ショー` | `〜쇼` (`하기 싫쇼!!`) | 샤로 주민 |
| `〜チョフ` / `〜スキー` | `〜초프` / `〜스키` | 샤로 주민(다른 사람) |
| `オレ、おまえ キライ` | `나、너 싫어` (문법을 일부러 흐림) | 포레포레 |
| `すばらシィー` | `훌륭하아안` | 시장 |

포레포레는 일본어가 **일부러 서툰 문장**이라 한국어도 매끄럽게 고치지 않았다.
샤로의 두 말버릇은 러시아풍 어미를 흉내 낸 것이라 **같은 마을 안에서 서로 섞지 않았다**.

### `・` 대신 공백

아카이브 132/2/3의 색 순서 단서 `あお・みどり・あお・ピンク`는 `・`가 게이트에서
일본어로 걸리므로 **공백으로 구분**했다(`파랑 초록 파랑 핑크`). 배치 059에서 가림 기호를
`.`로 바꾼 것과 달리, 여기서는 구분자라서 `.`을 쓰면 문장 끝처럼 읽힌다.

## 2026-09-25 후속: 이야기 데이터 퍼즐 표기 정정 + 배치 069

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 069 | 170·413·490·616·645·734 | 사자 제어 장치、타운 에리어3 길 내비들、악령 내비、**정크맨 대치** | 120 |

진척 **11,394 / 22,919** (49.7%).

### 퍼즐 빈칸의 정답과 다음 장의 서술이 다른 이름을 쓰고 있었다

보크탱 이야기 퍼즐(아카이브 512)은 서술 사이 빈칸에 **플레이어가 고른 이야기 데이터의
이름을 끼워 넣는다**(`printStoryDataOption`). 2장 빈칸의 틀은
「장고는 태양의 정령 「___」 그를 만나」이고 정답은 `おてんこさま`, 미끼는 `おこんてさま`다.

배치 007이 이 둘을 **「해님」/「달님」**으로 옮겼는데, 바로 다음 3장 서술(배치 021·027·028)과
다른 장면(024)은 같은 정령을 전부 **「오텐코 님」**이라 불렀다. 한 인물이 한 장 사이에 이름이 바뀐다.

원문 미끼 `おこんてさま`는 **て↔こ를 뒤바꾼 말장난**이다. 그래서 정답 「오텐코 님」、
미끼 **「오코텐 님」**(텐↔코)으로 고쳤다 — 서술과도 맞고, 퍼즐이 기대는 뒤바꿈도 그대로 산다.
같이 찾은 `ドラッキー` 표기(「드래키」 3곳 / 「드락키」 36곳)는 「드락키」로 통일했다.

**남는 것:** 빈칸에 실제로 끼워지는 아이템 이름(`おてんこさま`·`太陽の光`·`月の光`·`おこんてさま`)은
아카이브 16·62의 **짧은 라벨(short) 레코드**라 본편 파이프라인 밖이다. 지금 제품의 이 퍼즐 화면은
**한국어 틀 안에 일본어 아이템 이름이 끼워진다.** 짧은 라벨 작업이 따를 이름을
`translations/glossary.tsv`에 6행(exe4-term-012~017)으로 확정해 두었다.

## 2026-09-25 후속: 용어 일치 게이트 + 배치 070

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 070 | 123·245 | 셰로 카스티요 어트랙션과 **보크탱 이야기 소개판**、나나코의 몰래 알바、전기가 군중 | 138 |

진척 **11,532 / 22,919** (50.3%) — 본편 대사 절반을 넘었다.

### 대사 게이트가 못 보는 결함 부류

본편 대사 게이트는 **「같은 일본어 원문 → 한국어 하나」**를 강제한다. 그래서
**서로 다른 원문 속에 되풀이되는 같은 이름**은 한 줄도 실패하지 않은 채 갈라질 수 있다.
직전 절의 「해님/오텐코 님」이 그랬고, 용어집으로 전수 점검하자 16건이 더 나왔다.

| 원문 | 대사에서 | 용어집 | 건수 | 왜 문제인가 |
|---|---|---|---|---|
| バトルチップ | 배틀 칩 | 배틀칩 | 9 | **메뉴에 찍히는 이름**과 다르다 |
| データライブラリ | 데이터 라이브러리 | 데이터 도감 | 3 | 「PET 화면의 ○○에 등록된다」는 대사가 **메뉴에 없는 이름**을 가리킨다 |
| 太陽の光 | 태양빛 / 햇빛 | 태양의 빛 | 4 | 퍼즐 정답 아이템 「태양의 빛」이 서술에서 다른 말로 **메아리친다** |

### 규칙

`tools/check_glossary_terms.py` — 게이트된 줄의 **일본어에 용어집 원문이 있으면, 그 줄의 한국어에
용어집 한국어가 있어야 한다.** 레드선 변형(`ko_red_sun`)도 따로 본다. 상태가 provisional이어도
적용한다 — 메뉴가 이미 그 이름으로 찍히고 있으면 대사는 그것을 따라야 하기 때문이다.

**용어를 포함하지만 그 용어가 아닌 긴 단어**만 이유를 달아 제외한다. 지금은 하나뿐이다:
`アメロッパン`(빵 이름 「아메로팡」)은 `アメロッパ`(대륙)가 아니다. 이 규칙으로 아메로파 120건이
오탐 없이 통과한다.

**발화 증명:** 정정 전 상태에 돌려 **종료 코드 1·16건 거절**을 먼저 확인한 뒤 정정했다.
테스트 5건 — 실제로 있었던 「해님」 드리프트를 되돌려 넣으면 거절하는지, 레드선 변형만 틀려도
거절하는지, 긴 단어 제외가 맞는지, 이 규칙이 만들어진 용어들(오텐코·드락키·데이터 도감·배틀칩·
태양의 빛)을 **실제로 검사하는지**(아니면 아무것도 안 보고 통과할 수 있다). 벤치는 30 → 35케이스.
원장 검증기에도 묶었다: 보고서 PASS, 1,000건 이상 검사, 용어집 해시, 대사 게이트와 같은 배치 집합.

**한계:** 용어집에 없는 이름은 여전히 못 본다. 용어집은 17행이다 — 배치마다 `TERMS`로 적어 온
결정들을 용어집으로 옮기면 이 게이트의 범위가 그만큼 넓어진다.

## 2026-09-26 후속: 배치 071~074, 한 글자 연출, 빈 리터럴, 후리가나 이름

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 071 | 115·260·330·564·586·681 | 토너먼트 회장 안내판、히노의 분실물、가게 프로그램의 냉장고 흥정、**데카오전**(치사오를 구해 늦게 도착)、**테루오전** 입장、해제 비디오 재생 | 137 |
| 072 | 270·343·377·378·655 | 경기 전 메일과 야이토、**메일전**、가위바위보 프로그램·기합 프로그램·에코 과격파 내비、아이스크림 장수 | 146 |
| 073 | 587·656 | 테루오의 패배와 할아버지의 의절、메일전 뒤풀이(「그 누구 씨」) | 117 |
| 074 | 696·723 | 히노켄과 아츠키의 신경전、라울전 뒤 장로의 고백과 부족 계승 | 127 |

진척 **12,059 / 22,919** (52.6%).

### 한 글자씩 보여 주는 연출은 조각을 공유한다

`だ・ け・ ど、`처럼 한 단어를 조각마다 따로 리터럴로 찍고 사이사이 멈추는 연출이 있다.
대사 게이트는 원문 하나에 한국어 하나를 강제하는데, 조각이 짧아서 **다른 단어에도 그대로 나온다.**
배치 072의 `だ・け・ど、`를 쓰려다 걸렸다 — `だ・`는 だけど·だから·だれかさん 세 단어를 연다.
한 곳을 보고 정하면 나머지가 깨진다. 실제로 배치 033이 `イ・`를 「하.」(기.대.하.)로 정해 둬서,
그대로 두면 아이스크림 장수의 「아.이.스.크.리.임」이 「아.하.스…」가 될 참이었다.

`tools/survey_glyph_reveals.py`로 게임 전체를 셌다(점만 있는 쉼 줄은 제외): **연출 15개, 공유 조각 7개**.
보고서는 `analysis/story_glyph_reveals.json`.

| 공유 조각 | 들어가는 단어 |
|---|---|
| `だ・` | だけど(270) / だから(587) / だれかさん(656) |
| `か・` | だから / だれかさん |
| `れ・` | だれかさん / それに(723) |
| `イ・` | アイスクリーム(377·378) / キタイ(419) |
| `ス・` | アイスクリーム / ヨロシク(696) |
| `イ`·`ン` | 343의 ポイント 두 번(같은 단어라 충돌 없음) |

**설계:** 공유 조각은 **그 조각이 여는 모든 단어가 같은 음절로 시작할 수 있을 때만** 음절을 싣는다
(`だ・` = 「그.」 — 그.래.도 / 그.러.니.까 / 그.누.구.씨). 나머지 공유 조각은 **쉼표 점(`.`)만** 남기고
음절은 공유되지 않는 이웃 조각으로 옮긴다. 원문 조각도 전부 `・`로 끝나므로 점 자체는 원래 구조다.

| 연출 | 한국어 읽기 |
|---|---|
| 270 だ・け・ど、 | 그.래.도、 |
| 587 だ・か・ら | 그..러.니.까 |
| 656 だ・れ・か・さ・ん | 그...누.구.씨 |
| 723 そ・れ・に、 | 그.리..고、 |
| 377·378 ア・イ・ス・ク・リー・ム~ | 아.이...스.크.리.임~ |
| 419 キ・タ・イ・してるわよー! | 기.대..하고 있을게~! (배치 033 정정) |
| 696 ヨ・ロ・ス・ク! | 잘.부..탁혀! |
| 655 ぜ・ん・りょ・く・で、 | 전.력.을.다.해서、 |

### 빈 리터럴은 빌드 전체를 멈춘다

처음 설계는 공유 조각을 **빈 문자열**(소리 없는 한 박자)로 두는 것이었다. 게이트 셋은 통과했지만
TextPet이 `""`를 파싱하지 못해 **컴파일이 통째로 멈췄다**(`790FC8.tpl: Parse error on line 15`).
예전에 비운 214/4/1은 여러 줄 중 한 줄만 비운 경우라 문제가 없었다.

대사 게이트에 **빈 리터럴 거절** 규칙을 넣었다(`ko` 또는 `ko_red_sun`이 `""`). 정정 전 데이터에 먼저 돌려
**종료 코드 1·정확히 10건 거절**을 확인한 뒤 공유 조각을 「.」로 바꿨다. 시험 1건 추가, 벤치 35 → 36.

### 게임이 후리가나로 읽기를 준 이름

696/9/0은 `火村(ほむら)アツキ`라고 **읽기를 직접 찍는다.** 배치 062는 이를 「히무라」로 읽었다 —
오독이다. 「호무라 아츠키」로 정정했다(2줄, 방언 표도 정정).

원문 전체에서 후리가나가 달린 이름은 **여덟**이다: `電気街(でんきがい)`·`上文(じょうもん)`·`匠転助(たくみ・てんすけ)`·
`城戸舟子(きど しゅうこ)`·`五十嵐ラン(いがらし らん)`·`白泉(しらいずみ)`·`火村(ほむら)`·`山川味太(やまかわ あじた)`.
(처음 조사는 괄호 안의 `・`·공백을 허용하지 않는 정규식이라 넷만 셌다 — 다음 배치 준비 중에 `匠転助`를 보고 다시 셌다.)
여덟 다 용어집(exe4-term-018~025)에 넣어 용어 게이트가 지키게 했다. 기존 번역 중 읽기가 틀린 것은 `火村` 하나였다.
정정 전 표기로 되돌린 사본을 넣으면 **종료 코드 1·2건 거절**한다.

### 그 밖

* 가위바위보 선택지 343/11/4 「바위!!!」(57px)가 같은 자리 일본어 최대 폭 55px를 넘어
  선택지 폭 게이트에 걸렸다 → 「바위!!」.
* 치사오의 아기 말투(す→ちゅ)는 한국어 아기 말투 「~쪄」로 옮겼다(564/10/0 「형아! 걱정 끼쳐서 미안해쪄!」).
  이후 치사오 대사가 따를 규칙이다.
* 거츠맨 「~다 가스」, 테루오 「싯싯싯/시시시」, 기합 프로그램의 `〜ッス`는 「~슴다/~임다」.
* 심판 선언 `デリーート!!`는 모든 배치가 쓴 「삭제」로(「스파크맨、삭제---!!」).
* 071~074 작성 기록의 날짜가 작성 틀에 박힌 전날(09-25)로 찍혀 바로잡았고, 틀은 이제 실행일을 넣는다.
* **남은 문제:** 681/2/0 `りょうかい!`는 이미 정해진 「알겠습니다!」로 재사용됐는데 록맨→넷토 말높이에
  맞지 않는다. 같은 원문을 화자마다 다르게 옮길 방법이 생기기 전까지 남는 항목이다.

### 빌드와 확인

제품 BLUE `731cb243bf840ca5ccbd773c24de3ebd7b2a4e79b316c8ab507b1d5c4029bb76`,
RED `2b2ea9d843574742d620bf80ebf3daa9d5375b73ef47abdfc80730c821369c86`,
포인터 277워드, 기준본 대비 **+928,593바이트**. 게이트 셋 PASS(대사 12,059 / 선택지 538줄 / 용어 1,903회),
벤치 36케이스. 정적 검증 두 판본 PASS — 판본마다 12,019건(공통 11,979 + 그 판본 전용 40;
아카이브 3·4의 튜토리얼 슬롯이 판본마다 바뀐다). 부팅 검사 두 판본 DRAWS.
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(`analysis/STORY_RUNTIME_QA.json`, 캡처는 직접 확인). 이번 배치들의 대사는 콜드 경로(도입부) 밖이라
화면으로는 아직 못 봤다 — 정적 검증(역컴파일 대조)까지가 이 대사들의 증거다.

## 2026-09-26 후속 2: 배치 075~078, りょうかい 말높이, 후리가나 이름 재조사

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 075 | 234·281·342·344·471·580·582·638·675 | 롤이 끌려가기 전후의 메일、덴산/시티 우승 시상식、계획이 무너진 뒤의 히노켄、히구레전 입장、조몬 전기 광고 메일、기합 프로그램 사본、무술 사범 프로그램 | 145 |
| 076 | 494·595·617·618·670 | 인형 로봇 속 셰이드맨과 다크 칩、타쿠미·유코전 입장、내비 유령 소동 뒤 유코의 아빠、기합 사범 | 123 |
| 077 | 109·113·116·647·755 | 데카오 방·조몬 전기·덴산 돔 조사문、리키전 입장、미즈가미의 물 | 115 |
| 078 | 108·292·454·589·694·789 | 메일 방 조사문、리갈의 정체 뒤 소행성 위기、내비를 먹는 셰이드맨、타쿠미와 손자의 팽이、사로마전 입장、진실의 거울 | 126 |

진척 **12,568 / 22,919** (54.8%).

### `りょうかい!`는 록맨의 대답이다

원문 3종(`りょうかい!`·`りょうかい!!`·`りょうかい`)이 44곳에 나온다. 보이는 문맥은 전부 넷토의 지시에
록맨이 답하는 자리다(「록맨! 사이버 불경을!」→、「서둘러 플러그아웃이다!!」→ …). 그런데 `りょうかい!`만
처음 정한 「알겠습니다!」가 계속 재사용돼 **록맨이 넷토에게 존댓말**을 하고 있었다.
`りょうかい!!`=「알겠어!!」、`りょうかい`=「알겠어」에 맞춰 「알겠어!」로 7개 배치(023·034·044·050·059·069·071)를
정정했다.

같은 부류(짧은 공용 대사가 한 화자의 말투로 정해져 전부 재사용되는 것)를 전수로 훑었다: 여러 아카이브에 나오는
짧은 원문 중 한국어 어미가 말높이를 강하게 드러내는 것은 다섯. 원문 자체가 존댓말인 셋(`ノりますか?`·
`まちがっています`·`そうですか・・・`)은 맞고, `いらない`→「됐어요」는 플레이어 선택지라 둔다.
`どうする?`→「어쩔 텐가?」(반말 상인 1곳 + 인형 내비 2곳)는 다음 배치에서 고친다.

### 후리가나 이름 재조사

앞 절의 후리가나 조사는 괄호 안의 `・`·공백을 허용하지 않는 정규식이라 넷만 셌다. 배치 078을 준비하다
589/14/2의 `匠転助(たくみ・てんすけ)`를 보고 다시 세니 **여덟**이었다(앞 절 서술은 정정했다).
추가된 넷(匠転助·城戸舟子·五十嵐ラン·山川味太)은 기존 번역이 이미 읽기를 따르고 있었고, 용어집 022~025로 넣었다.
같은 김에 `ドクター・リーガル`를 「리걸」로 쓸 뻔해서, 034·040이 쓴 「닥터 리갈」을 용어집 026으로 넣었다.
용어 게이트는 이제 **26개 용어, 2,007회 사용**을 본다 — 배치마다 `TERMS`로 적어 온 결정을 용어집으로 옮기는
방향의 첫 걸음이다.

### 빌드와 확인

제품 BLUE `545d7eebe15060cc48e632069a0dce8bdb4f50b5ad912349cddad9f0364ae205`,
RED `67b0c5a11c64aa77655122d9edd8b9883619ee7936790b1b7d1ac047dafb0ff6`,
포인터 303워드, 기준본 대비 **+965,169바이트**. 게이트 셋 PASS(대사 12,568 / 선택지 539줄 / 용어 2,007회),
벤치 36케이스. 정적 검증 두 판본 PASS(판본당 12,528). 부팅 검사 두 판본 DRAWS.
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속: 배치 079~082, どうする? 말높이

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 079 | 266·324·333·506 | 셰로 카스티요 입구의 군중과 폴더 인형、야이토 HP의 프로그램들、불 피우는 프로그램 | 123 |
| 080 | 267·323·325·334·335 | 토너먼트 동안의 야이토 HP 방문객、대회 뒤 셰로 카스티요의 군중과 임시 휴업 | 154 |
| 081 | 326·405·489·578·588·629·685 | 토너먼트에서 전 세계 네트워크 분단까지의 넷 에리어 프로그램들、HK 발화 장치 시큐리티、탭맨·간테츠·우드맨전 앞 | 131 |
| 082 | 235·332·519·520·705 | 레드선/블루문 초대와 출발、여행 전후의 메일、카레 도전과 쿠킹 마스터의 메일、샤로 HP의 내비들 | 127 |

진척 **13,103 / 22,919** (57.2%). 079의 결정이 323·325·267과 줄을 공유해 080은 154건 중 40줄을 재사용했다.

### `どうする?`도 한 화자의 말투로 정해져 있었다

앞 절의 전수 훑기에서 남은 하나다. `どうする?`는 세 곳뿐인데(배치 032의 반말 교환 상인 1곳 + 셰로 카스티요
폴더 인형 2곳) 처음 정한 「어쩔 텐가?」(고어체)가 셋 모두에 재사용될 참이었다. 셋 다 반말이므로
「어떡할래?」로 배치 032를 정정했다.

### 빌드와 확인

제품 BLUE `d94d808679df2bf35ea74adea3ea9dc4dd04d0e7b1cf2731c9768d73352c3a99`,
RED `ad8c71aab03dd95ca1a20639eb6768cd6ed379ba830871fe009efb7a181f2d32`,
포인터 324워드, 기준본 대비 **+1,009,105바이트**. 게이트 셋 PASS(대사 13,103 / 선택지 545줄 / 용어 2,065회),
벤치 36케이스. 정적 검증 두 판본 PASS(판본당 13,063). 부팅 검사 두 판본 DRAWS.
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 2: 배치 083~086

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 083 | 110·698·709·791 | 야이토 방 조사문、불이 잦아든 뒤、카레 대결 개막、**보크탱 결전**(장고·오텐코 님·셰이드맨) | 134 |
| 084 | 83·231·258·345·346·666·739 | 인형 로봇 폭주 중 넷토의 지시、붙잡힌 엄마、대회 뒤 덴산 군중(관서벤 아주머니)、폭주 팽이、**취한 란전** 입장、명인 불참 | 123 |
| 085 | 84·347·356·422·591·665·767 | 롤의 술래잡기 도전、타쿠미와 팽이、경기 전 긴장한 란、라이카와 샤로군、언더넷 관문 | 122 |
| 086 | 119·357·421·605·610·689·787 | 테마파크 역 조사문、술꾼 사범 프로그램、폰타전 앞、성불하는 내비 유령、우드맨을 잃은 사로마、**다크 소울을 깨우는 석상** | 131 |

진척 **13,613 / 22,919** (59.4%).

* 보크탱 결전(791)은 용어집이 정한 그대로 옮겼다 — `太陽の光`=「태양의 빛」、`おてんこさま`=「오텐코 님」、`ジャンゴ`=「장고」.
  용어 게이트가 이 줄들도 검사한다. 보크탱의 경구 `あすも また日はのぼる!`는 「내일도 해는 다시 뜬다!」.
* 란(666)은 정화한 물 대신 술을 들고 나와 취한 채 등장한다 — 혀 꼬인 어미(「~다아」「~구우」)로 옮겼다.
  취하기 전의 란(665)은 원문대로 공손하다.
* 관서벤 아주머니(258)는 방언 원장(관서벤=경상도)을 따른다: 「~데이」「~기라」「억수로」「아지매」.

### 빌드와 확인

제품 BLUE `e4f6eb67ff19215ad89eb80422c8a63c100580a8d2e455970664c26e902a6229`,
RED `ce4e9d66e9c35d5662f290c7acde047a89dd97a517f5b34cc480a17ba73b4ef3`,
포인터 349워드, 기준본 대비 **+1,049,095바이트**. 게이트 셋 PASS(대사 13,613 / 선택지 551줄 / 용어 2,140회),
벤치 36케이스. 정적 검증 두 판본 PASS(판본당 13,573). 부팅 검사 두 판본 DRAWS.
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 3: 배치 087~090, 에리어 번호 띄어쓰기, 「차단」

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 087 | 542·555·737 | 워프 홀 앞 레이저맨、소행성 뒤 **리갈의 최후**、켄도맨 사범 | 122 |
| 088 | 479·493·683·784 | 파크 에리어 관문 경비、어두운 언더넷 에리어、**나르시 히데전**、버려진 내비들의 원념 | 116 |
| 089 | 250·468·602·606·676 | 넷배틀 협회 회장과 외국인 관광객、대진 발표、오해한 아쿠아맨、유코와의 첫 만남、바위 깨기 수련 | 128 |
| 090 | 269·461·495·613·620 | 대회 뒤 셰로 카스티요의 탈인형들、**셰이드맨의 최후와 다크 칩 사용**、성불하는 내비 유령、물에 잠긴 인터넷 | 130 |

진척 **14,109 / 22,919** (61.6%).

### 두 부류 정정

**에리어 번호 띄어쓰기.** 일본어 원문은 늘 `エリア3`처럼 붙여 쓰고 한국어도 「에리어3」이 86줄로 다수인데,
8개 배치(007·011·012·013·014·047·049·082)의 22개 원문 줄이 「에리어 3」으로 띄어 써 있었다. 붙여 쓰기로
통일했고(남은 띄어쓰기 0), 작성 틀이 이제 「에리어 N」을 거절한다.

**`ぶんだん`은 「차단」.** 네트워크가 끊기는 `ぶんだん`을 14줄은 「차단」, 9줄(015·058·065·081)은 「분단」으로
옮겨 갈라져 있었다. 한국어의 「분단」은 나라가 갈라진 느낌이라 「차단」으로 통일하고, 용어집에
`ぶんだん`·`ブンダン`(exe4-term-027·028)을 넣었다(원문에 한자 `分断`은 없다). 정정 전 사본에 용어 게이트를
돌리면 **종료 코드 1·정확히 9건 거절**한다.

### 빌드와 확인

제품 BLUE `7c5b610be86cdc5cd01a80cf3f58ad88ea1729ea26279e1c7256330c220d4bfc`,
RED `2f491ea7088ae21220c31a29572c3a1230080be2015acfe98177172bb36ac29c`,
포인터 375워드, 기준본 대비 **+1,081,647바이트**. 게이트 셋 PASS(대사 14,109 / 선택지 551줄 / 용어 28개 2,213회),
벤치 36케이스. 정적 검증 두 판본 PASS(판본당 14,069). 부팅 검사 두 판본 DRAWS — 세 번째 캡처의 색 수가
지난 빌드들(블루 118·레드 100)과 달리 124·95로 나왔는데, 두 빌드의 캡처가 같은 타이틀 페이드인 화면이라
캡처 순간의 밝기 차이로 판단했다(내용 변화 아님).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 4: 배치 091~094, 「로트 넘버」

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 091 | 80·216·243·731 | 넷 속 넷토의 지시들、엔잔의 열쇠 안내、히구레야 가게 대화(대회 기간 내내)、쓰레기장 기습 | 126 |
| 092 | 81·82·244·447·526 | 세계 대회 동안의 나나코、고장 난 가스레인지 프로그램과 아침밥、대회 입구의 「진실의 입」 석상 | 110 |
| 093 | 242·446·556·633 | 나나코 채용과 가게 보기、전단지 알바와 경쟁 가게、**엔딩 시상식** | 126 |
| 094 | 502·513·657·671 | 이글/호크 우승 시상식과 네뷸라의 습격、란·윈드맨과의 첫 만남、타마코와 메탈맨 | 119 |

진척 **14,590 / 22,919** (63.7%).

* **「로트 넘버」.** `ロットナンバー`가 048·054·064에서는 「롯트 넘버」(5줄), 086에서는 「로트 넘버」였다. 표준 외래어 표기
  「로트」로 통일하고 용어집 exe4-term-029로 넣었다. 정정 전 사본은 용어 게이트가 **종료 코드 1·7건**(원문 5줄=레코드 7개)으로 거절한다.
* 조회 중 배치 037의 퀴즈(아카이브 412)에서 「히구레야 알바생 이름은?」이 「넷토 아버지의 직업은?」으로 바뀐 것을 봤다.
  배치 037 NOTES에 이유(세로 3칸 선택지에 한국어 세 음절 이름이 안 들어감, 정답 슬롯 유지)가 적힌 의도적 개작이라 유지한다.
* 끼운 이름 뒤의 `の`는 받침에 따라 바뀌지 않는 「의」라 그대로 쓴다(배치 005·016의 전례).
* 엔딩(556)의 리갈 인용은 배치 087의 표현 그대로다(「악」은 결코 사라지지 않는다).

### 빌드와 확인

제품 BLUE `2d214188b9caf36004bb1d40b7d8a3e7f6f790086569e85b2b1fd2ffbbf0215c`,
RED `370a896c997ff17a4de9d3f517eda3600c83333b97d1675aa8b5837687a701a6`,
포인터 392워드, 기준본 대비 **+1,117,903바이트**. 게이트 셋 PASS(대사 14,590 / 선택지 565줄 / 용어 29개 2,299회),
벤치 36케이스. 정적 검증 두 판본 PASS(판본당 14,550). 부팅 검사 두 판본 DRAWS(색 수 118·100 — 직전 빌드의 124·95는
타이밍 차이였다는 판단과 부합).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 5: 배치 095~098, 「성불」

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 095 | 729·762·773 | 풋봄 재건을 꿈꾸던 선수의 방송 출연 제의、안테나 복구와 콜드맨의 도발、다크 소울에 씐 블루스와 엔잔 | 125 |
| 096 | 239·424·643 | 이야기 내내의 야이토、레이저맨 부하와 사랑에 빠진 내비 소동、크래셔를 노리는 마피아 내비들 | 119 |
| 097 | 428·455·619 | 파크 에리어 경비 프로그램(폭발 전후)、롤을 데려가는 셰이드맨、시합 뒤 작별하는 유코 | 123 |
| 098 | 227·283 | 히카리 집의 아빠·엄마(고장 난 전자레인지부터 결승까지)、내비 유령을 부탁하는 유코 아빠、아지나 사원·유적과 제인의 예언 | 121 |

진척 **15,078 / 22,919** (65.8%).

* **「성불」.** `じょうぶつ`(成仏)를 배치 042·045는 「승천」, 069는 가타카나 `ジョウブツ`까지 「승천」으로 옮겼고,
  086·097은 「성불」이었다. 이 장은 사이버 불경·대불로 유령 내비를 달래는 이야기라 「성불」로 통일하고
  용어집 exe4-term-030(じょうぶつ)·031(ジョウブツ)로 넣었다. 정정 전 사본 셋은 용어 게이트가 모두 **종료 코드 1**로
  거절한다(042 1건·045 2건·069 1건 = 레코드 4개, 원문 2줄).
* 파크 에리어 경비 프로그램(428)은 일본어로 모든 문장을 가타카나로 쓴다. 한국어엔 대응하는 둘째 문자가 없어
  딱딱한 존댓말(~요)과 반복되는 의성어(빤히빤히、물끄러미、힐끔)로 옮겼다. 아지나 사람들(283)의 가타카나 어미(カ·ヨ·ネ)는
  배치 015의 전례대로 평범한 한국어로 둔다.
* 455/2/0 `うっ、グググ`는 거츠맨의 신음이라 웃음처럼 읽히는 「크크크」 대신 「으윽、끄으으」로 썼다.
* 끼운 아이템 이름 뒤의 `」は`·`」を`는 조사 없이 줄을 넘긴다(배치 008·045의 전례, 227/9/1·10/1·10/5).

### 빌드와 확인

제품 BLUE `7996ca87d118af327678e1cee7a59d8f67e803890fe120a87338df4f633b7e53`,
RED `25bab7a2c2944c4bbd5ac148abe28ddbe9d8fc84e49ee3925186ad2f94d2b41f`,
포인터 403워드, 기준본 대비 **+1,155,123바이트**. 게이트 셋 PASS(대사 15,078 / 선택지 567줄 / 용어 31개 2,353회),
벤치 36케이스. 정적 검증 두 판본 PASS(판본당 15,038). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 6: 배치 099~102, 「코오리스키」

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 099 | 460·687·738 | 셰이드맨의 어둠의 노이즈와 롤 구출、과격해진 자연 보호 단체와 사로마、켄도맨에게 보이는 면허증 세 장 | 124 |
| 100 | 89·453·497 | 플러그인하는 곳마다 넷토의 혼잣말、덴산·시티 배틀 토너먼트 발표、일본 넷배틀 협회가 가져온 배틀러즈 포인트 | 126 |
| 101 | 280·504·585·653 | 봉쇄로 갇힌 호텔 손님들、아쿠아맨 사건 뒤 자기 안의 「악」에 흔들리는 록맨、폴더 잠금을 푸는 할아버지、구출 뒤의 롤 | 124 |
| 102 | 90·91·491·499·761 | 최면 가스에 자꾸 조는 샤로 연구원과 전뇌 스노우맨·전뇌 횃불、성의 대진 발표、인형 로봇 전화、넷 속 넷토 | 136 |

진척 **15,588 / 22,919** (68.0%).

* **「코오리스키」.** `イワン・コオリスキー`는 이번에 처음 번역했다. 「이반 코오리스키」로 정하고 용어집 exe4-term-032
  (`コオリスキー`)로 넣어, 그를 부르는 뒤 아카이브(759·763·764)도 같은 이름을 쓰게 했다. 용어집 설명에는 원문으로
  확인되는 사실(763/1/3의 선수, 761/1/0의 기상 위성 교란)만 적었다.
* 배치 100의 결정이 아카이브 90·91의 공유 줄을 채워, 102는 136건 중 25줄을 재사용했다(91은 새 줄 1개).
* 738/1/0의 「めんじょう」는 원문에 글자로 적힌 인용이라 조사를 붙였다(「면허증」을). 엔진이 끼우는 이름
  (89/30·31, 585/9/2~3)은 전례대로 조사 없이 줄을 넘긴다.
* `ロールチャーム`은 앞선 번역·칩 데이터 어디에도 없어 외래어 그대로 「롤 참」. 아쿠아맨은 배치 009의 말버릇 「~삐유」를
  잇고, `コポ`는 「보글」로 옮겼다.

### 빌드와 확인

제품 BLUE `d1ba218e0f73e703f968bb0b3f43da0b7126d60d4a65bc6bc8aeafeac53746c0`,
RED `81f14837190433a84f744923d745d5a6927950c9fce12eba2bf6ffbcf78a21b2`,
포인터 418워드, 기준본 대비 **+1,194,999바이트**. 게이트 셋 PASS(대사 15,588 / 선택지 567줄 / 용어 32개 2,412회),
벤치 36케이스. 정적 검증 두 판본 PASS(판본당 15,548). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 7: 배치 103~106, 진척 70% 돌파

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 103 | 249·611·612·721·772 | 성 아랫마을 사람들(혀 짧은 아이·외국인 관광객·숨은 포인트 지급자)、악령 내비 둘、라울·선더맨의 저주 풀기 의식、블루스 기권 소식과 엔잔의 전화 | 122 |
| 104 | 238·448·496·692 | 데카오·치사오、전자레인지를 고친 뒤의 아침 식사、테마파크 사건 뒤 엔잔이 설명하는 네뷸라、폭탄 내비에게 등 돌리는 우드맨 | 125 |
| 105 | 294·466·522·525·604·631 | 작전 전의 ANSA、예선 규칙、아메로파 유괴、대회 날 아침、아쿠아맨전 뒤 슈코와 동생들、히구레의 사퇴 | 120 |
| 106 | 614·615·639·662·674 | 남은 악령 내비 둘、넘버맨전 뒤 히구레、윈드맨을 막아 달라는 란、타마코·메탈맨의 바위 깨기 승부 | 124 |

진척 **16,079 / 22,919** (70.2%).

* 유코 아빠가 말한 악령 내비 4체의 퇴치 장면(611·612·614·615)이 모두 들어갔다. `じょうぶつ` 줄은 전부
  「성불」이고 용어 게이트(exe4-term-030)가 지킨다. 사이버 불경 주문은 키보드 용어를 붙여 쓰고 배치 069의
  「카아앗!」으로 맺는다.
* 674의 선택지 세 쌍(잠깐!/좋아!, 아직!/오케이!, 잠깐/컴온!)은 첫 선택지 뒤의 공백 두 칸을 그대로 두었다.
  선택지 폭 게이트는 572줄 PASS다(이번에 5줄 늘었다). `カモン!`은 배치 105의 결정(「컴온!」)이 재사용됐다.
* 614의 관서벤 유령은 방언 원장대로 경상도 말(~끼다、~아이가、마)이다.
* 249의 아이는 `シェロ・カスティロ`를 `チェロ・カチュチロ`로 혀 짧게 말한다. 한국어도 「체로 카추치요」로 발음을 살렸다.
  외국인 관광객의 `YO`·`デース` 어미는 배치 038·029의 전례(~YO、~답니다요)를 따랐다.
* 448에서 아빠가 넷토 앞에서 엄마를 `ママ`라 부르는 줄은, 남편이 아내를 부르는 한국어로 「여보」라고 옮겼다.
* **실행 QA 명령줄 한도.** `run_story_qa.py`는 재배치 아카이브와 포인터 워드마다 `--guard`(ROM 바이트 대조)를
  명령줄에 붙여 `run_mesen_segment.py`를 부른다. 이번 빌드에서 가드가 888개(가드만 31,695자)가 되어 윈도 명령줄
  한도(32,767자)를 넘었고, 두 판본 QA가 에뮬레이터를 띄우기도 전에 `WinError 206`으로 끝났다(몇 초 만에 끝나 로그를
  열어 보고 알았다). 가드 목록을 임시 인수 파일로 넘기도록 고쳤다(`run_mesen_segment.py`는 이제 `@파일`을 읽는다).
  같은 빌드로 다시 돌려 통과했고, 가드 888개는 전부 검사되어 각 세그먼트 `result.json`에 기록된다.

### 빌드와 확인

제품 BLUE `9cab1978f70a53f1b54bace5a5afbb375bd5c222068d622c0726e9e59f885592`,
RED `4bba3013e695bd7ec15c0e7f260d2ac81e21b9652e2d22f7db82f0ca15c12e9d`,
포인터 442워드, 기준본 대비 **+1,229,675바이트**. 게이트 셋 PASS(대사 16,079 / 선택지 572줄 / 용어 32개 2,482회),
벤치 36케이스. 정적 검증 두 판본 PASS(판본당 16,039). 부팅 검사 두 판본 DRAWS(색 수 118·100).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 8: 배치 107~110, 「비운 줄」 게이트

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 107 | 228·759·771 | 대회 내내 집의 엄마와 연기 나는 컴퓨터、인터넷 냉각을 멈추는 콜드맨과 코오리스키、서치맨전 뒤 친구가 되는 라이카 | 130 |
| 108 | 414·565·581 | 아키하라 에리어에서 잘린 프로그램과 격려하는 내비들、거츠맨전 뒤 데카오·치사오(유괴 자작극 고백)、파이어맨전 뒤 히노켄과 타코야키 누나 | 118 |
| 109 | 255·284 | 덴산 돔 광장 사람들(첫 대회부터 결승까지)、아지나 대불과 제인의 예언 | 130 |
| 110 | 431·484·658·763 | 아프리크 인터넷의 동물 흉내 프로그램들、파크 관리 시스템 뒤의 록맨、배고픈 넷토、얼어붙은 샤로 대전 개막 | 121 |

진척 **16,578 / 22,919** (72.3%).

* **비운 원문 줄 게이트.** 배치 018이 `「そなえあれば うれいなし」／・・・ですよ`의 둘째 줄을 빈 줄로 두어(「유비무환」 뒤
  공백), 여덟 배치가 재사용한 레코드 9개에서 「…ですよ」가 화면에서 사라져 있었다. 화면은 멀쩡히 그려지니 눈에 띄지
  않는 결함이다. 대사 게이트에 규칙을 넣었다: 원문과 줄 수가 같을 때, 원문에 내용이 있는 줄을 한국어에서 비우면 거절한다.
  예외는 조사 한 글자뿐인 줄이다(아카이브 214의 ` を`처럼 한국어에서는 앞말에 붙는 경우). 전수 조사에서 비워진 줄은 이 두
  경우뿐이었다. 정정 전 사본 8개 배치에 게이트를 돌리면 **종료 코드 1·정확히 9건**(다른 문제 0건)으로 거절하고, 조사 줄
  예외는 통과한다(시험 2개 추가, 벤치 38케이스). 둘째 줄은 서브 칩을 나눠 주는 화자의 말투(나눠 드리죠)대로 「...이죠」로
  채웠다.
* **「미즌도」.** `ミズンド`는 배치 007·029·077의 「미즌도」를 따르고, 아직 번역하지 않은 마을 아카이브(751~757)도 같은 말을
  쓰도록 용어집 exe4-term-033에 넣었다.
* 763의 얼어붙은 사회자는 추위에 혀가 굳어 `ます`·`です`를 뭉개 말한다(입장임다、~겠슴다). 코오리스키는 샤로 말버릇
  (~초프、~코프、~쇼、~스키)을 잇는다.
* 771에서 라이카의 `トモダチにな`는 점 세 개의 한 글자 연출 뒤에 따로 나온다. 한국어도 도치된 순서(되어 줘도 괜찮다 …
  친구 말이다)로 옮겨 조각마다 그대로 읽히게 했다.

### 빌드와 확인

제품 BLUE `5a798c00983319e762920ce67d3afda76bf1c269815b70a10f4da3bd5c99e1bf`,
RED `5e72b4f9aee4e318e346d8e8761bd4aba165d67c3fa118db47661386367cb12e`,
포인터 454워드, 기준본 대비 **+1,266,915바이트**. 게이트 셋 PASS(대사 16,578 / 선택지 573줄 / 용어 33개 2,537회),
벤치 38케이스. 정적 검증 두 판본 PASS(판본당 16,538). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 9: 배치 111~114, 유괴범 수수께끼

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 111 | 546·560·717 | 듀오와의 마지막 싸움、데카오가 가져온 유괴 메일과 수수께끼、라울과 아메로 카페 | 131 |
| 112 | 124·507·596·727 | 흡혈귀 저택 전시、장고 이야기 뗏목(선택지)、탭맨 할아버지와 손자、풋봄 선수 재대결 | 107 |
| 113 | 505·538·547·594·725 | 발신기 신호가 끊긴 ANSA의 리갈、로켓을 모는 듀오、다투는 두 할아버지、진 뒤의 풋봄 선수들 | 120 |
| 114 | 456·568·664·726·753 | 전파탑의 셰이드맨、타코야키 기계、제정신을 찾은 윈드맨、최강구 도전、강이 마른 아프리크 마을 | 121 |

진척 **17,058 / 22,919** (74.4%). 배치 012의 보류 한 줄이 풀려 1건이 더해졌다.

* **유괴범 수수께끼.** 치사오 유괴범의 메일(아카이브 007, 데카오 앞에서 읽는 560)에 `きさおにひ／きんじいろ／なにいるば`
  라는 격자와 힌트 `こくごの きょうかしょ`가 있다. 배치 012는 해답이 확정되지 않았다며 격자 줄을 보류했었다. 격자를
  국어 교과서처럼 오른쪽 열부터 세로로 읽으면 「ひろばにいる おじいさんに ききな」(광장에 있는 할아버지에게 물어라)이고,
  아카이브 251에서 광장의 노인이 「파란 반다나 소년에게 전해 달라더라」며 다음 메모를 건넨다. 그래서 해답이 확정됐다.
  한국어는 같은 방식으로 읽히게 격자를 새로 짰다: `보께아있광／아물버는장／라어지할에`를 오른쪽 열부터 세로로 읽으면
  「광장에 있는 할아버지께 물어보아라」다. 정정 스크립트는 이 읽기 결과가 정답 문장과 같은지 먼저 확인한 뒤에만 쓴다.
  한국 교과서는 가로쓰기라 「국어 교과서」로는 단서가 되지 않아, 힌트를 세로쓰기로 오른쪽부터 읽는 「옛날 책」으로 바꾸고
  배치 012도 같은 결정으로 고쳤다. 메일 원본과 낭독 네 레코드가 한 결정을 쓴다.
* 507의 선택지 한 쌍(사과  /포도)은 첫 선택지 뒤의 공백 두 칸을 유지하고, 가린 과일 이름 「****」에는 어느 답이든
  맞는 「를」을 붙였다. 선택지 폭 게이트 576줄 PASS다.
* 538의 리갈은 정체를 드러내기 전이라, ANSA 사람들 앞에서 점잖은 말투를 쓴다.
* 753의 아프리크 마을은 용어집 exe4-term-033(미즌도)이 새 줄에 처음 적용된 곳이다.

### 빌드와 확인

제품 BLUE `a6792e08529a4c091d1762a4e7b9c5c71983ab88c61cbe16f7e99a311882d3eb`,
RED `92e1d906615e65ebea6ef4868d48a4891422d31d38fbd35aca60a5a922fe1b74`,
포인터 473워드, 기준본 대비 **+1,297,915바이트**. 게이트 셋 PASS(대사 17,058 / 선택지 576줄 / 용어 33개 2,595회),
벤치 38케이스. 정적 검증 두 판본 PASS(판본당 17,018). 부팅 검사 두 판본 DRAWS(색 수 124·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 10: 배치 115~118

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 115 | 680·735 | 나르시와 비디오맨의 「되감기」와 해제 비디오 세 권、시합 뒤 정크맨의 최후 | 116 |
| 116 | 559·561·562·563 | 시합 전 데카오와 치사오、보이스 체인저 범인의 전화와 숫자 데이터、전파탑 바이러스、돌아온 치사오(늦게 시작한 시합 564는 배치 071) | 101 |
| 117 | 584·686·740 | 개조된 PET의 패스워드 칸을 찾는 할아버지、아키하라를 둘러보는 사로마와 시장、파문당한 제자에게 인질을 잡힌 명인 | 125 |
| 118 | 508·601·667·673·776·777 | 뗏목 바이러스、슈코의 문、술에서 깬 란과 윈드맨、시합 중계로 여관을 선전하는 타마코、블루스를 구하려고 록맨을 빌리는 엔잔 | 122 |

진척 **17,522 / 22,919** (76.5%).

* **작성 틀의 앞선 결정 대조.** 배치 116 초안에 이미 배치 071이 번역한 아카이브 564를 넣었고, 초안의 「오야마 데카오」는
  기존 결정(「오오야마 데카오」)과도 어긋났다. 작성 틀은 초안에 적은 줄을 다른 배치의 결정과 대조하지 않아 이를 못 잡았다
  (시드가 적은 줄을 건너뛰기 때문). 564를 빼고, 작성 틀에 「다른 배치가 유일하게 정한 원문을 다르게 적으면 거절」 검사를
  넣었다. 틀린 성을 넣은 음성 대조본은 정확히 그 한 줄로 거절된다. 전 배치를 전수로 세어 보면, 같은 원문에 번역이 둘 이상인
  곳은 0건이다.
* 정크맨(735)의 가타카나 말투와 `オデ`는 배치 020처럼 「나」와 평범한 반말로 옮겼다. 나르시(680)의 연극조는
  배치 088을 따른다.
* 엔잔은 넷토를 성으로(`光`) 부른다. 한국어도 「히카리」로 부른다(776·777).

### 빌드와 확인

제품 BLUE `9b14875a2054403ad1b850c87dd315b8acc8b51bf9b58ea26881aff1bcc85fe7`,
RED `6d740eed0c2e699b861475196b8b217bce6414cf419d067de40f5b44ab92b8d5`,
포인터 488워드, 기준본 대비 **+1,328,151바이트**. 게이트 셋 PASS(대사 17,522 / 선택지 576줄 / 용어 33개 2,645회),
벤치 38케이스. 정적 검증 두 판본 PASS(판본당 17,482). 부팅 검사 두 판본 DRAWS(색 수 118·100).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 11: 배치 119~122

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 119 | 521·626·706·730·775 | 본즈와 넷토를 태워 간 차、마피아 부하들과 혼자 싸우는 크래셔、요리 도장、정크맨 소개、언더넷으로 이끄는 엔잔 | 124 |
| 120 | 86 | 넷토가 넷에서 다음 행선지를 알려 주는 안내 줄(첫 번째 묶음) | 67 |
| 121 | 95·98 | 같은 안내 줄의 나머지 두 묶음 | 130 |
| 122 | 92·404·779 | 플러그인하는 곳마다 넷토의 혼잣말、대회 내내 아키하라 에리어의 프로그램과 내비、록맨을 통해 블루스를 되찾는 엔잔 | 118 |

진척 **17,961 / 22,919** (78.4%).

* 아카이브 86·95·98은 넷토가 넷에서 「다음엔 어디로」를 말하는 안내 줄 세 묶음이다. 86(배치 120)에서 정한 문장이 95·98
  130건 중 121건을 채워, 배치 121에서 새로 옮긴 줄은 9개뿐이다(물에 잠긴 인터넷、마피아와의 결투 등).
* 626의 크래셔는 `じゃい` 같은 말투를 쓰지만 방언 원장에 대응하는 한국어 방언이 없다. 새 방언을 배정하지 않고 거친
  표준어로 옮겼다.
* 521의 본즈는 배치 015처럼 어색한 존댓말(~했었습니까、~하겠다요)을 그대로 살렸다. `鬼に金棒`는 한국어 관용구
  「호랑이에 날개」로 옮겼다.
* 779에서 제정신을 찾은 블루스는 엔잔을 「엔잔 님」으로 부른다(`炎山さま`).

### 빌드와 확인

제품 BLUE `8d27c90600defefc45c598eb3063a2d08c2bfb8593c0e698ce05642b291c0165`,
RED `9623e1622d3981d7fa70b9c8a0cb90a184ff51653b91d0dff20efcd8cdc7a212`,
포인터 499워드, 기준본 대비 **+1,368,523바이트**. 게이트 셋 PASS(대사 17,961 / 선택지 577줄 / 용어 33개 2,765회),
벤치 38케이스. 정적 검증 두 판본 PASS(판본당 17,921). 부팅 검사 두 판본 DRAWS(색 수 124·100).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 12: 배치 123~126, 진척 80% 돌파

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 123 | 237·411·583 | 이야기 내내 집의 데카오와 치사오、넷의 순찰 프로그램들(시 짓는 프로그램 포함)、칩 폴더를 잠가 버리는 가짜 정비원 | 124 |
| 124 | 240·259·630·650·695 | 이야기 내내 야이토、돔 앞 사람들、시합 뒤 간테츠、야이토에게 연습을 부탁하는 메일、시합 뒤 사로마 | 121 |
| 125 | 93·608·764 | 플러그인하는 곳의 혼잣말、내비 유령을 설명하는 유코 아빠、얼어붙은 시합 뒤 체포되는 코오리스키 | 124 |
| 126 | 757·782·788 | 미즈가미 사건 뒤의 포레포레와 마을、시합 뒤의 엔잔과 블루스、더 깊은 어둠을 노리는 포르테 | 120 |

진척 **18,450 / 22,919** (80.5%).

* 608에는 엔진이 끼우는 아이템 이름이 둘 있다(전뇌 수정·사이버 불경). 받침에 따라 바뀌는 조사가 뒤에 붙지 않도록
  문장을 짰다: 두 이름의 목록은 「와/과」 대신 쉼표로 잇고, 수정을 가리키는 줄은 「그 [이름]만 있으면」、「[이름]의 색이」로
  옮겼다.
* `井の中の蛙`는 한국어 관용구 「우물 안 개구리」로 옮겼다(630·757). 782의 `ぐんばいが あがりました`는 배치 073의
  「승리로 끝났습니다」, 블루스의 `ハッ`은 배치 107(라이카)의 「넷」을 따른다.
* 259의 자판기 버튼 문구 「차가~운」·「따뜻~한」은 원문에 적힌 인용이라 조사를 붙였다.

### 빌드와 확인

제품 BLUE `ee8330f05ebc7cb2758a70b44f5245b9cf255cc28920c8af03b79def22ebf285`,
RED `6626a737fcd0e5052a962645932e35f6ba2a60cf652b2fcbceec433b1123ced8`,
포인터 513워드, 기준본 대비 **+1,405,987바이트**. 게이트 셋 PASS(대사 18,450 / 선택지 577줄 / 용어 33개 2,827회),
벤치 38케이스. 정적 검증 두 판본 PASS(판본당 18,410). 부팅 검사 두 판본 DRAWS(색 수 118·100).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-27 후속 13: 배치 127~130, 이름 갈림 통일, 레드선 폴백 결함

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 127 | 518·736 | 소행성을 향한 레이저 발사와 방해 공작、아프리크 대표 켄도맨의 오퍼레이터였던 명인 | 123 |
| 128 | 462·467·474·537 | 섀도맨을 쫓아내는 엔잔과 블루스、예선 통과、대회 한 주 뒤의 넷토와 메일、록맨과 함께 자폭하려는 네뷸라 내비 | 126 |
| 129 | 131·548·651·769 | 아지나의 불상들、록맨을 응원하는 세계(레드선은 히노켄)、롤이 끌려갔다는 야이토、언더넷에서 넷토를 시험하는 라이카와 서치맨 | 127 |
| 130 | 133·712·733·774 | 샤로 마을 풍경、시합 뒤 아지타、록맨 몸속의 정크맨、다크 블루스를 만드는 네뷸라 | 122 |

진척 **18,948 / 22,919** (82.7%).

### 이름 갈림 다섯 개 통일

번역 전체에서 가타카나·한자 이름마다 가장 많이 쓰인 번역어가 문장에 없는 레코드를 셌다(읽기 전용 진단).
인물 이름은 전부 일관적이었고, 갈린 것은 다섯이었다.

| 원문 | 통일 | 갈라져 있던 표기 |
|---|---|---|
| マサカリひめ·マサカリヒメ | 도끼공주 | 마사카리히메 6건(010·013·026·090) |
| ウィザーモンキー | 위저몽키 | 위저 몽키 1건(007) |
| 秋原町·アキハラチョウ | 아키하라 마을 | 아키하라초 6건·그냥 아키하라 3건(018·034·037·038·041·042·045) |
| ヌポポぞう | 누포포상 | 누포포 상 1건(007) |
| ナビカス | 내비커스 | 내비 커스텀 2건(034), 보류 중인 019 한 줄 |

용어집에 12행(exe4-term-034~045)을 더해 이 다섯과, 일관적이지만 다음 배치에 또 나오는 위저독·브리킹·셰로 카스티요·
내비 커스터마이저를 게이트에 묶었다. `ナビカス`는 `ナビカスタマイザー` 안에도 들어 있어 긴 낱말 예외에 넣었다.
**새 행을 고치기 전 번역에 걸자 정확히 19건이 FAIL**했고, 고친 뒤 45개 용어 PASS다. 「아키하라 마을」로 길어져
180px를 넘는 네 줄은 문장을 다시 짰다(각각 측정). 秋原小(학교)의 「아키하라초 6-A」는 그대로다.
퀴즈 412의 「넷토 아버지의 직업」 문제는 선택지 폭 때문에 의도적으로 바꾼 것이라(2026-09-22 기록) 이번에도 유지했다.

### 레드선 폴백 결함: 레드선에 블루문 화자가 나왔다

두 판본의 원문이 다른 레코드(differs)에 레드선 번역을 따로 쓰지 않으면 `prepare_story_batch.py`가 **블루문 번역으로
조용히 채웠다**. 아카이브 504는 레드선에서 아쿠아맨 대신 거츠맨(~でガス)이 나오는 장면인데, 배치 101 이후 레드선
개발 빌드에는 이 장면에 「아쿠아맨」 대사가 들어가 있었다(화면 확인은 아니고 빌드 입력으로 확인). 이번 배치 129의 548도 레드선은 사로마 대신 히노켄의 대사인데 같은 일이
생길 뻔했다. 게이트는 두 문구가 「있는지」만 봤고, 폭·인코딩·줄 수 검사는 블루문 문구에만 돌았다.

* 준비 단계: 레드선 문구는 경로별 문구 → **레드선 원문을 키로 한 문구** → (원문 차이가 공백뿐일 때만) 블루문 문구 순으로
  찾고, 없으면 거부한다. 항목에 `ja_red_sun`을 함께 적는다.
* 대사 게이트: 모든 검사를 레드선 문구에도, **레드선 원문 기준으로** 돌린다. 원문이 다른데 번역이 같으면 거부.
* 용어 게이트: 레드선 번역은 레드선 원문의 용어와 대조한다.
* 고치기 전 번역에 새 규칙을 걸자 게이트 62건 FAIL, 준비 단계는 101(12건)·129(15건)을 거부했다. 새 폭 검사는
  새로 쓴 레드선 문구 세 줄의 초과(184·203·188px)도 바로 잡았다.
* 504 레드선 12건은 거츠맨의 「~다 가스」로, 548 레드선 15건은 히노켄의 거친 반말로 새로 썼다(블루문 번역은 그대로).
* 게이트 시험이 38개에서 **48개**가 됐다(대사 게이트 5·준비 4·용어 1).
* 작성 틀(scratch)도 `키:red`로 레드선 문구를 받게 했고, 미번역 differs가 있는 503에서 레드선 칸 15개를 막는 것과
  이미 고친 548에서 레드선 결정 15줄을 씨앗으로 받는 것을 확인했다. 남은 differs는 43건(503·53·552·549·551·550)이다.

### 빌드와 확인

제품 BLUE `3d79ca3f2b1b4b69e6561ba6fc667d69f0b449886db51370236fb81bc1c4052e`(+1,439,891바이트),
RED `3a546dfa1291cc242a73cae82ff2df6d6bcfb3cf6ffd4bc398417653b380ed38`(+1,439,739바이트), 포인터 527워드.
두 판본 크기가 이제 다르다: 레드선 문구가 따로 생겼고, 548에 한 판본에만 있는 줄(블루문 1·레드선 2)이 있어
정적 검증 건수도 BLUE 18,906 / RED 18,907이다. 게이트 셋 PASS(대사 18,948 / 선택지 577줄 / 용어 45개 3,191회),
벤치 48케이스. 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들과 레드선 수정 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 14: 배치 131~134, 레드선 문구를 처음부터 따로 쓴 첫 배치

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 131 | 410·724 | 아키하라 넷의 노래하는 프로그램·수상한 판매상·셰로 카스티요 선전、넷토에게 도전하는 풋봄 소년 | 128 |
| 132 | 24·287 | 셰로 카스티요 게시판、토너먼트부터 소행성 위기까지의 ANSA·샤로 직원、넷토를 시험하는 샤로군 사령관 | 123 |
| 133 | 22·704 | 아메로파 호텔 게시판(지역별 인터넷 걷는 법)、아지타의 카레와 쿠킹 배틀 도전 | 115 |
| 134 | 50·503 | 첫 바이러스 버스팅 튜토리얼、록맨의 다크 소울을 끌어내는 레이저맨(블루문 아쿠아맨 / 레드선 거츠맨) | 113 |

진척 **19,427 / 22,919** (84.8%).

* 503은 두 판본의 원문이 다른 레코드가 16건이다. 어제 고친 규칙대로 레드선 문구를 **레드선 원문을 키로 따로**
  썼다(거츠맨의 「~다 가스」·「가츠」·「우가」). 준비 단계가 블루문 문구로 채우는 길은 이제 없고, 16건 모두
  레드선 원문에서 풀렸다. 남은 differs는 27건(53·552·549·551·550)이다.
* 132의 게시판은 용어집에 새로 묶은 이름(도끼공주·위저몽키·위저독·브리킹·셰로 카스티요)을 그대로 쓴다.
  `ガンデルソル`은 칩 이름 「건델솔」을 따랐다.
* 133의 칩 이름은 칩 카탈로그(블랙봄·다크홀·패널리턴), 속성은 「나무 속성」·「불 속성」을 따랐다.
  처음 나오는 바이러스 `キルブー`·`ウォーラ`는 「킬부」·「워라」로 정했고, `マルモコ`는 배치 034의 「마루모코」다.
* 134의 튜토리얼은 메뉴 말(커스텀 게이지·커스텀 화면·록버스터·칩 데이터·「A 버튼」)을 앞 배치에 맞췄다.

### 빌드와 확인

제품 BLUE `53309a4dd40c58885091bb6170c63b8ae48bffc67ece4018bca5cc8405f992a6`(+1,481,059바이트),
RED `c57749a4462391fa56a7e24d10dacf67966c6a29bca1877c8b50468854ef6658`(+1,480,859바이트), 포인터 535워드.
게이트 셋 PASS(대사 19,427 / 선택지 578줄 / 용어 45개 3,279회), 벤치 48케이스. 정적 검증 두 판본 PASS
(BLUE 19,385 / RED 19,386). 부팅 검사 두 판본 DRAWS(색 수 124·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 15: 배치 135~138, タワシ 통일

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 135 | 463·632 | 섀도맨이 떨어뜨린 다크 칩을 설명하는 히구레、히구레야를 수세미 가게로 바꾸려는 NAM 고문 콘 | 112 |
| 136 | 26·720 | 조몬 전기 게시판、록맨에게 걸린 저주와 네 증표의 시련을 알려 주는 라울 | 111 |
| 137 | 120·679 | 셰로 카스티요 어트랙션 안내와 캐릭터 이야기、승리를 양보해 달라는 비디오맨 오퍼레이터 나르시 히데 | 106 |
| 138 | 567·624 | 타코야키 가게의 자릿세 깡패를 쫓는 히노켄、어깨뼈 사기꾼을 쫓아내는 간테츠 | 101 |

진척 **19,857 / 22,919** (86.6%).

* `タワシ`는 배치 093(633)에서 「타와시야」로 음역돼 있었고, 배치 131(410)은 「고급 수세미」로 옮겼다. 632는
  콘이 「タワシ」라고 하자 넷토 쪽이 「た」「わ」「し?」로 한 글자씩 되묻는 장면이라, 한국어가 「수」「세」「미?」로
  되려면 이름이 「수세미」여야 한다. 093의 한 줄을 「수세미 가게」로 고치고 용어집에 `タワシ`·`たわし` 두 행
  (exe4-term-046·047)을 더했다. **새 행을 고치기 전 번역에 걸자 정확히 그 한 줄(633/4/1)만 FAIL**했고, 고친 뒤
  47개 용어 PASS다.
* 135의 히구레는 「~습니당/~입니당」, 나나코는 「~요오」, 콘은 외국인 말투(「~네요~」·「~습니다~」·YO)다.
  히구레가 부르는 `ナナコちゃん`은 「나나코 양」으로 정했다.
* 136의 네 증표는 721 의식의 「용기、강함、예지、상냥함」, 주문(`グレスピリ`)은 배치 103의 「그레스피리」를 따른다.
  넷토는 라울에게 배치 064·074처럼 존댓말을 쓴다.
* 137의 캐릭터 이야기는 배치 021의 동화 말투(「~습니다」)이고, 이어지는 줄의 한 칸 들여쓰기를 원문대로 지켰다.
* 138의 간테츠는 배치 119·124처럼 새 방언 없이 거친 표준어다.

### 빌드와 확인

제품 BLUE `e12aae03422ae3ccd8cb567d18d5c485e85a85e414ff5c962627dcaeedaaed7d`(+1,514,399바이트),
RED `4486a0be4da393207a2ba05fecf8bc36ffe31e1962babb3c08c50ba29f374c21`(+1,514,199바이트), 포인터 543워드.
게이트 셋 PASS(대사 19,857 / 선택지 578줄 / 용어 47개 3,344회), 벤치 48케이스. 정적 검증 두 판본 PASS
(BLUE 19,815 / RED 19,816). 부팅 검사 두 판본 DRAWS(색 수 118·100).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들과 093 수정 줄은 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 16: 배치 139~142

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 139 | 256·766 | 덴산 돔 공원 사람들(팬·청소부·연구원·오피셜)、넷토에게 선전포고하는 라이카 | 97 |
| 140 | 20·464 | 야이토 HP 잡담 게시판、레이저 작전을 가결하는 세계 과학자 회의(닥터 리갈) | 94 |
| 141 | 641·700 | 크래셔를 빼앗긴 리키와 마피아 보스(빵집의 꿈)、히노켄과 아츠키의 싸움 | 93 |
| 142 | 482·524 | 부하를 숙청하는 섀도맨과 메일의 테마파크 초대、납치가 예선이었다고 밝히는 본즈 | 88 |

진척 **20,229 / 22,919** (88.3%).

* 141의 리키는 평소엔 거칠지만 크래셔를 잃자 `〜ダス`로 운다. 한 낱말 버릇이라 방언 원장에 넣지 않고,
  히구레의 `でマス`(「~니당」)처럼 **「~다스」**로 옮겼다. 원장대로 아츠키(도호쿠벤)는 전라도(「~랑께·~당께」),
  보스 할머니는 거친 반말이다. 첫 대사의 「~쇼」는 샤로 인물의 버릇과 겹쳐 쓰지 않았다.
* 142의 본즈는 여러 방언을 섞는 말투라 배치 015처럼 「~습니다요」, 납치범은 「보이·유」(배치 015의 `ユー`)다.
  `オートでんわ`는 배치 024의 「자동 전화」, 섀도맨의 `キキッ`은 「키킷」이다.
* 140의 리갈은 배치 034처럼 하게체(「~네」), 과학자의 방백은 이어지는 줄의 한 칸 들여쓰기를 지킨다.

### 빌드와 확인

제품 BLUE `4ec947bfd89a029169fec307f52ddb9fde996ae078d153c1815f54d439c82579`(+1,544,671바이트),
RED `835ee20d6f9f2ced60578a42411c946b2095ce9779462fe37710878ade650dc5`(+1,544,471바이트), 포인터 551워드.
게이트 셋 PASS(대사 20,229 / 선택지 578줄 / 용어 47개 3,380회), 벤치 48케이스. 정적 검증 두 판본 PASS
(BLUE 20,187 / RED 20,188). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 17: 배치 143~146, 대사 속 칩 이름을 칩 폴더에 맞춤

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 143 | 426·599 | 파크 에리어의 순찰 프로그램·데이트 커플·오피셜、세탁기 얘기를 오해하고 인터넷으로 뛰쳐나간 아쿠아맨 | 87 |
| 144 | 485·758 | 넷토와 메일의 테마파크 데이트、시합 전 아메로파의 냉방을 얼리는 코오리스키 | 86 |
| 145 | 28·253 | 다크 칩 사용자들의 언더넷 게시판、전파탑 광장의 라이벌 아이들과 오피셜 | 81 |
| 146 | 669·751 | 바위로 넷토의 기합을 시험하는 타마코、아프리크 마을의 미즈가미 찾기(주아) | 80 |

진척 **20,563 / 22,919** (89.7%).

### 칩 이름은 칩 폴더의 이름으로

대사가 칩을 가리킬 때 칩 폴더(칩 카탈로그)와 다른 이름을 쓰던 곳이 31줄 있었다(읽기 전용 진단으로 셈).

* 이름 자체가 달랐다: `メットガード` 7줄이 「메트가드」인데 폴더는 **「메톨가드」** — 「메트가드1 A」와 교환하자는
  퀘스트 대사라 플레이어가 폴더에서 못 찾는다. `スイコミ`(흡입)는 「빨아들이다」, `ユカシタ`(마루밑)는 「바닥 아래」,
  `ロールアロー`는 「롤 애로우」(폴더는 롤애로)였다.
* `シェードマン`은 기존 25줄이 폴더와 같은 「셰이드맨」인데, **배치 134·135에서 새로 쓴 2줄이 「섀도맨」**으로
  갈라져 있었다(같은 실수가 있던 초안 145의 6줄도 고쳐서 넣음).
* 나머지는 띄어쓰기 차이(버블 샷↔버블샷, 와이드 소드↔와이드소드 등, 대부분 배치 012의 소울 설명).

`check_glossary_terms.py`가 이제 칩 카탈로그의 칩 이름(번호·EX 등을 뗀 기본형, 3자 이상) **181개**를 용어로 함께
검사한다(용어집에 같은 원문이 있으면 용어집 쪽). 「パトロール」 속의 `ロール`은 긴 낱말 예외로 뺐다.
**고치기 전 번역에 걸자 정확히 31건 FAIL**했고, 9개 배치(009·012·022·036·063·093·134·135·140)의 31레코드를 고친 뒤
PASS다(번역 필드만 바뀐 것을 대조로 확인). 벤치에 「메톨가드를 메트가드로 되돌리면 거절」 시험을 더해 49케이스다.

### 빌드와 확인

제품 BLUE `21d299e7dac740a654db592b286ba7b46a84c1447854f69e9fd0a55db1182de0`(+1,571,459바이트),
RED `4002d7f2d219414005f43019ca85d9a7d05dd9dc67128a57e80f572023850700`(+1,571,259바이트), 포인터 559워드.
게이트 셋 PASS(대사 20,563 / 선택지 578줄 / 용어 47개+칩 이름 181개 4,303회), 벤치 49케이스. 정적 검증 두 판본 PASS
(BLUE 20,521 / RED 20,522). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들과 칩 이름 수정 줄은 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 18: 배치 147~150, 판본이 갈리는 레코드 마무리

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 147 | 53·549·550·551·552 | 소행성 위기 때 세계 각지의 응원、소울 유니즌 튜토리얼(블루문 아쿠아 소울 / 레드선 거츠 소울) | 65 |
| 148 | 51·252·598 | 칩 코드 튜토리얼、칩 이름을 외치며 싸우는 아이들、불운을 한탄하는 슈코와 아쿠아맨 | 111 |
| 149 | 52·646·684 | 카운터와 풀 싱크로를 가르치는 아빠、배신자를 물리치고 리키를 보내 주는 보스、시합 뒤 다투는 나르시와 비디오맨 | 108 |
| 150 | 452·554·570 | 아메로파로 불려 가는 아빠、소행성 안의 결전과 심판을 보류하는 존재、타코야키 기계를 고친 히노켄 | 100 |

진척 **20,947 / 22,919** (91.4%).

* 147은 두 판본의 원문이 다른 레코드가 27건이다. 띄어쓰기만 다른 2건을 뺀 **25건의 레드선 문구를 레드선 원문
  키로 따로 썼다**(레드선은 라울의 부족·예언자·아프리크 사람들이 말하고, 샤로 응원에는 코오리스키 말버릇이
  레드선 쪽에 붙는다. 튜토리얼은 거츠 소울·크랙아웃·거츠펀치). 레드선 552의 멈춤 조각 「・」은 기존 결정 「.」을
  씨앗으로 받았다. **이것으로 판본이 갈리는 레코드는 남지 않는다.**
* 148·149의 칩 이름은 이제 용어 게이트가 칩 카탈로그와 대조한다(에리어스틸·와이드소드·발칸·흡입·리커버리 등).
  아이들이 늘여 외치는 이름(에리어스티이이일·메톨가----드)은 카탈로그 이름을 늘인 꼴로 썼다.
* 149의 `ココロウインドウ`는 「마음 윈도」, `フルシンクロ`는 배치 122의 「풀 싱크로」다.

### 빌드와 확인

제품 BLUE `56f089d2ec25855c5b695b5dc6e3b691a1713d9e4349459e4ff4818d970e4df4`(+1,597,919바이트),
RED `d49ae190b8e43e7e495d7dab388e1dffe1898c4e11f11d253faae802998f0981`(+1,597,799바이트), 포인터 575워드.
게이트 셋 PASS(대사 20,947 / 선택지 578줄 / 용어 47개+칩 이름 181개 4,410회), 벤치 49케이스. 정적 검증 두 판본 PASS
(BLUE 20,902 / RED 20,905 — 판본 전용 줄이 147에서 레드선 3·블루문 1 늘었다). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 19: 배치 151~154, 덴산 돔에서 샤로의 눈보라까지

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 151 | 257·277·592 | 덴산 돔 접수처와 관객、오즈마 감독과 로트 넘버 수수께끼、타쿠미 씨 대신 넷토를 시험하는 넷배틀 동호회 | 95 |
| 152 | 331·703·747 | 조몬 전기 넷의 흥정 할아버지、시합 앞둔 야마카와 아지타、켄도맨 시합 뒤 명인의 말 | 90 |
| 153 | 577·637·702·752 | 경기장의 HK 발화 장치、아이들이 지켜 낸 히구레야、시합 뒤 아츠키、강이 마르는 날의 미즌도 | 113 |
| 154 | 106·529·566·760 | 히카리 집、ANSA로 불려 가는 세계 챔피언、시합 앞둔 히노켄、샤로에서 온 눈보라 | 109 |

진척 **21,354 / 22,919** (93.2%).

* 151의 수수께끼(277/25)는 번호를 그대로 두었고、볼즈의 이름 `カーミラ`·`イストラカン`·`そうくうのとう`·`ぎんか`는
  여기서 처음 나와 「카밀라」·「이스트라칸」·「창공의 탑」·「은화」로 정했다. `おてんこさま`는 「오텐코 님」(exe4-term-012)、
  `ロットナンバー`는 「로트 넘버」(exe4-term-029)다.
* 152의 `味太`는 「아지타」(exe4-term-024)、성까지 부르면 「야마카와 아지타」다. `アキハラチョウ`는 「아키하라 마을」(exe4-term-041).
* 153의 발화 장치는 글자를 살려 「HK 발화 장치」로 썼다. `タワシ`는 「수세미」(exe4-term-046)、`ミズンド`는 「미즌도」(exe4-term-033)、
  아츠키는 원장대로 전라도 말씨다.
* 154의 `しゅにん`은 「주임님」(exe4-term-007)、`てんねんもの`는 배치 020의 「천연물」이다. 760/3의 인용 메일은 이어지는 줄의
  한 칸 들여쓰기를 지켰다.
* 이번 주기에는 판본이 갈리는 레코드가 없어 정적 검증 수가 두 판본 모두 407건씩 늘었다.

### 빌드와 확인

제품 BLUE `70454a2ba5c7b17390b20f5ba6f6c28f6989977c24849b94bd45cfc8f6acf44c`(+1,628,499바이트),
RED `54fe0589017921bd663455caad19ac4ed3120bb165c1ff391615443be0e58624`(+1,628,379바이트), 포인터 589워드.
게이트 셋 PASS(대사 21,354 / 선택지 578줄 / 용어 47개+칩 이름 181개 4,473회), 벤치 49케이스. 정적 검증 두 판본 PASS
(BLUE 21,309 / RED 21,312). 부팅 검사 두 판본 DRAWS(색 수 124·100).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 20: 배치 155~158, 히노켄 일당에서 우드맨의 폭탄 경비까지

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 155 | 569·628·715·732 | 히노켄과 부하들、불량배와 맞서는 싸움꾼、쿠킹 배틀 심사、록맨 행세를 하는 정크맨 | 108 |
| 156 | 449·475·625·750 | 전기가 나들이、셰로 카스티요 홍보、간테츠와 불량배、포레포레의 초대 | 101 |
| 157 | 134·644·661·708 | 샤로 우주 센터 전시、풀려난 크래셔、윈드맨 계략、쿠킹 마스터의 내비 | 93 |
| 158 | 61·130·135·553·690 | 여행 지도、아지나의 노점과 불상、ANSA 관제실、케이블이 되는 리갈、우드맨을 꾀는 폭탄범 | 109 |

진척 **21,765 / 22,919** (95.0%).

* 155의 싸움꾼과 156의 간테츠는 배치 119·124처럼 `じゃい`를 거친 표준어로 옮겼다. 732의 정크맨은 록맨 몸으로
  말하다 거친 말투가 새고 바로잡는다. 끊겨 들리는 732/0·1의 부름은 원문이 이름을 끊는 자리에서 「록맨」「넷토야」를 끊었다.
* 156의 `電気街`는 「전기가」(exe4-term-020)라 괄호 속 읽기 표시는 뺐고、`秋原町`은 「아키하라 마을」(exe4-term-040)이다.
* 157의 661/3/0은 물속에서 뭉개지는 「넷토야」를 원문처럼 뭉갰고、`味太`는 「아지타」(exe4-term-024)다.
* 158의 버튼 안내는 배치 030의 「(R버튼:…)」을 따랐다. 130/8은 코끼리 `ゾウ`와 상 `ぞう`의 말장난을
  「코끼리의 상이며 상인 코끼리다」로 살렸고、엔트리 네임 코드의 장음 부호는 배치 077처럼 하이픈으로 썼다.
* 이번 주기에도 판본이 갈리는 레코드는 없어 정적 검증 수가 두 판본 모두 411건씩 늘었다.

### 빌드와 확인

제품 BLUE `6264c87770ed5f9f4929dd6de5697dfaa6b174863f666d5426e3e994cb3874f9`(+1,658,723바이트),
RED `62b6489dd9d12f810da5c063413e9f77d9015b342dacd2afc147369b48f07bdc`(+1,658,603바이트), 포인터 606워드.
게이트 셋 PASS(대사 21,765 / 선택지 578줄 / 용어 47개+칩 이름 181개 4,528회), 벤치 49케이스. 정적 검증 두 판본 PASS
(BLUE 21,720 / RED 21,723). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 21: 배치 159~162, 수수께끼 보류 해소와 딸꾹질 통일

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 159 | 276·451·481·699·707·780 | 스릴 찾는 소년、아빠와 전자상가、다크 칩 신디케이트 네뷸라의 등장、불타는 넷、요리 사범의 마지막 가르침、되돌아온 블루스 | 97 |
| 160 | 273·536·544·597·600·660·745 | 탑 꼭대기 손님、범인을 알리는 아빠의 전화、리갈의 도발、운세 메일、가출한 아쿠아맨、란의 연기、풀려난 명인 | 96 |
| 161 | 127·634·648·719·768 | 아메로파 호텔 방、창고에 갇힌 넘버맨、리키의 작별、아메로팡 뒤 쓰러지는 록맨、언더넷 진입 | 85 |
| 162 | 30·85·94·118·121·122·129·136·457·640·693 | 전파탑 초음파、리키와 크래셔 첫 만남、리더 사로마、대회장 방과 넷배틀 머신、내비 호출 | 97 |

진척 **22,144 / 22,919** (96.6%).

* **아카이브 9·10의 보류 수수께끼 해소.** 메모 `びなのりどみ／んさありえんうた`는 줄마다 거꾸로 읽어
  「みどりのなび たうんえりあさん」(초록 내비、타운 에리어3)、힌트 데이터 `がしてみるは／さ!なだんな／をかなのばた`는
  함께 나오는 「うずまき」대로 오른쪽 위에서 아래로 시작하는 시계 방향 나선으로 읽어 「はなたばのなかをさがしてみるんだな!」다.
  두 답 모두 원문 글자를 남김없이 써서 문장이 되므로 해독이 확정된다(게임 안 대상 위치는 대사 데이터로 특정하지 못했다).
  한국어도 같은 방식으로 뒤섞었다: 「비내 록초／3어리에 운타」、「보는거꽃／아!야다／찾을속발」.
* **번역 게이트에 수수께끼 규칙.** 유괴범 수수께끼(007·560) 포함 7곳을 읽는 법과 답으로 등록하고, 원문이 등록된 답으로
  풀리는지(해독이 맞는지)와 한국어가 제 답으로 풀리는지를 본다. 글자 두 개를 바꾼 사본과 뒤섞기를 풀어 버린 사본을 모두
  거절했고, 거부 시험 2건을 더해 벤치는 51케이스다.
* **딸꾹질 표기 통일.** `ヒック`은 9건 중 7건이 「딸꾹」인데 032·039·157(란)만 「히끅」이었다. 용어집 exe4-term-048/049
  (`ヒック`·`ひっく` → 딸꾹)를 넣고 고치기 전 사본에서 게이트가 정확히 그 세 줄을 잡는 것을 확인한 뒤 고쳤다.
  425의 `ウィック`는 다른 소리라 「히끅」으로 둔다.
* 161은 처음 저작할 때 160의 메타데이터가 섞여 들어가 바로잡아 다시 준비했다.

### 빌드와 확인

제품 BLUE `49fda6c1604528768021467914b8034028739691fbef48e269c11e9213299120`(+1,687,987바이트),
RED `4ae757cffb2cd4521da59e67583e22154d787202685c80edc878cc6f15acde9f`(+1,687,867바이트), 포인터 638워드.
게이트 셋 PASS(대사 22,144 / 선택지 578줄 / 용어 49개+칩 이름 181개 4,611회), 벤치 51케이스. 정적 검증 두 판본 PASS
(BLUE 22,099 / RED 22,102). 부팅 검사 두 판본 DRAWS(색 수 118·100).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 22: 배치 163~166, 엄마의 배웅에서 서치맨 소문까지

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 163 | 229·236·261·539·682 | 대회 내내 배웅하는 엄마、롤을 빼앗긴 데카오와 동생、연설 뒤 청소부、배리어 앞 친구들、결승 전 나르시 | 91 |
| 164 | 125·126·263·329 | 아메로파 거리와 유적、HK 발화 장치 호출、흥정 노인과 대회 안내 내비 | 64 |
| 165 | 478·530·593·607 | 침입자의 최면 가스에 쓰러진 엄마、ANSA 도착、동호회 노인의 전화、유코와 술래잡기 | 71 |
| 166 | 623·649·652·765 | 간테츠와의 만남、대전 상대가 된 롤、스토커 내비에 붙잡힌 롤、서치맨 소문 | 63 |

진척 **22,433 / 22,919** (97.9%).

* 236의 데카오 동생은 배치 071의 「~쪄」、539의 거츠맨 `でガス`는 배치 009의 「~가스」、593의 노인 내비는 배치 017의
  「자네、~게야」、623의 간테츠는 배치 119·124의 거친 표준어를 따랐다.
* 엔트리 네임 코드(125/6/3)의 장음 부호는 배치 077처럼 하이픈、인용 메일(607/8/1)은 이어지는 줄의 한 칸 들여쓰기를 지켰다.
* 판본이 갈리는 레코드는 없어 정적 검증 수가 두 판본 모두 289건씩 늘었다.

### 빌드와 확인

제품 BLUE `f918be03302cc70c0a3907174c2513d6dd5f477a0df06f9416246037dcdd1e0e`(+1,712,351바이트),
RED `5a07b9ee7c9ca4e10ed16135f18e1fbfc6d4d2c1ddba3e71738ef2a6128eeaf7`(+1,712,231바이트), 포인터 655워드.
게이트 셋 PASS(대사 22,433 / 선택지 578줄 / 용어 49개+칩 이름 181개 4,665회), 벤치 51케이스. 정적 검증 두 판본 PASS
(BLUE 22,388 / RED 22,391). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 23: 배치 167~170, 결승 대진에서 미궁의 내비까지

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 167 | 501·543·627·654·668·718 | 결승 대진 발표、다크 소울을 남기고 쓰러지는 리갈의 내비、불량배 두목、롤의 스피드、타마코의 도전、노인의 주문 | 64 |
| 168 | 359·394·450·480·510·511·714 | 전파 방해 프로그램、미궁에 쓰러진 내비、아빠를 기다림、카스티요 종업원 내비、뗏목 안내、소화 버스터 | 55 |
| 169 | 272·358·361·366~368·375·376·473·609·636·642 | 경기장 직원、훈련 프로그램、집 경비견、음료 기계와 원데이 패스、리갈의 이탈、유령 성불、넘버맨、크래셔를 가둔 마피아 | 77 |
| 170 | 351~374·390~401 | 시설 프로그램、미궁의 쓰러진 내비와 떠다니는 빛 | 52 |

진척 **22,681 / 22,919** (99.0%).

* 여러 아카이브가 같은 프로그램 대사를 되풀이하는 곳(366~368、375·376、351~374)은 한 문구를 나눠 쓴다.
* 473의 리갈은 배치 034의 「~게」、609의 유령 내비는 배치 069의 「자네、~구먼」、642의 부하는 「~습죠」를 따랐다.
* 판본이 갈리는 레코드는 없어 정적 검증 수가 두 판본 모두 248건씩 늘었다.

### 빌드와 확인

제품 BLUE `feb301fedcaea0f64237208d800c095855cf4ed7876a5828136b99b2ecc41eb4`(+1,748,631바이트),
RED `15c8339c6972d5e1a123a9cbc9050dba9663d74d8cb90ed205dcae4692c6a33c`(+1,748,511바이트), 포인터 701워드.
게이트 셋 PASS(대사 22,681 / 선택지 578줄 / 용어 49개+칩 이름 181개 4,694회), 벤치 51케이스. 정적 검증 두 판본 PASS
(BLUE 22,636 / RED 22,639). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.

## 2026-09-28 후속 24: 배치 171, 남은 소형 아카이브 전부

| 배치 | 아카이브 | 내용 | 엔트리 |
|---|---|---|---|
| 171 | 152~156·271·282·293·296·297·317·441·445·469·470·483·492·500·509·514·527·532~535·541·557·558·572~576·621·677·678·713·716·741~744·749·785 | 게시판 표지、대회 결과 발표、에리어 연결 알림、발화 장치 정지、사자、짧은 배틀 대사 | 90 |

진척 **22,771 / 22,919** (99.4%). 남은 줄은 보류 중인 아카이브 63(146건)과 도달 불가 56·57(각 1건)뿐이다.

* 에리어 이름은 숫자를 붙여 쓴다(에리어2). 같은 대사를 되풀이하는 아카이브는 한 문구를 나눠 쓴다.

### 빌드와 확인

제품 BLUE `a66858e3cf0789f3097355d7e68b2f411ef2db991b0d3edb18f47980881fadd1`(+1,759,475바이트),
RED `5f21bc817bc953537d04115babda688eeabd7ea675a645c62b3fb7f274192c18`(+1,759,355바이트), 포인터 914워드.
게이트 셋 PASS(대사 22,771 / 선택지 578줄 / 용어 49개+칩 이름 181개 4,709회), 벤치 51케이스. 정적 검증 두 판본 PASS
(BLUE 22,726 / RED 22,729). 부팅 검사 두 판본 DRAWS(색 수 118·95).
실행 확인: 두 판본 콜드 경로 각 107/107 complete·rc0, **11개 메시지 18줄이 ROM 글리프와 픽셀 일치**
(캡처 직접 확인). 이번 배치들의 대사는 콜드 경로 밖이라 정적 검증까지가 그 증거다.
