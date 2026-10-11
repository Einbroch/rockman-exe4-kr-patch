# 재개 기록

2026-09-15 | request | 사용자: 에그제 2 경험을 참고해 에그제 4 한글패치 진행 | 목표: 일본판 두 버전 전체 한글화 | 승인: 분석/번역/개발 시험의 사용자 지시 | 상태: 진행 중

2026-09-15 | platform | game-translate에는 GBA 어댑터 없음 | 해당 하네스 완료/릴리스 상태 사용 불가 | create-kr-patch의 GBA 실제 증거 기반 제작으로 진행 | 근거: 설치 platforms 목록, README.md | 상태: 적용

2026-09-15 | analysis | 각 793개 압축/raw 아카이브 추출, 직접 763/flagged 324 포인터 검증 | flag 없는 단순 08 포인터 가정 금지 | 소비 시 재배치 포인터 플래그를 유지 | 근거: analysis/*_analysis.json, 실제 opening 실행 | 상태: 적용; 전체 flagged 소비자 의미는 추가 조사

2026-09-15 | roundtrip | 양쪽 각 13개 아카이브에서 F9 00 xx x4 인덱스의 상위 비트 손실 | 수정 전 번역 빌드 중단 | printFolderName.entry 4→8비트 보존 | 근거: analysis/roundtrip_differences.json, pristine 플러그인, 수정 후 793/793 왕복 | 상태: 적용

2026-09-15 | versions | 아카이브 781개 동일, 12개 상이 | 번역 전역 공유 금지 | 페이로드 동일 범위만 재사용 | 근거: analysis/version_comparison.json | 상태: 적용

2026-09-15 | font | IWRAM 일반 출력기에서 96바이트/12행/가변 폭 폰트 확인, 별도 64바이트 폰트도 읽힘 | EXE2 폰트/훅 그대로 이식 불가 | Galmuri11 2.24.29 기존 BDF를 기능 시험 후보로 사용 | 근거: analysis/runtime/*fontread*, inspect_runtime_renderer.py, ROM anchors | 상태: 일반 경로 확인; 전체 경로 분류 미완료

2026-09-15 | translation | 공통 오프닝 26개 스크립트/59문구 초안 | 언어 독립 검수 없음 | needs_review, 임시 개발 정책만 선택 | 근거: translations/opening_korean.json | 상태: 초안

2026-09-15 | product | 5페이지/65글자 visibility PoC와 26스크립트/222글자 opening 개발본을 두 버전 모두 원본에서 생성 | 임시 코드 재배정이 다른 일본어를 손상함 | NON-DISTRIBUTION; 배포/전체 게임 시험 불가 | 근거: poc/output/*.json의 Expected Writes/해시/입력 정책 | 상태: 개발본

2026-09-15 | reproduced-failure | 전체 오프닝 시험에서 일반 대화 색 블록 | 442번째 레코드는 폰트가 아니라 palette at blue 0x69F564 / red 0x69F784 | 거절된 ROM을 별도 이름으로 보존하고 441레코드 범위로 원본에서 재빌드, 경계 뒤 0x100바이트 보호 | 근거: 원본/실패본 동일 입력 폰트-read PC, 원본 팔레트 0000 FE7B…, ROM 참조 10곳, poc/output/*rejected_palette* | 상태: 원인 확인/수정 적용; 수정본 런타임은 project_verification.json 확인

재개 우선순위는 README.md의 다음 완료 조건이다. 가장 큰 미해결 조건은 전체 한글 코드 공간이다.
E4 기존 공간만으로 최종 한글 수요가 충족됐다고 판단하지 않는다. 추가 lead 도입 시 압축/적재된
IWRAM 코드와 별도 메뉴 디코더까지 모두 수정/재검증해야 한다. 번역 문구를 자동 치환해
글자 수요를 줄이거나 오프닝 개발본을 전체 한글패치로 승격하지 않는다.

2026-09-15 | decoder-source | 관측한 IWRAM 0x03005800..0x03006FCB 6,092바이트가 ROM 0x212700..0x213ECB와 동일 | 앞선 압축 코드 우려는 이 구간에서는 해당 없음 | 일반 출력기 훅의 직접 저장 좌표를 조사 근거로 사용, 다른 뱅크는 여전히 미분류 | 근거: analysis/decoder_site_survey.json | 상태: 확인

2026-09-15 | runtime-isolation | 동시 실행 한 run의 종료 시점에는 캡처 0개인데 이후 파일이 생겨 실행 소유권 불명확 | 동시 실행 자료를 최종 오프닝 QA로 사용 불가 | 마지막 QA는 순차 실행/설정 저장 금지/SingleInstance=false/실제 ROM 기대 바이트 검사 | 근거: runtime/*opening_palette_fixed/result.json와 파일 생성 순서; tools/run_opening_qa.py | 상태: 순차 QA로 대체

2026-09-15 | opening-runtime | 양쪽 opening_final 각 64/64, opening_end 각 3/3, opening_exit 각 3/3 캡처 완료/종료0 | 콜드부팅 이후 동일 ROM 자연 진행 체크포인트만 연결, 헤더/글리프/압축 데이터 실제 로드 바이트 검사 | 59문구 표시와 마지막 응답, 넷토 방으로의 장면 전환을 시각 확인 | 근거: analysis/OPENING_RUNTIME_QA.json 및 project_verification.json, 각 result.json/캡처 | 상태: 오프닝 표시 시험 통과; 언어 독립 검수/전체 게임/기기 QA 미완료

2026-09-15 | artifact-gate | 원본 SHA 불변, 4개 개발 ROM Expected Writes/전체 차분/압축 해제/441경계 뒤 팔레트 보존 검사 통과 | opening 개발본 BLUE 9d987469c3e55e43a51a0939302e92c3e825dd557876834e263ba6ee1ca15a8d, RED 23ef15f9c64340913c520876fde6ef340998bbfd1b9dd194a3409b6623422810 | 임시 재배정 NON-DISTRIBUTION 정책 유지 | 근거: analysis/project_verification.json, ARTIFACT_MANIFEST.tsv | 상태: 전체 패치 완료 또는 배포 승인으로 승격하지 않음

2026-09-15 | resume | 사용자 계속 진행 요청 | 전체 한글 코드 공간이라는 설계 위험부터 작업 | 기존 일본어 재배정 방식 대신 추가 코드/글꼴 공급을 구현 | 상태: 진행 중

2026-09-15 | extension-sites | 일반 대사/누적 폭 F9 슬롯, IWRAM 글꼴/폭 리터럴과 원래 복귀 지점을 버전별 원본에서 대조 | 전체 오프셋 델타 가정 금지; IWRAM 2A66/488A 후보는 관측 상태의 그래픽/팔레트 데이터로 디코더 주장 철회 | 근거: analysis/expansion_site_survey.json, tools/specs/exe4_dialogue_extension_v1.json | 상태: 일반 대사 확장 좌표 채택; 전체 소비자 완전성 미주장

2026-09-15 | extension | F9 FC + U+AC00 기준 uint16 LE 음절 번호, renderer index 442+번호 | 일반 글꼴 441레코드 및 원본 palette-alias index441의 읽기/폭도 호환 뷰에 복제; 일본어 원본 폰트/폭/팔레트 무변경 | 원본 793개 각 payload에 F9FC 쌍 0개지만 미인덱스/외부 문자열 충돌은 열림 | 근거: extended_dialogue.py, F9FC_indexed_census.json, extended_verification.json | 상태: 일반 대사 11172 공급 구현; NON-DISTRIBUTION

2026-09-15 | reproduced-return-failure | 첫 확장 시험은 1글리프 읽기 뒤 낮은 PC로 진행 정지 | 폭 훅 BX LR가 원래 MOV LR,PC의 짝수 주소로 ARM 상태 전환 | 같은 ROM 실행 추적에서 width-return LR=0804E0C2 확인, TI925T 제어 fixture에서 BX는 T=0/MOV PC,LR은 T=1 | 원본에서 수정본 재빌드; 거절된 BLUE/RED 해시 907016c59d461cdb10011e84a68b6177e325c0a35dc65cdf7479d7fe52410c09 / 28ffaceb12523eec15162730ddbaf0f9e6144c2f2536d6fbad95ab819bc331ed | 근거: *_extended_rejected_return.*, blue_moon_extended_return_trace, test_dialogue_extension.py | 상태: 원인 확인/수정/회귀 시험 통과; RED 실패본은 실행하지 않음

2026-09-15 | extended-runtime | 수정본 BLUE db3fb04fa3636d2f75b619293840d5ca6c1f3e6856b92bf4347e400ceb823351 / RED 0c6c0425c36f55fda4f8167b11a865bb4bea95dda69d0de7316788000022b2b3 | 각 콜드부팅 일반 입력70단계/70캡처/종료0, 59문구 시각 확인 및 방의 원래 일본어 표시 | 원래 IWRAM 출력기에서 추가 글꼴의 정확한222음절 읽기 | 근거: analysis/EXTENDED_RUNTIME_QA.json, extended_verification.json, runtime/*extended_v2_final | 상태: 새 일반 대사 기준선; 언어 검수/전체 게임 미완료

2026-09-15 | font-boundary | 이야기 번역을 수정하지 않는 별도 수동 작성 기능 입력으로 첫/마지막 음절과 E5/E8/FF/00 인자·밀집 받침·영문·숫자·줄바꿈 시험 | 각9단계/9캡처/종료0; 새11172 글꼴 모두 독립 BDF 픽셀 대조 및 모든 코드 제어 CPU fixture 실행 | 새 TPL/MSG 바이트 왕복과 정확한 문구 재추출을 주 빌드에 강제 | 근거: boundary_verification.json, poc/font_probe_wording.json, runtime/*boundary_final | 상태: 일반 대사 공급/경계 확인; 실제11172개 전부 게임 화면에서 표시한 주장은 아님

2026-09-15 | menu-design-open | Galmuri9의9픽셀 잉크는 관측8픽셀 타일 셀에 손실 없이 들어가지 않음; Galmuri7 공급4363 | 없는 글리프 빈 칸 대체 금지 | 다음은 실제 메뉴 텍스트 수요/셀/버퍼/소비자 경계를 확정하고 표현 선택 | 근거: full_font_supply_survey.json, native tile renderer | 상태: 미해결

2026-09-16 | resume | 사용자 중단된 부분부터 이어서 진행 지시 | 일반 대사 기준선 보존, 두 타일 글꼴/색상 경로 조사 및 메뉴 추가 개발본 구현 | 상태: 진행 중

2026-09-16 | menu-source-correction | PET 상태6E73BC 주소를 파일명으로 못 찾아 추출 목록 밖이라고 첫 추정 | raw 아카이브13 범위와240~243테이블 엔트리에 실제 포함됨 | 인덱스 밖 주장은 철회; 다른 미인덱스 모집단은 여전히 미해결 | 근거: menu_consumer_survey.json, 6E6A3C.tpl, runtime/blue_moon_menu_survey_12 | 상태: 대조/정정

2026-09-16 | menu-sites | 실제 PET/폴더/저장에 두 원본 글꼴, BG/잉크/그림자0/1/2 및1/3/4 | BLUE68E004/6C699C, RED68E224/6C6E60 각각 전체441×64 원본 앵커 대조 | 원본213650슬롯 F9만 연결; FC 외 nextbyte는 기존1바이트 F9로 전달 | 근거: exe4_menu_extension_v1.json, runtime/menu_survey_09..12 | 상태: 관측 두 스타일 채택; 모든 소비자 완전성 미주장

2026-09-16 | menu-build | 메뉴11스크립트 source-bound needs_review 초안, 미선택 raw 스크립트/EOF 슬롯/alias 바이트 보존 | 쉼표 호환표가 미선택、를 누락시킨 것을 보존 gate로 발견해 ROM쓰기 전 거절; 메뉴 파생 플러그인은 원문표 유지 | 새4363음절×2색상 공급/번호 테이블, 없는 수요는 컴파일 전 거절; 미분류 실행 코드/폰트는 정지 루프 | 근거: menu_extension.py, menu_verification.json, menu_bench.json | 상태: 벤치 통과; 인간 서체/언어 검수 미완료

2026-09-16 | menu-runtime-partial | 수기헤더 guard 오류 조사1은0캡처/종료1; ROM에서 자동 생성해 수정 | BLUE 첫 장시간 실행은104/107캡처240초timeout | 부분 증거로 보존, 완료 판정/그 체크포인트 재사용 금지 | 근거: blue_moon_menu_survey_01, blue_moon_menu_final_01/result.json | 상태: 같은 ROM360초 순차 재시험 진행

2026-09-16 | menu-runtime | BLUE40b49cf6ac463f3a5e6d02d070f3ea367456188bed9c7f3e2ff6d98697b85acd / RED164433a06a42d5de30cf280ea1ed3d16314e89ebdab00a84a9c30891714b7b47 | 두 버전 menu_final_02 각각107/107콜드부팅/종료0, 두 타입 새 타일21레코드 실제읽기/스트림/버퍼 대조 | PET넷토 방/폴더1/저장4항목 시각 확인; 기존 일본어 칩/숫자/NAME/저장 질문/아이콘 유지 | 근거: menu_verification.json, MENU_RUNTIME_QA.json, menu_two_versions.png | 상태: 관측 두 메뉴 스타일 추가 기준선; 전체 메뉴/언어/인간 서체/기기 검증 미완료

2026-09-16 | folder-consumer | normal F9 폴더 출력은64바이트 버퍼 복사 후 대사/width스트림 교체 | 새 폴더1/2의 실제 native 전달/width 버퍼 경로와 복사된 IWRAM 파서/개행/종료 padding 통합 fixture 추가; 복사/DMA helper만 stub | 근거: test_menu_extension.py, menu_bench.json | 상태: 메뉴7개/대사6개 제어 시험 통과; 폴더2 실제 화면/모든 기타 동적 소비자 완전성 미주장

2026-09-16 | failure-retention | 최초 쉼표 실패 로그는 이후 정상 재빌드 로그와 구분이 필요함 | 미변경 raw원문과 잘못된opening표만으로 별도 원인 재현; TextPet종료0인데15바이트/14스팬 누락 | 원래 실패 아티팩트라고 주장하지 않음, 제품 쓰기 없음 | 근거: rejected_menu_comma_reproduction/result.json, reproduce_menu_comma_rejection.py | 상태: 거절 원인 재현/보존

다음 재개는 나머지 mmbn4s와 칩/전투/이름 입력 소비자를 실제 상태/글꼴/버퍼별로 분류하고
전체 번역 수요를 선언하는 단계다. 현재4363 공급이 전체 메뉴 수요를 충족한다고 가정하지 않는다.
default 일반 대사 기준선과 --menu-font 추가 개발본은 같은 primary build의 옵션이며
기존 일본어 메시지/그래픽이 남은 NON-DISTRIBUTION이다. 언어 검수와 최종 서체 인간 판단은 미완료다.

2026-09-16 | resume | 사용자 계속 진행 지시 | 칩/NAME 소비자 조사 및 잘못된 확장 선택 거절 | 상태: 진행 중

2026-09-16 | chip-consumer | BLUE0802F4AC/RED0802F4E4는 raw41 문자열을 BG 타일맵으로 변환하며 F9>=E5에서 종료 | 일반 메뉴 훅만으로 칩 한글화를 주장할 수 없음 | 원래 함수 전체를 CPU fixture에서 실행해 빈/접두사만 남는 이름 재현 | 근거: test_consumer_contracts.py, menu_bench_2.log | 상태: 원인 분류; 칩 확장은 미구현

2026-09-16 | consumer-gate | 원래 메뉴11개 명시적 항목만 채택한 계약에서 허용, 원본 코드/문구/셀/인코딩 버퍼 한계 대조 | raw41 및 이웃 미분류 문자열을 컴파일 전에 거절 | 대사6/메뉴7/소비자4 PASS; 주 빌드 재생성 후 양쪽 메뉴 ROM SHA 동일 | 근거: exe4_consumer_contracts_v1.json, consumer_contracts.py, menu_verification.json | 상태: 적용; 자동 전체 소비자 승격 금지

2026-09-16 | chip-runtime | 같은 menu_final_02 ROM의 검증된 coldboot 체크포인트에서 각각31/31 일반 입력/종료0 | 초기 폴더30칩 스크롤, 서로 다른 이름10종/호출58개/위아래 타일맵 간격16바이트/기준타일512 | 실제 스트림/아카이브41/소스 payload/문구 대조 | 근거: runtime/*folder_chip_inventory_01, remaining_consumer_survey.json | 상태: 초기 폴더 범위; 전투/라이브러리/모든 호출 미분류

2026-09-16 | chip-draft | 캐논·소드·리커버리10은 EXE2 기존 번역 참고, 10종 source-bound needs_review 초안 | 필요24음절 Galmuri7 공급 있음; GPU 공급 증명과 다름 | 제품에는 제외 | 근거: chip_names_korean_draft.json, remaining_consumer_survey.json | 상태: 초안; 독립 언어 검수/실제 한글 칩 화면 미완료

2026-09-16 | chip-vram | 양쪽 실제 폴더 VRAM에서 source font0..159 전체10240바이트가06004000에 유일 일치 | source416 시작2048바이트가0600D800에도 일치하나441공급 뒤7레코드 상당은 용도 미분류 | 바로 뒤 공간을 새 폰트용으로 예약하지 않음 | 근거: blue_moon_chip_survey_03, red_sun_chip_vram_survey_01, remaining_consumer_survey.json | 상태: 실제 적재 바이트 확인; 다른 VRAM 사용/적재 코드 전수 조사 남음

2026-09-16 | name-consumer | 두 버전 PET actual NAME word00828282, 원래 shift0/8/16 출력3회 | 두 버전/두 스타일 CPU fixture에서3바이트 index 및 상위바이트 무시 확인 | F9FC4바이트 스트림으로 NAME 필드 변경 불가 | 근거: runtime/*name_trace_01, test_consumer_contracts.py, archive/418/script/11의3개 menuOptionName source-only | 상태: 기존 표시 분류; 입력/저장/CRC/통신/이리더 소비자 미분류

2026-09-16 | survey-scope | blue_moon_battle_survey_01..04는 방/PET책상 설명에 머묾 | complete는 입력/캡처 완료 의미이며 전투 화면 도달 근거 아님 | 최종 전투 QA에서 제외 | 근거: 각 step PNG | 상태: 방 이동 조사 자료만 보존

다음 재개는 CHIP_EXTENSION_PLAN.md를 따라 폴더의 모든 VRAM 적재/쓰기와 예약 영역을
확정하고 칩 F9FC BG 타일맵 소비자를 구현하는 것이다. 아카이브41의 다른 소비자를 닫기 전에
번역 raw41 재배치를 자동 추가하지 않는다. 기존 두 메뉴 제품 SHA/107단계 완료 기준선은 유지된다.


2026-09-16 | folder-chip-implementation | 사용자 계속/중단 지점 재개 지시 | private archive41 clone과 F9FC BG tilemap parser 및24음절 split VRAM cache 구현 | 초기화 native font copy를 보존하고2개 새 bank를 실제 queue helper에 추가 | 근거: chip_extension.py, exe4_chip_folder_v1.json | 상태: 폴더10종 개발 범위만 지원

2026-09-16 | VRAM-correction | 06006800부터는 빈32글리프 구간이 아니라7개128바이트 칩 아이콘 | 두 버전8단계 view/edit/reentry WRITE/copy trace로 겹치지 않는6B80..6FFF 및7360..74DF 채택 | 첫 BLUE 넓은 trace01은10/13 timeout 부분 증거/체크포인트 재사용 금지 | raw IO dump를 PPU 설정 근거로 채택하지 않음 | 근거: runtime/*chip_vram_writes_02, adopt_chip_spec.py | 상태: 관측 폴더 수명만 채택

2026-09-16 | folder-chip-tests | 양쪽 원래 chooser 함수 전체256항목 실행: 미선택246개 출력 동일/선택10개 상하타일 확인 | real queue helper3요청, 없는/범위 밖 음절/9번째 셀 stop/canary 유지 | 전체11172 normal 및4363x2 menu BDF pixel/원본/차분/최종 ARM byte 검증 | 근거: chip_bench.json, chip_verification.json | 상태: CPU3 및 기존17 PASS

2026-09-16 | folder-chip-runtime | BLUE44c338623fb644edde81344da28b609cbc2d3dfce41141cb82af4e7f2818c2f5 / RED938d3893cb01d869953fcdcaa7c782d32524104a4a87a647e1091efe8b4cf493 | 각107콜드/38폴더 입력 캡처/종료0;10종 실제 stream,33캡처 cache bytes,31캡처 native buffer→BG map 확인 | 편집/PET복귀/재진입,10종 한글/아이콘/코드/숫자/색상 직접18캡처 검사 | 근거: chip_verification.json, CHIP_FOLDER_RUNTIME_QA.json | 상태: 제한된 개발본 수용, 배포/인간 최종 서체/독립 언어 검수 미완료

현재 이어갈 지점은 초기10종 밖 폴더 칩의 수요/매 화면 상주량과 다른 칩 소비자 조사다.
24음절 고정캐시를 전체 칩 번역으로 확장하지 않는다. 다른7개 아카이브41 참조와 원본은 그대로다.
배틀/도감/외부 문자열, NAME 입력/저장/통신, 전체 번역/기기 QA는 남아 있다.
기존 메뉴 기준선과 새 *_opening_menu_chip_folder_korean_development.gba는 별도로 보존한다.


2026-09-16 | chip-catalog | 사용자 계속 진행 지시 | source41..44의391항목/두 버전 원문 대조, ROM chooser0..310과RAM311 경계 확인 |294개 수작업 초안,EXE2 exact22/기존10 문구 보존,8칸/204음절/누락0 | source binding·양쪽 MSG byte roundtrip/unselected span PASS | 근거: chip_catalog_analysis.json, chip_catalog_authored.tsv | 상태: research-only/needs_review, 새294종 ROM 삽입 금지

2026-09-16 | catalogue-limit | ROM source 경로에는 전투용 내부 명칭도 있음 |294개를 실제 장착 가능 칩 수로 취급하지 않음;7이름36/41음절 조합은 가상 작업 집합만 증명 | 도감 표시5번은 sourceID15발칸1 | 번호 동일성/실제 장착 조합 주장은 하지 않음 | 상태: source reachability와 gameplay eligibility 분리

2026-09-16 | native-library | BLUE08038030/RED08038064는 상하16바이트 행/palette E200/0 padding, F9FC 종료 | 원본+현재개발본 whole-function CPU test로 빈/접두사 손실 재현 | source6/BG8/PPU2 단계 각버전 완료/rc0; 실제sourceIDs1/4/15와prefix32bytes/136glyph8704bytes VRAM 일치 | 근거: library_consumer_analysis.json, library_consumer_bench.log | 상태: 분류 완료, 새한글 도감 파서 미구현

2026-09-16 | library-cache-correction | 폴더160font/6800icon/7000label과 달리 도감136font/6200icon/7400label |6380 후보는3/4행 아이콘과 겹쳐 거절, 원본7×128 루프로6580부터58glyph 후보 | 실제PPU4BG×1024全entry를 검사해기본탭 기존참조0,활성copy겹침0 | raw IO interpretation을 근거로 쓰지 않음 | 근거: *library_ppu_survey_01, library_consumer_analysis.json | 상태: 후보, 갱신/전환/나머지상태/새pixel 미검증

현재 다음 구현은 analysis/LIBRARY_EXTENSION_PLAN.md의 도감7행×8칸56glyph 슬롯 및 private 선택이다.
기존 아이콘의 직접복사 helper 후보/프레임 갱신, 원래palette/0padding/실제버퍼02016600 범위 및
다른5행 caller의 원문 유지, PET↔도감↔폴더 리소스 복구를 검증한다. 현 ROM SHA/폴더10종 기준선은 유지된다.
391모집단 밖 source/PA/soul/special 및 RAM eReader의 유효ID/입력/전투/저장/통신/기기/독립언어 검수는 미완료다.

## 2026-09-16 후속: 도감294종 private 개발 구현 완료

`exe4_chip_library_v1.json`에 BLUE37F58/RED37F8C의12바이트 원본 창, 원래 parser/root41/42,
copy helper,02016600의7행 범위와06580..737F의56슬롯을 고정했다. 첫10바이트 점프안은 r7을
훼손하는 CPU 실패로 거절했고, 원래 분기까지 포함해 r7을 스택 보존하는12바이트 창으로 고쳤다.
첫 실화면은 새 타일에 palette상위bit가 빠져 palette0으로 표시돼 거절했다. saved E200에서
FC00만 결합하도록 고친 최종 제품을 새02 실행으로 다시 검증했다. 01 실행은 결함 이력이다.

원본 archive41/42와 원래 claims는 그대로다. 정렬된 도감7행 버퍼와 원래 두 root일 때만 private
clone을 선택한다. 294개 초안은 development seven-row library insertion only이며 needs_review다.
각 한글 셀은 Galmuri7 full bank에서0800098C/SVC0B로64바이트를 해당 행/열 슬롯에 복사한다.
native문자,0padding,8칸,원래E000 palette bits,missing/range/ninth explicit stop을 유지한다.

최종 BLUE ROM SHA는 b10f56a147ec5e025c80bf8e0b84d2ab152e1a0232b79afcd15234d5950db09e,
RED는13ee7822bc281f9717dce0029ca20f13cbc5013b4e522c9a1b3a7394b762dd6e다.
CPU는 양쪽 ID0..310, 번역294,7행, native fallback, 실제 copy wrapper 의미를 통과했다.
각 판본 새 제품에서 cold02 107/107와 final02 25/25 complete/rc0이다. 실제 등록된 source1/4/15,
표준/메가 탭, 스크롤, 폴더 진입으로 공유 VRAM이 덮인 뒤 도감 재진입 복구를 확인했다.
step25 RAM에서 에어슛 E35C/E35E/E360, 발칸 E36C/E36E와 digit E204가 양쪽 동일했다.
근거는 library_bench.json, library_verification.json, LIBRARY_RUNTIME_QA.json,
visual_qa/library_korean_two_versions_02.png이다. 실제 저장에 없는 나머지291개를 자연 화면에서 봤다고
주장하지 않는다. 다음은 전투/PA/soul/special/RAM311+/NAME/저장/통신 소비자와 독립 언어 검수다.

## 2026-09-17 후속: 전투 칩 선택창 개발 구현과 두 판본 검증 완료

이번 재개에서는 Mom→오븐→첫 튜토리얼 전투에 실제 도달해 Custom Screen 이름 소비자를
분류했다. 이전 battle_route05..42는 이동 탐색 자료이며 전투 증거가 아니다.
BLUE chooser0801FC84의 원래 호출0801FB5E 직후와 RED의 개별+3C 위치를 원본 문맥으로 고정했다.
이8바이트 창에서만 archive41/42 private clone을 선택하고 원래 r3/r4/r5/r6 준비를 복구한다.
root42는 index0..54만 선택하고 그 밖의 root/index는 원문을 유지한다. 다음 원래 명령에서
r7=8 tint를 설정하므로 기존 F9FC 메뉴 렌더러가 원래0203E590의512바이트를 채운다.
원래 DMA 큐를 거쳐06009380에 표시하며 추가 VRAM 할당은 없다.

새 옵션은 --battle-caption이며 --library-chips가 필요하다. 입력294개 초안 문구/needs_review는
그대로이고 별도 caption 계약으로 소비자를 명시적으로 추가했다. 공용 archive/포인터/기존 폰트 및
다른 기능 바이트는 이전 도감 제품과 동일하다. 새8바이트 훅과 추가 helper만 차이가 있음을 검사했다.
tools/battle_caption_extension.py, test_battle_caption.py, verify_battle_caption.py가 구현/CPU/정적 근거다.
양쪽 ID0..310 전체(번역294/원문17), tint/padding,512바이트 canary,SP/r8/r9 및 fallback PASS.
CPU의 최종 큐 전송은 stub이며 실제 전송 근거와 구분한다. 빌드 도구 변경에 따라 기존 도감
bench 입력 해시도 재실행으로 갱신했고 verify_extended의 도감 회귀 검사도 다시 통과했다.

채택 제품 BLUE SHA630bd9b425f4f0b0b2c6ffc5b17b2413bf50b4dabc2708b20521246772420a1f,
RED SHA44c85aba141fa37083a3c0489bc0eea25d2d9dd8398d9f329217bc6332c68a26.
파일은 poc/output/*_opening_menu_chip_folder_library_battle_caption_korean_development.gba다.
원본 및 이전 도감 제품은 보존했다. NON-DISTRIBUTION 개발본이며 전체 패치 완료가 아니다.

각 새 제품 cold01은263입력/17캡처 complete/rc0이지만 부엌에서 끝난다. 과거 checkpoint 경로를
일괄 재생한 결과가 달랐으므로 후속 route02(8입력)→03(11)→04(11)로 위치를 수정했다.
route04에서 실제 오븐 접속, ready01(35입력)에서 Custom Screen 도달을 직접 확인했다.
모든 연결은 동일 ROM 해시의 체크포인트/receipt 검증을 거치며 게임 RAM/진행 플래그를 쓰지 않았다.
두 판본 final01 snapshot6단계와 calls01 tilecalls6단계가 complete/rc0이다.
sourceID1/29/48/107의 캐논·미니봄·소드·리커버리10을 직접 확인했으며, 총12캡처의512바이트
RAM 및 VRAM이 독립 생성한 예상 글자 데이터와 일치한다. 네 private stream 주소/prefix도 일치한다.
근거: battle_caption_verification.json, BATTLE_CAPTION_RUNTIME_QA.json 및
visual_qa/battle_caption_two_versions_01.png. 재현은 README 마지막 절 및 run_battle_caption_followup.py.

다음 이어갈 지점: ready01 또는 final01의 **같은 새 ROM** 체크포인트에서 실제 칩을 선택해
전투 화면으로 나가고, 선택창 밖 사용 중 칩 이름/칩 설명의 소비자를 분류한다.
새 ROM 변경 시 이 체크포인트를 다른 해시 제품에 주입하지 말고 콜드 경로를 재현한다.
다른 archive41 참조를 이번 caption 성공만으로 번역 복제본에 연결하지 않는다.
나머지294종 자연 표시·전체 폴더 확대·PA/soul/special/RAM311+/NAME·저장·통신·전체 번역·기기 및
독립 언어 검수는 미완료다. ledger는 모든 산출물과 문서 저장 후 마지막에 갱신/검증한다.

## 2026-09-17 재개: 전투 사용 대기 이름 구현 완료, 설명10종 준비

실제 전투 호출은 앞선 후보04A60C가 아니라 BLUE0801503A→080539D4였다.
입력r0/root41,r1/chip1,r2/0203E590,r3/06009380,r4/8,r5/1,r6/style0,r7/tint0을 관측했다.
BLUE08015030/RED08015064의원본494B08240125494E를8바이트 hook으로 바꾸고 기존 private
clone41/42를 선택한다. 원래 준비 명령과 계속 주소를 복구하며 다음 명령의tint0은 유지한다.
기존 선택창 제품에 비해 이8바이트와 추가helper만 달라지고 폰트/원문/다른 기능 바이트는 같다.
--battle-active는 --battle-caption을 요구한다. 새제품 SHA:
BLUE e9ce575ce682cf23f460671c37d46a032d2b0875ec55729817833e6cac96fa65
RED bbf5aec22e26dedb086c717a9bd36d4f51ef9217e0657082337b39cb4a177d73
파일명 *_opening_menu_chip_folder_library_battle_active_korean_development.gba, NON-DISTRIBUTION.

CPU는 양쪽311IDs/번역294/원문17 출력·512바이트 canary·SP/r8/r9·fallback을 통과했다.
특히 native caller가r0를 이름 길이와 뒤 공격력 숫자 좌표에 쓰므로294개 모두r0==len(text)를
검사했다. 최종DMA 큐는CPU test stub이며 actual transfer 증거와 구분한다.
기존 도감/선택창 검증도 변경된 build 도구 입력 해시로 갱신했고 이전 ROM SHA는 유지했다.

run_battle_active_qa.py는 새 제품별cold263입력부터 caption route02..04/ready를 순서대로
재현하고 active survey01..05로 실제전투에 진입했다. 각verify_survey05 step2가 캐논40 대기다.
run_battle_active_followup.py의use01(6입력)→reentry01(3)→second01(9)에서 두 캐논 사용,
이름 지우기, R선택창 재진입, 미니봄50 선택/전투복귀를 확인했다. 앞뒤1입력 calls01/02는
각private sourceID1/29 stream과tint0을 확인했다. 모든receipt complete/rc0 및같은ROM계보다.
양쪽12개이름snapshot의RAM/VRAM512bytes=ROMglyph, BG3(F800 map/8000 tileset)의상하18/19행
이름·숫자 배치가 일치했다. use01 step4/5/6은각16칸×2행0으로소비후잔상이없다.
직접본실화면은analysis/visual_qa/battle_active_two_versions_01.png이며 판정은
BATTLE_ACTIVE_RUNTIME_QA.json/battle_active_verification.json에기록했다.

설명: blue_moon_battle_description_survey01의R창은archive54/script1.
description_trace02에서0801FCDC returnr0=08749A28/r1=1,03006A48 20glyphcalls/첫index319(前)를
관측했다. BLUE literal1FCE4에archive54,1FCE8에archive55가있고chipID의9bit가선택에쓰인다.
source54는각256scripts/10048bytes/raw,4개참조(Blue1FCE4/106AC4/106DAC/1098A8,
Red은chip_description_analysis.json의실제값)다. 다른3참조는사용처미분류로유지한다.
translations/chip_description_authored.json의초기10종을수작업작성했고source-bound draft생성,
71Hangul Galmuri11공급/최대132px·3줄연구예산/양쪽MSGbyte왕복/컨트롤·246미선택스팬보존PASS.
이초안은research-only이며ROM에미삽입이다. prepare_chip_descriptions.py로재현할수있다.

다음작업: Custom Screen 설명의원본selector/표시폭·높이·loader·해제수명 및4개참조를구분해
명시적소비자계약을만들고설명10종을개발삽입한다. 일반대사F9FC가있다는이유로4개참조를일괄교체하지않는다.
새 ROM 변경 시같은hashcheckpoint원칙유지. 현재 new verify_ready01은선택창,second01은미니봄대기다.
기존ready01은다른captionROM해시이므로새activeROM에주입하지않는다.
294개자연획득/모든전투·폴더범위/PA/soul/special/RAM311+/NAME·저장·통신·전체대사·독립검수·기기QA는남아있다.

## 2026-09-19 재개: 선택창 설명10종 삽입 및 두 판본 검증 완료

이전 중단 시 ledger는19260건/850377472바이트로 저장돼 있었다. 재개한 검사 중 새 RED 설명
trace01 파일을 추가해 옛 inventory와의 차이가 생겼으므로, 이번 최종 ledger는 새 자료를 포함해
다시 갱신한다. 기존 기록의 바이트/해시 오류로 판정한 것은 아니다.

RED에서도 description selector return0801FD18의r0=08749F30/r1=1과 normal03006A48의20글자,
첫glyph319를 관측했다. 실제BLUE selector는0801FCA8,RED0801FCE4부터 시작한다.
code영역0..55000의Thumb BL 후보조사에서는caller각202B6/202F2 하나를 확인했지만,
이조사만으로전체간접호출이없다고주장하지않는다. 원본 문맥과TPI의명시적포인터를계약으로고정했다.

exe4_description_v1.json은Blue1FCE4/Red1FD20의Custom Screen 설명table1개와원본context를고정한다.
description_extension.py는컴파일된archive54복제본을추가하고포인터4바이트만교체한다.
새실행코드/글꼴/VRAM할당은없다. 원본archive54와다른3참조,archive55와기존개발기능은그대로다.
옵션--chip-descriptions는--battle-active를요구하며needs_review10종에대한개발opt-in이다.
입력기본정책을전체소비자허용으로승격하지않는다.

최종제품: *_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba
BLUE SHA342642391ead8f10ac1ad99369ed35be3acbb2f1c16033c5fa3f9d654cf540d8
RED SHAc622fb0768f4b3daaaeda3ad8d0bc0f440af50a1df38d0e687e73f6a9443273d
원본/기존active제품보존,NON-DISTRIBUTION 개발본이다.차분은4byte pointer+clone뿐이다.

test_descriptions.py는각514입력(0..511,3784,FFFF)으로원래selector끝부분을실행해index/반환/stack을
대조했다.이는514개유효설명이나자연플레이범위의증명이아니다.또256개script를전부검사해선택10개는
정확한번역바이트로만치환되고control명령이그대로이며,246개는완전일치함을확인했다.
준비된10종71Hangul의최장줄123px,보수적작성예산132px/3줄을유지한다.132px를물리적창폭으로
취급하지않는다. 실제창은게임의기존전체폭메시지박스/들여쓰기규칙을그대로사용했다.

run_descriptions_qa.py로각새ROM cold263입력→route02/03/04→ready35입력을재현했다.
비관측이동구간은probe none으로실행하되ROM guards와같은hash checkpoint규칙을유지했다.
final01은16입력snapshot,reads01은같은ready체크포인트/같은16입력의Hangul bank read probe다.
두판본각sourceID1/29/48/107과소드재개방의5회에대해글리프read집합이문구와정확히일치했다.
각31개의서로다른한글음절실제읽기를관측했다.10회open/close에서caption VRAM512bytes가
열기전/열린중/닫은뒤같았다. 실제두판본32개final캡처에서한글4설명,줄바꿈,닫기,선택이동,
소드재개방을직접보았다.잘림/일본문구잔상은관측하지않았다.나머지6종자연표시는미검증이다.
채택근거:descriptions_verification.json,DESCRIPTIONS_RUNTIME_QA.json,
visual_qa/descriptions_two_versions_01.png.이전도감/caption/active 검증도변경된build입력해시로재실행PASS.

다음재개: archive54의나머지3참조가폴더/도감등어느설명경로인지실제출력으로분류한다.
현재description제품의descriptions_ready01은첫전투선택창,final01은소드선택/설명닫힌상태다.
칩설명문구10종은삽입됐지만다른설명소비자및나머지설명/대사번역은아직미완료다.
폴더의10종밖이름,PA/soul/special/RAM311+/NAME·저장·통신·전체게임·독립언어/서체·기기QA도남아있다.

## 2026-09-20 재개: 폴더·도감 설명10종 삽입 완료, 9칸 한도 확정

앞선 세션이 빌드만 하고 멈춘 지점을 이어받았다. 중단 시점 상태는 v2 제품 두 개와
정적/CPU PASS, 그리고 두 판본 `menu_descriptions_cold_02` 체크포인트까지였다.
이번에 같은 ROM 해시 체크포인트에서 `final_02`를 각51입력/51캡처 complete/rc0으로 실행하고,
캡처를 직접 검토한 뒤 기록했다.

archive54의 참조4개 중 셋을 분류했다. `1FCE4`(선택창)는 앞 절, 이번에 폴더 편집
BLUE `106AC4` / RED `106B34`와 도감7행 BLUE `1098A8` / RED `109918`을 실제 출력으로 붙였다.
네 번째 BLUE `106DAC` / RED `106E1C`는 여전히 미분류라 원문 포인터를 그대로 둔다 —
참조가 같은 아카이브를 가리킨다는 이유만으로 번역 복제본에 연결하지 않는다.

**칸 한도는9다.** 네이티브 파서는 줄마다10칸을 채우지만 OAM에는 줄당 8×16 스프라이트가
9개만 올라간다. 열 번째 칸은 버퍼에 남고 화면에는 제출되지 않는다. 10칸으로 쓴 첫 제품
(BLUE `2b48d2b7…`, RED `55d4b27d…`)은 실화면에서 마지막 글자가 사라져 거절했고
`analysis/rejected/menu_descriptions_10cell/`에 OAM 근거와 함께 보존했다.
**RAM=VRAM 일치는 표시된 문구가 온전하다는 증거가 아니다** — 이번 기록기는 줄마다 아홉 개
OBJ 셀의 타일/좌표/팔레트를 세고, 열 번째 칸이 빈 칸인지 단언하고, 화면 픽셀의 잉크 기하를
글리프 비트맵과 대조한다.

채택 제품 BLUE `770836ad7ed268c766f1d8cb56790dc109aede3258250cea0ebcad52d015db7d`,
RED `ec7aea0fc00c318581fe3476d69525e6885c0f85c0405f8b84b03bac6ee0e7e7`.
파일은 `poc/output/*_opening_menu_chip_folder_library_menu_descriptions_v2_korean_development.gba`다.
차분은 두 판본 모두10,368바이트 — 전용 복제본과 포인터8바이트뿐이고 새 실행 코드/VRAM 할당은 없다.
이전 제품과 원본은 보존했다. NON-DISTRIBUTION 개발본이며 전체 패치 완료가 아니다.

`verify_artifact_manifest.py`에 이 단계의 귀속 검사를 넣었다 — 거절된10칸 제품 해시가
9칸 주장에 붙지 않는지, 기록된 문구가 줄당9칸을 넘지 않는지, 캡처30개의 증거 해시가
맞는지 검사한다. `record_artifacts.py`는 10칸 제품·그 실행 폴더·그 시각 시트를
거절 이력으로 분류하고, 메뉴 설명 컴파일 산출물을 설명 입력으로 분류한다.

다음 재개: 네 번째 참조 BLUE `106DAC` / RED `106E1C`의 소비자를 실제 출력으로 분류한다.
그 뒤는 카탈로그294종 설명의 나머지와, 아직 손대지 않은 본편 대사 모집단이다.
폴더10종 밖 이름, PA/soul/special/RAM311+, NAME 입력·저장·통신, 전체 번역,
독립 언어/서체 검수, 기기 QA는 그대로 남아 있다.

2026-09-20 | fourth-reference | 다음 단계 사전 조사 | 미분류 참조 BLUE `106DAC` / RED `106E1C`는 폴더 풀과 같은 모양의5워드 블록이고 다섯 워드 전부 정적 적재 경로0, 앞 루틴 BL 호출자0 | 전투 참조도 직접 적재0인데 표 기준점으로 닿는 실제 소비자라 "죽은 참조" 결론은 보류; 판정은 그 주소 읽기 BP 런타임 | 근거: analysis/fourth_description_reference_survey.json | 상태: 후보

## 2026-09-20 착수: 본편 대사

사용자가 다음 방향으로 **본편 대사**를 골랐다. 지금까지의 화면별 계약 작업과 달리,
일반 대사 경로는 이미 뚫려 있다 — F9FC 확장의 **11,172자는 현대 한글 음절 블록 전체**라
이 경로에는 글리프 예산 문제가 없다.

세 가지를 세웠다. **모집단**: 계약 소유를 뺀 이야기 후보 710 아카이브, 일본어를 담은
id 25,302, 서로 다른 줄 18,847, 그리고 두 판본 원문이 99.5% 같아 **번역 한 벌로 양쪽**을 덮는다.
**조판 예산**: 폰트가 비례폭이라 렌더러가 적재하는 폭 표로 전 줄을 실측했다. 리터럴은
게임 전체에서 최대 3줄이고, 이야기 아카이브의 자기 최장 줄은 p90 176px, 일반 대사 최장은
198px다. 채택값은 **한 줄 180px = 한글 15자, 한 쪽 3줄**. 200px를 넘는 7개는 BBS·미스터리
데이터·엔딩 크레딧으로 **다른 창**이다. **전수 추출**: 23,758 레코드에 안정 id와 원본
payload/TPL 해시, 원문 줄별 실측 픽셀을 붙였다.

원본이 나누는 두 스크립트 언어를 분류로 승격했다 — `story`(mmbn4) 22,919 레코드 /
694 아카이브 / 고유 17,184줄 / 48만 9,595자, `short`(mmbn4s) 839 / 32 아카이브.
**short 는 이야기 번역에 넣지 않는다**: 짧은 라벨은 소비자가 따로이고 일부는 대사 인코더의
선두 바이트에서 종료한다(아카이브 41이 그랬다).

게이트 `check_story_translation.py`는 배치를 컴파일러 앞에서 거른다. 만들 때 인자 우선순위
버그로 `--batch` 가 통째로 무시되고 있었는데 **음성 시험이 잡았다** — 게이트는 실패할 수
있음을 먼저 증명한 뒤에만 통과를 보고한다(`test_story_gate.py` 12건, `story_bench.json`).

아직 **한 줄도 번역하지 않았고 ROM 에 넣지도 않았다.** 다음 재개는
(1) 배치 번역, (2) 아카이브 하나만 재배치하던 `build_opening_poc.py`를 전 아카이브
재삽입으로 확장(TextPet `.tpi` 색인과 793/793 왕복은 이미 통과해 있다),
(3) 자연 진행 런타임 QA다. 이 조사들은 이 아카이브들이 일반 렌더러에서 그려지는 것을
**관측했다고 주장하지 않는다**.

2026-09-20 | story-punctuation | 본편 구두점 제약 확정 | 표에 ASCII 쉼표 글리프가 없고, 오프닝이 쓴 「`、` 항목을 `,`로 치환」 수는 본편에서 못 쓴다 — 한 아카이브에 미번역 일본어가 남아 그 `、`를 인코딩할 수 없게 된다(메뉴 단계 실거절 이력) | 쉼표는 `、`(U+3001) 또는 생략, 말줄임표는 `.` 세 개; 게이트가 ASCII 쉼표 거절 | 상태: 규칙 채택

2026-09-20 | story-batch-001 | 첫 배치 번역: 오퍼레이션 배틀 메뉴 명인 설명 | 아카이브3(Blue)/4(Red) 원문 바이트 동일이라 한 벌로 양쪽,80엔트리 게이트 0 problems, 진척 80/22,919 | 매핑 한 칸 어긋남을 계기로 「원문과 줄 수가 다르면 거절」 검사 추가; 게이트 시험16건 | 상태: needs_review/미삽입

## 2026-09-20 후속: 본편 대사 첫 4배치 삽입과 두 판본 실행 확인

파이프라인이 끝에서 끝까지 한 바퀴 돌았다: 전수 추출 → 배치 번역 → 게이트 → 빌드 →
제품에서 되읽는 독립 검증 → 두 판본 실행 확인.

배치 001 오퍼레이션 배틀 튜토리얼(아카이브 3/4), 002 내비커스 프로그램 설명(12),
003 넷토 방 아침 장면(443), 004 PET 획득(230). 합계 **137 / 22,919**.
아카이브 3·4 는 **판본마다 역할이 바뀐다**(Blue 는 3 이 튜토리얼, Red 는 4) —
같은 문구를 양쪽 슬롯에 적용하면 두 판본이 덮인다.

채택 제품 BLUE `1a1e2ae1c8140ec1a7591d40ccd9941422be9c1d84f1cc5c295631a4b0dd4bfd`,
RED `b026ddef2a77b8b9eba6e67bfadb20b9b0aabb24a9fea950a16ca8864840e8e6`,
기준본 대비 +9,585바이트. 새 실행 코드·글꼴·advance·VRAM 은 0 이고, 차분은 포인터 9워드와
덧붙인 아카이브 5개뿐이다. **아카이브 12 는 포인터 참조가 5곳**이라 단일 참조만 받던 첫 빌더가
거절했다 — 하나라도 남기면 그 경로만 일본어 사본을 읽는다.

실행 확인은 **화면이 스스로 증명하게** 했다. 제품 ROM 안의 한글 글리프 비트맵으로 기대 줄을
렌더하고, 캡처에서 그 잉크 패턴을 찾는다. 두 판본 각 10개 메시지 16줄이 픽셀 단위로 일치했고
기준선 격자(y=108/122/136, 행간 14px)와 여백(x=51)까지 맞았다.
**글리프 셀 16열 중 advance 밖은 자른다** — 공백 기록이 advance 8 뒤 14·15열에 잉크를 달고
있어서, 안 자르면 공백이 든 줄은 하나도 안 맞는다. 분할 메시지의 이어지는 리터럴은 왼쪽
여백에서 시작하지 않으므로(`「PET」` 뒤에 붙는다) 여백 단언은 여는 리터럴에만 건다.

다음 재개: 배치를 계속 쌓는다. 화면 확인이 바로 되는 것부터 고르면 좋다 — 같은 콜드 경로에
남은 일본어는 **아카이브 8**(메일 알림)인데, 그 아카이브는 ASCII 엔딩 크레딧 줄도 함께 담고
있어 시트에 안 들어간다(시트는 일본어가 든 리터럴만 담는다). PET 메뉴 라벨은 다른 소비자다.
그리고 아직 **넷째 archive54 참조**(BLUE `106DAC` / RED `106E1C`) 분류가 남아 있다.

2026-09-20 | gate-selftest | 원장 검증의 새 귀속 검사들이 발화함을 확인 | 메뉴 설명4종·본편2종 교란이 모두 rc=1, 복원 후 PASS | 교란 시 원장을 다시 만들어야 의미 검사가 바이트/해시 검사에 가려지지 않는다 | 상태: 확인

## 2026-09-20 후속: 본편 배치 011까지 삽입, 저장 형태 결함 수정

배치 005~011을 더해 **1,299 / 22,919**(아카이브 15개)까지 왔다. 도중에 부팅이 죽는 결함을
하나 잡았다 — 빌더가 재배치 아카이브를 **전부 LZ77로 감쌌는데** 이 ROM의 793개 중
**77개는 비압축**이고, 이번 대상 중 **8·12·48·64가 비압축**이다. 아카이브 8은 부팅 경로에서
읽히므로 첫 프레임부터 화면이 검었다.

**정적 검증은 전부 통과했다.** 검증기가 빌드와 같은 가정으로 LZ 해제를 했기 때문이다.
그리고 앞선 4배치 제품에는 **아카이브 12가 이미 깨진 채** 들어가 있었는데 그 화면을
지나가지 않는 경로라 드러나지 않았다. 셋을 고쳤다: 빌더는 원본 플래그대로 저장,
검증기는 **원본 플래그로 되읽고 형태 변경을 거절**, 그리고 `boot_check.py`(콜드 3캡처,
1분)를 빌드 직후 정식 단계로 넣었다. `story_bisect.py`가 배치 부분집합으로 빌드해
범인을 좁힌다(이번엔 005에서 재현됐다).

작성 도구도 둘 늘었다. **`by_source`**(원문 줄 → 번역)로 반복 아카이브를 싸게 쓰고,
**`deferred`**로 뒤섞인 수수께끼 줄을 이유와 함께 원문으로 남긴다. `by_source`를 처음엔
경로로 풀어서 **아카이브 301/303/305/307이 같은 경로에 담은 서로 다른 줄이 한 문장으로
뭉개졌는데**, 결과가 멀쩡한 한국어라 게이트도 왕복도 못 잡았다 — 「작성한 줄이 아무
레코드에도 안 닿으면 거절」 하나가 잡았다. 규칙을 `wording()`으로 떼어 시험 5건으로 잠갔다.

채택 제품 BLUE `d5dc5db911f575f722c7dba2db75517aff38f2fdfb920da015454936e2c77e20`,
RED `9ffc27648f97f85fecb4de3231d99cd6702d444a0ac3a7783ec1df106599759b`.

다음 재개: **배치 012가 작성·폭검사까지 끝나 있다**(아카이브 7, 207건 + 보류 1).
`prepare_story_batch.py --batch 012`부터 이어가면 된다. 그 뒤로 남은 큰 아카이브는
430(218)·278(201)·251(188)·268(180)·17(168)이고, `story_reuse.py`가 이미 번역한 원문을
새 아카이브에 미리 채워 준다. 미번역은 아직 **21,620 레코드**다.

2026-09-20 | story-013 | 배치012·013 삽입 완료 | 진척1,686/22,919(7.4%), 아카이브17개; 제품 BLUE 1adedbe4… / RED d7ef831d…, 포인터31워드·+117,537바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107,11개 메시지18줄 픽셀 일치 | 다음: 배치014(아카이브251, 188건)·015(아카이브278, 201건)가 작성·폭검사까지 끝나 있다 — prepare 부터 이어가면 된다 | 상태: 수용

2026-09-20 | story-022 | 배치014~018·020~022 삽입, 019는 보류 | 진척3,132/22,919(13.7%), 아카이브26개; 제품 BLUE 22bbbae6… / RED c067b904…, 포인터40워드·+218,286바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 새 게이트 둘: 메뉴 선택지 행 폭(check_option_widths.py, 시험9건)과 포인터 클레임 없는 아카이브 거절(prepare) | 다음: 배치023(아카이브429, 130건)이 작성·폭검사까지 끝나 있다 — prepare 부터 이어가면 된다 | 상태: 수용

2026-09-20 | option-width-open-question | 선택지 예산은 「ROM이 같은 선언 폭에서 실제 그리는 가장 넓은 일본어 행」이지 렌더러 상수가 아니다 | positionOption* 의 width 가 몇 px 단위인지는 미확정 — 11·12·14·16 전부 반증됨 | 실기에서 선택지 행의 좌우 끝을 재면 상수를 고정할 수 있고, 그러면 지금 거절되는 표현 몇 개가 되살아난다 | 상태: 미해결(보수적으로 동작 중)

2026-09-20 | story-030 | 배치023~030 삽입 완료 | 진척5,076/22,919(22.1%), 아카이브66개; 제품 BLUE b64d7dcf0f06796d78ccc2e5082f5fb1e6b590edc08bfebe39acfdf06593cdb4 / RED dc8986d2a8538aa90c82f6f278930722714315cf0da0edafaec919180188e76a, 포인터94워드·+356,241바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 새로 얻은 방법: 남은 아카이브를 크기순이 아니라 「레코드 ÷ 새로 쓸 줄」 순으로 훑는다 — 67·70·73·75는 76의 사본이라 497건을 다섯 줄로 덮었다 | 같은 원문이 넓은 자리와 좁은 자리에 함께 쓰이므로(`いいえ`), 번역은 가장 좁은 자리에 맞춰 전역 통일해야 한다 | 다음: 배치031(아카이브427, 127건)이 작성·폭검사까지 끝나 있다 — prepare 부터 이어가면 된다 | 상태: 수용

2026-09-20 | story-034 | 배치031~034 삽입 완료 | 진척5,772/22,919(25.2%); 제품 BLUE fb4064e9429e99995acf711071c814262ba6e8c84886b2e9f499956aba4493c8 / RED 4ea054acacd85b984a1f60887d0fd8151f7fc9d453c9773b129ffcf43d0f14eb, 포인터100워드·+413,013바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 방언 배정 규칙: 인물마다 다른 한국어 방언을 쓰고 겹치지 않게 관리(경상도=배치024 개그 사부、충청도=배치031 관광객) | 다음: 남은 큰 아카이브는 406(104)·63(146, 포인터 없음·보류)이며 대부분 100건 미만으로 잘게 흩어져 있다 | 상태: 수용

2026-09-22 | story-036 | 배치035~036 삽입 완료 | 진척6,175/22,919(26.9%); 제품 BLUE e6ccc492d6d095d9fc8cd8feb8bfa85d42786e25c2c3e1b3965f66a6317f987f / RED 1a4c04fba4d6ad8778f12b3d6ba68b007235bb482875a945f4118005dcd20f50, 포인터104워드·+442,433바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 방언 규칙 정정: 인물별이 아니라 원문 방언별(관서벤→경상도, 가고시마벤→충청도) | 다음: 412·415(197건/신규169)、248(103/101)、247(95/69)、432(94/71) 순으로 남았고 100건 미만으로 잘게 흩어져 있다 | 상태: 수용

2026-09-22 | story-038 | 배치037~038 삽입 완료 | 진척6,570/22,919(28.7%); 제품 BLUE 18abd19df2e652500220a2ac89cf56da21f78deef70f537937a8259bd111ec9b / RED 86fb5db8732a63a77184dc47b3daf9560d1cec702e0feebf487cd569055b9c2a, 포인터108워드·+470,301바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 선택지 폭 미확정의 대가가 처음으로 번역 내용을 깎았다(아카이브412 퀴즈 두 문제) — 실기 측정 우선순위를 올릴 것 | 다음: 432(94/71)·540(89/85)·274(89/80)·710(88/78) 순、100건 미만으로 흩어져 있다 | 상태: 수용

2026-09-24 | story-040 | 배치039~040 삽입 완료 — 진척 30% 돌파 | 6,930/22,919(30.2%); 제품 BLUE eb49c3c99ac240b2bfff40cbbf6672d4a53145ab3fefcd21ad5f9ce086c613a0 / RED 7d9eb384d047bebb7a1ee230171777bed516e1b15e0f0655b084150cc61f7925, 포인터113워드·+494,297바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 본편 전환점(아카이브540 리갈 정체 폭로)과 카레 대결(710)까지 들어갔다 | 다음: 254(82/78)·336(82/66)·103(81/81)·68(80/79)·65(79/79)·74(79/78)·571(77/77) 순、전부 100건 미만 | 상태: 수용

2026-09-24 | story-042 | 배치041~042 삽입 완료 | 진척7,255/22,919(31.7%); 제품 BLUE 4e6fe2e87f4fdc6ae68988a7bcdc5a4310b4d0bc7f05035778cf7ea4fbcf68a6 / RED 9b5c7215071bfe28bfec2517165c7fdcb63c921edda98e869f9d88373fe89903, 포인터117워드·+525,465바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 아카이브68·103은 같은 안내의 양방향이라 어미로 화자를 갈라 둠 | 다음: 65(79)·74(79)·571(77)·나머지는 전부 80건 미만으로 흩어져 있다 | 상태: 수용

2026-09-25 | story-050 | 배치043~050 삽입 완료 | 진척8,265/22,919(36.1%); 제품 BLUE a3718c361159f7d787e6d71b868a22a08d72fb6f2ae9b1b5a7a2d8d56e9f7ea2 / RED bd9fcae4268bdf49fcc421a2ddd6d53f6b9f8fe50d9dfa9851d643f7a63918c2, 포인터153워드·+616,720바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치, 벤치 30케이스 | 중복 우선 정렬로 043~046이 613건을 새 문장 148개로 덮음 — 할인 종료, 잔여 577아카이브는 레코드당 새 문장 0.5~0.7(총 12,129문장) | 아카이브111 스크립트35는 머리 없는 조각(호출부 0건·두 판본 동일)이라 표면 독해로만 옮김 | 포인터 주장 없는 잔여는 56(`デューオ`)·57(`グランプリパワー`)·63(146건): 56·57은 원문4바이트 대 한글8바이트라 제자리 치환도 불가 | 다음: 63(146)·74(79)·99(77)·298(77)·571(77) 순、선택지 행 기하 실측(아카이브412 퀴즈 복구)은 여전히 미착수 | 상태: 수용

2026-09-25 | story-056 | 배치051~056 삽입 완료 | 진척9,495/22,919(41.4%); 제품 BLUE 6adfede18d51c6732708c35669548ae99f16d7d908def47096aa8a22496c7b99 / RED 5ec0432603e32732673e97b993c8184914841fb279c8d98e1f551a9968d94162, 포인터182워드·+735,632바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치, 벤치 30케이스 | 직전 사이클의 "중복 할인 종료" 결론을 배치055가 반증(456건을 새 문장55개로) — 잔여 비율은 직전 배치에 의존하는 값이라 배치마다 순위를 다시 매긴다 | 작성 데이터는 ko0NN.json 으로 분리(heredoc 길이 한계) | 아카이브437은 같은 제안 세 목소리(그대~노라/너~다/자네~일세) | 다음: 배치057 후보(60·318·353·407·486·515, 128건/새문장86) 작성 준비 완료 | 상태: 수용

2026-09-25 | story-060 | 배치057~060 삽입 완료 | 진척10,179/22,919(44.4%); 제품 BLUE a83538db38b4bed64d8ff2829523862b1753eb58948e23c16019e1a91836aa84 / RED 148797f41f2612d111828f08baa3c20dc53f449adc7839947ddd988b5e24e958, 포인터213워드·+789,052바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치, 벤치 30케이스 | `・`(U+30FB)는 게이트가 일본어로 분류 — 가림 기호는 `.`으로 옮기고 가린 글자 수·모양은 유지 | 남은 525개 아카이브는 레코드당 새 문장 0.70~0.76(관찰) | 다음: 배치061(327·385, 112건/새문장84) 작성 준비 완료 | 상태: 수용

2026-09-25 | story-064 | 배치061~064 삽입 완료 | 진척10,752/22,919(46.9%); 제품 BLUE d246bab6a7aaa0873971a4a95c553d29f8d68635675b3cb43ffc4b875aefde54 / RED ecf77120e28cba0010b2beb0466602876b0723a0d2a0e3b045e7c6b9c27312e2, 포인터233워드·+831,328바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치, 벤치 30케이스 | 방언 원장: 경상도=관서벤 화자(024)·충청도=가고시마 관광객(031)·전라도=히무라 아츠키(062); 규칙은 「일본어 방언 하나에 한국어 방언 하나」 | 조사만 있는 줄은 비운다(214/4/1) | 다음: 배치065(128·217·218·408·465·672·756, 129건/새문장94) 작성 준비 완료 | 상태: 수용

2026-09-25 | story-068 | 배치065~068 삽입 완료 | 진척11,274/22,919(49.2%); 제품 BLUE faa431584ef8efd4cc0b0e4e3378e4a0bf94f5a531ecf49f87b5467833bdfdea / RED f10117905f4bdaac74db93d47587de032f1f495278d73fcce60bf83cf1a0a723, 포인터254워드·+871,741바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치, 벤치 30케이스 | 말버릇 보존(샤로 〜ショー·〜チョフ/〜スキー、포레포레) | 다음: 이야기 데이터 퍼즐 표기 불일치 2건 수정(おてんこさま 「해님」↔「오텐코 님」、ドラッキー 드래키3↔드락키36) + 배치069 | 상태: 수용

2026-09-25 | story-069 | 배치069 + 이야기 데이터 퍼즐 표기 정정 | 진척11,394/22,919(49.7%); 제품 BLUE 7dba2e4bc16ed4b1808058d0e7a34854d96773959a9330e75fcb1399705553c6 / RED 7d5868989a0da0c9d3098a67699fe1f9faa0b25627637ea09ec4c2ce841ee39b, 포인터260워드·+881,189바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치, 벤치 30케이스 | おてんこさま 「해님」→「오텐코 님」(미끼 「오코텐 님」)、ドラッキー→드락키 통일 | 용어집 012~017: 퍼즐 아이템 이름(짧은 라벨 아카이브16·62, 미번역)이 따를 이름 | 다음: 용어 일치 검사기(check_glossary_terms.py) 편입 + 발견된 16건(배틀칩9·데이터 도감3·태양의 빛4) 정정 | 상태: 수용

2026-09-25 | story-070 | 용어 일치 게이트 편입 + 배치070 | 진척11,532/22,919(50.3%); 제품 BLUE a2b1ff6f46cb1359f4071e400191ed1470ccd9ffe19080c265d0eef70d613bcc / RED f0d2e1de3025bd75a3cbc1c18e0e86f56b02623dc4cbce86f0250ee728fb4965, 포인터262워드·+892,337바이트 | 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치, 벤치 35케이스 | tools/check_glossary_terms.py: 용어집 원문이 든 줄은 용어집 한국어를 가져야 함(레드선 변형 포함); 정정 전 종료코드1·16건 거절 확인 후 정정 | 원장 검증기에 보고서 PASS·1,000건 이상·용어집 해시·배치 집합 일치를 묶음 | 한계: 용어집 17행 밖은 못 봄 — 배치 TERMS를 용어집으로 옮기면 범위가 넓어짐 | 상태: 수용

2026-09-26 | story-074 | 배치071~074 + 한 글자 연출 전수 설계 + 빈 리터럴 규칙 + 후리가나 이름 | 진척12,059/22,919(52.6%); 제품 BLUE 731cb243bf840ca5ccbd773c24de3ebd7b2a4e79b316c8ab507b1d5c4029bb76 / RED 2b2ea9d843574742d620bf80ebf3daa9d5375b73ef47abdfc80730c821369c86, 포인터277워드·+928,593바이트 | 게이트 PASS(대사12,059·선택지538줄·용어21개1,903회), 벤치36케이스, 정적 검증 판본당12,019(공통11,979+판본 전용40), 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 원장 용어 블록 교란 시험 3/3 거절 | 한 글자 연출: 전수 15·공유 조각7, だ・=그., 나머지 공유 조각은 쉼표 점만(빈 리터럴은 TextPet 이 못 읽음 → 게이트 규칙, 정정 전 10건 거절 확인), 배치033 정정 | 火村=호무라(062 히무라 오독 정정), 후리가나 이름4개 용어집 018~021 | 다음: りょうかい!(록맨→넷토 대답 44곳) 「알겠습니다!」→「알겠어!」 일괄 정정(scratch fix_ryoukai.py 준비) + 배치075(145건)·076(123건) 검사 통과본 투입 | 상태: 수용

2026-09-26 | story-074-정정 | 바로 위 story-074 항목의 「076(123건) 검사 통과본」은 기록 시점에 검사 전이었음 — 실제 첫 검사는 FAIL(494/9/3 폭 189px 초과 1건 + 아직 준비 안 된 075 결정을 재사용하는 5줄 미포함) | 075 준비 후 494/9/3 을 줄여 재검사 PASS(123건) | 교훈: 「검사 통과」는 검사를 돌린 뒤에만 쓴다 | 상태: 정정

2026-09-26 | story-078 | りょうかい! 말높이 정정 + 배치075~078 + 후리가나 이름 재조사 | 진척12,568/22,919(54.8%); 제품 BLUE 545d7eebe15060cc48e632069a0dce8bdb4f50b5ad912349cddad9f0364ae205 / RED 67b0c5a11c64aa77655122d9edd8b9883619ee7936790b1b7d1ac047dafb0ff6, 포인터303워드·+965,169바이트 | 게이트 PASS(대사12,568·선택지539줄·용어26개2,007회), 벤치36케이스, 정적 검증 판본당12,528, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | りょうかい!→「알겠어!」(7배치; 록맨→넷토 대답), 후리가나 이름 8개 전부 용어집(018~025)+リーガル=리갈(026) | 다음: どうする? 「어쩔 텐가?」→「어떡할래?」(배치032, scratch fix_dousuru.py) 후 배치079(123건)·080(154건, 079 준비 후 검사)·081(131건) — 079만 검사 통과 확인됨 | 상태: 수용

2026-09-27 | story-082 | どうする? 말높이 정정 + 배치079~082 | 진척13,103/22,919(57.2%); 제품 BLUE d94d808679df2bf35ea74adea3ea9dc4dd04d0e7b1cf2731c9768d73352c3a99 / RED ad8c71aab03dd95ca1a20639eb6768cd6ed379ba830871fe009efb7a181f2d32, 포인터324워드·+1,009,105바이트 | 게이트 PASS(대사13,103·선택지545줄·용어26개2,065회), 벤치36케이스, 정적 검증 판본당13,063, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치083(134건)·084(123건) 검사 통과본 투입, 085(122건)는 폭 1줄 고친 뒤 083·084 준비 후 재검사 필요(재사용 7줄이 그 둘에 걸림) | 상태: 수용

2026-09-27 | story-086 | 배치083~086 | 진척13,613/22,919(59.4%); 제품 BLUE e4f6eb67ff19215ad89eb80422c8a63c100580a8d2e455970664c26e902a6229 / RED ce4e9d66e9c35d5662f290c7acde047a89dd97a517f5b34cc480a17ba73b4ef3, 포인터349워드·+1,049,095바이트 | 게이트 PASS(대사13,613·선택지551줄·용어26개2,140회), 벤치36케이스, 정적 검증 판본당13,573, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음 주기에 적용할 부류 정정 둘(scratch 준비): 「에리어 N」 띄어쓰기 24줄→「에리어N」(일본어 원문·다수 86줄 기준, fix_area_number.py) / ぶんだん 「분단」9줄→「차단」(다수 14줄, 용어집 027·028, fix_bundan.py); 이어서 배치087(122)·088(116)·089(128) — 087만 단독 검사 통과, 088·089는 선행 배치 준비 후 재검사 | 상태: 수용

2026-09-27 | story-090 | 에리어 번호·차단 정정 + 배치087~090 | 진척14,109/22,919(61.6%); 제품 BLUE 7c5b610be86cdc5cd01a80cf3f58ad88ea1729ea26279e1c7256330c220d4bfc / RED 2f491ea7088ae21220c31a29572c3a1230080be2015acfe98177172bb36ac29c, 포인터375워드·+1,081,647바이트 | 게이트 PASS(대사14,109·선택지551줄·용어28개2,213회), 벤치36케이스, 정적 검증 판본당14,069, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 「롯트 넘버」5줄→「로트 넘버」(048·054·064, 표준 표기; 용어집 029; scratch fix_lot_number.py) 후 배치091(126)·092(110)·093(126) — 091은 단독 검사 통과, 092·093은 앞 배치 준비 후 재검사 | 상태: 수용

2026-09-27 | story-094 | 로트 넘버 정정 + 배치091~094 | 진척14,590/22,919(63.7%); 제품 BLUE 2d214188b9caf36004bb1d40b7d8a3e7f6f790086569e85b2b1fd2ffbbf0215c / RED 370a896c997ff17a4de9d3f517eda3600c83333b97d1675aa8b5837687a701a6, 포인터392워드·+1,117,903바이트 | 게이트 PASS(대사14,590·선택지565줄·용어29개2,299회), 벤치36케이스, 정적 검증 판본당14,550, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치095(125) 단독 검사 통과, 096(119)은 095 준비 후 재검사(재사용 2줄), 097(455·619·428, 123)은 원문 조사만 끝남 | 상태: 수용

2026-09-27 | story-098 | 성불 정정 + 배치095~098 | 진척15,078/22,919(65.8%); 제품 BLUE 7996ca87d118af327678e1cee7a59d8f67e803890fe120a87338df4f633b7e53 / RED 25bab7a2c2944c4bbd5ac148abe28ddbe9d8fc84e49ee3925186ad2f94d2b41f, 포인터403워드·+1,155,123바이트 | 게이트 PASS(대사15,078·선택지567줄·용어31개2,353회), 벤치36케이스, 정적 검증 판본당15,038, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | じょうぶつ/ジョウブツ=성불(용어집 030·031; 정정 전 사본 거절 확인) | 다음: 배치099(460·687·738, 124)·100(89·453·497, 126)·101(280·504·585·653, 124)은 작성 틀 --check 단독 통과(scratch ko099~101.json) — 099부터 차례로 준비하고, 앞 배치 준비 후 뒤 배치를 재검사 | 상태: 수용

2026-09-27 | story-102 | 배치099~102 + 코오리스키 이름 | 진척15,588/22,919(68.0%); 제품 BLUE d1ba218e0f73e703f968bb0b3f43da0b7126d60d4a65bc6bc8aeafeac53746c0 / RED 81f14837190433a84f744923d745d5a6927950c9fce12eba2bf6ffbcf78a21b2, 포인터418워드·+1,194,999바이트 | 게이트 PASS(대사15,588·선택지567줄·용어32개2,412회), 벤치36케이스, 정적 검증 판본당15,548, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 용어집 032 コオリスキー=코오리스키 | 다음: 배치103(249·611·612·721·772, 122)·104(238·448·496·692, 125)·105(294·466·522·525·604·631, 120)은 작성 틀 --check 단독 통과(scratch ko103~105.json) — 103부터 차례로 준비하고, 앞 배치 준비 후 뒤 배치를 재검사 | 상태: 수용

2026-09-27 | story-106 | 배치103~106 + 실행 QA 명령줄 한도 수정 — 진척 70% 돌파 | 진척16,079/22,919(70.2%); 제품 BLUE 9cab1978f70a53f1b54bace5a5afbb375bd5c222068d622c0726e9e59f885592 / RED 4bba3013e695bd7ec15c0e7f260d2ac81e21b9652e2d22f7db82f0ca15c12e9d, 포인터442워드·+1,229,675바이트 | 게이트 PASS(대사16,079·선택지572줄·용어32개2,482회), 벤치36케이스, 정적 검증 판본당16,039, 두 판본 부팅 DRAWS, 콜드 경로 각107/107(가드 888개, 인수 파일), 11개 메시지18줄 픽셀 일치 | 다음: ① 배치018 「유비무환」 둘째 줄 빈칸(・・・ですよ 누락, 레코드 9개) 정정 + 「내용 있는 원문 줄을 비우면 거절(조사 한 글자 줄만 예외)」 게이트 규칙과 시험 ② 배치107(228·759·771, 130)·108(414·565·581, 118)·109(255·284, 130)은 작성 틀 --check 단독 통과(scratch ko107~109.json) — 107부터 차례로 준비하고 뒤 배치 재검사 | 상태: 수용

2026-09-27 | story-110 | 비운 원문 줄 게이트 + 배치107~110 | 진척16,578/22,919(72.3%); 제품 BLUE 5a798c00983319e762920ce67d3afda76bf1c269815b70a10f4da3bd5c99e1bf / RED 5e72b4f9aee4e318e346d8e8761bd4aba165d67c3fa118db47661386367cb12e, 포인터454워드·+1,266,915바이트 | 게이트 PASS(대사16,578·선택지573줄·용어33개2,537회), 벤치38케이스, 정적 검증 판본당16,538, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: ① 유괴범 수수께끼(배치012 보류 literal 8) 해소 — 오른쪽 열부터 세로 읽기(ひろばにいる おじいさんに ききな, 아카이브251의 노인이 메모를 건넴으로 확인)를 한국어 격자 보께아있광／아물버는장／라어지할에(=광장에 있는 할아버지께 물어보아라)로, 힌트 국어 교과서→옛날 책 (scratch fix_riddle_012.py) ② 배치111(546·560·717, 131)·112(124·507·596·727, 107)은 작성 틀 --check 단독 통과(scratch ko111~112.json) — 012 정정 후 111부터 준비 | 상태: 수용

2026-09-27 | story-114 | 유괴범 수수께끼 해소 + 배치111~114 | 진척17,058/22,919(74.4%); 제품 BLUE a6792e08529a4c091d1762a4e7b9c5c71983ab88c61cbe16f7e99a311882d3eb / RED 92e1d906615e65ebea6ef4868d48a4891422d31d38fbd35aca60a5a922fe1b74, 포인터473워드·+1,297,915바이트 | 게이트 PASS(대사17,058·선택지576줄·용어33개2,595회), 벤치38케이스, 정적 검증 판본당17,018, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치115(680·735, 116)·116(559·561·562·563, 101)·117(584·686·740, 125)은 작성 틀 --check 단독 통과(scratch ko115~117.json; 116 은 564 제외, 564 는 배치071) — 115부터 차례로 준비하고 뒤 배치 재검사 | 상태: 수용

2026-09-27 | story-118 | 배치115~118 | 진척17,522/22,919(76.5%); 제품 BLUE 9b14875a2054403ad1b850c87dd315b8acc8b51bf9b58ea26881aff1bcc85fe7 / RED 6d740eed0c2e699b861475196b8b217bce6414cf419d067de40f5b44ab92b8d5, 포인터488워드·+1,328,151바이트 | 게이트 PASS(대사17,522·선택지576줄·용어33개2,645회), 벤치38케이스, 정적 검증 판본당17,482, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 작성 틀(scratch)에 앞선 배치 결정 대조 검사 추가 | 다음: 배치119(521·626·706·730·775, 124)는 작성 틀 --check 단독 통과(scratch ko119.json) — 준비 후 120 이후 계속 | 상태: 수용

2026-09-27 | story-122 | 배치119~122 | 진척17,961/22,919(78.4%); 제품 BLUE 8d27c90600defefc45c598eb3063a2d08c2bfb8593c0e698ce05642b291c0165 / RED 9623e1622d3981d7fa70b9c8a0cb90a184ff51653b91d0dff20efcd8cdc7a212, 포인터499워드·+1,368,523바이트 | 게이트 PASS(대사17,961·선택지577줄·용어33개2,765회), 벤치38케이스, 정적 검증 판본당17,921, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치123(237·411·583, 124)·124(240·259·630·650·695, 121)·125(93·608·764, 124)·126(757·782·788, 120)은 작성 틀 --check 단독 통과(scratch ko123~126.json) — 123부터 차례로 준비하고 뒤 배치 재검사 | 상태: 수용

2026-09-27 | story-126 | 배치123~126 | 진척18,450/22,919(80.5%); 제품 BLUE ee8330f05ebc7cb2758a70b44f5245b9cf255cc28920c8af03b79def22ebf285 / RED 6626a737fcd0e5052a962645932e35f6ba2a60cf652b2fcbceec433b1123ced8, 포인터513워드·+1,405,987바이트 | 게이트 PASS(대사18,450·선택지577줄·용어33개2,827회), 벤치38케이스, 정적 검증 판본당18,410, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치127(518·736, 123)·128(462·467·474·537, 126)·129(131·548·651·769, 127)·130(133·712·733·774, 122)·131(410·724, 128)은 작성 틀 --check 단독 통과(scratch ko127~131.json) — 127부터 차례로 준비하고 뒤 배치 재검사 | 상태: 수용

2026-09-27 | story-130 | 배치127~130 + 이름 갈림 통일 + 레드선 폴백 수정 | 진척18,948/22,919(82.7%); 제품 BLUE 3d79ca3f2b1b4b69e6561ba6fc667d69f0b449886db51370236fb81bc1c4052e / RED 3a546dfa1291cc242a73cae82ff2df6d6bcfb3cf6ffd4bc398417653b380ed38, 포인터527워드 | 게이트 PASS(대사18,948·선택지577줄·용어45개3,191회), 벤치48케이스, 정적 검증 BLUE18,906/RED18,907, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치131(410·724, 128)·132(24·287, 123)은 작성 틀 --check 단독 통과(scratch ko131·132.json, 틀은 키:red 지원판) — 131부터 준비; 후보 133(704·22: 22의 바이러스 이름 キルブー·ウォーラ·マルモコEX 는 번역된 곳이 없어 먼저 정할 것), 503은 differs 16건이라 :red 문구 필요 | 상태: 수용

2026-09-28 | story-134 | 배치131~134 | 진척19,427/22,919(84.8%); 제품 BLUE 53309a4dd40c58885091bb6170c63b8ae48bffc67ece4018bca5cc8405f992a6 / RED c57749a4462391fa56a7e24d10dacf67966c6a29bca1877c8b50468854ef6658, 포인터535워드 | 게이트 PASS(대사19,427·선택지578줄·용어45개3,279회), 벤치48케이스, 정적 검증 BLUE19,385/RED19,386, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치135(463·632, 112)·136(26·720, 111)은 작성 틀 --check 단독 통과(scratch ko135·136.json); 135 준비 전에 タワシ 를 수세미로 통일(배치093 633/4/1 「타와시야」 한 줄, 용어집에 タワシ·たわし 행) — 632 의 「수·세·미?」 연출이 이 결정에 기대고 있음; 남은 differs 27건(53·552·549·551·550)은 작성 틀의 키:red 로 | 상태: 수용

2026-09-28 | story-138 | 배치135~138 + タワシ 통일 | 진척19,857/22,919(86.6%); 제품 BLUE e12aae03422ae3ccd8cb567d18d5c485e85a85e414ff5c962627dcaeedaaed7d / RED 4486a0be4da393207a2ba05fecf8bc36ffe31e1962babb3c08c50ba29f374c21, 포인터543워드 | 게이트 PASS(대사19,857·선택지578줄·용어47개3,344회), 벤치48케이스, 정적 검증 BLUE19,815/RED19,816, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치139(256·766, 97)는 작성 틀 --check 단독 통과(scratch ko139.json) — 139부터 준비; 후보 20·464·700·641; 남은 differs 27건(53·552·549·551·550)은 작성 틀의 키:red | 상태: 수용

2026-09-28 | story-142 | 배치139~142 | 진척20,229/22,919(88.3%); 제품 BLUE 4ec947bfd89a029169fec307f52ddb9fde996ae078d153c1815f54d439c82579 / RED 835ee20d6f9f2ced60578a42411c946b2095ce9779462fe37710878ade650dc5, 포인터551워드 | 게이트 PASS(대사20,229·선택지578줄·용어47개3,380회), 벤치48케이스, 정적 검증 BLUE20,187/RED20,188, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치143(426·599, 87)은 작성 틀 --check 단독 통과(scratch ko143.json) — 143부터 준비; 후보 485·758·253·28·669·751; 남은 differs 27건(53·552·549·551·550)은 작성 틀의 키:red | 상태: 수용

2026-09-28 | story-146 | 배치143~146 + 칩 이름 통일 | 진척20,563/22,919(89.7%); 제품 BLUE 21d299e7dac740a654db592b286ba7b46a84c1447854f69e9fd0a55db1182de0 / RED 4002d7f2d219414005f43019ca85d9a7d05dd9dc67128a57e80f572023850700, 포인터559워드 | 게이트 PASS(대사20,563·선택지578줄·용어47개+칩181개4,303회), 벤치49케이스, 정적 검증 BLUE20,521/RED20,522, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치147(53·549·550·551·552, 65 — differs 25건을 키:red 로)은 작성 틀 --check 단독 통과(scratch ko147.json) — 147부터 준비; 이것으로 differs 는 전부 끝남 | 상태: 수용

2026-09-28 | story-150 | 배치147~150 | 진척20,947/22,919(91.4%); 제품 BLUE 56f089d2ec25855c5b695b5dc6e3b691a1713d9e4349459e4ff4818d970e4df4 / RED d49ae190b8e43e7e495d7dab388e1dffe1898c4e11f11d253faae802998f0981, 포인터575워드 | 게이트 PASS(대사20,947·선택지578줄·용어47개+칩181개4,410회), 벤치49케이스, 정적 검증 BLUE20,902/RED20,905, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치151(257·277·592, 95)·152(331·703·747, 90)은 작성 틀 --check 단독 통과(scratch ko151·152.json) — 151부터 준비; 남은 약 1,960건은 30건 안팎 아카이브라 배치마다 3~4개씩 | 상태: 수용

2026-09-28 | story-154 | 배치151~154 | 진척21,354/22,919(93.2%); 제품 BLUE 70454a2ba5c7b17390b20f5ba6f6c28f6989977c24849b94bd45cfc8f6acf44c / RED 54fe0589017921bd663455caad19ac4ed3120bb165c1ff391615443be0e58624, 포인터589워드 | 게이트 PASS(대사21,354·선택지578줄·용어47개+칩181개4,473회), 벤치49케이스, 정적 검증 BLUE21,309/RED21,312, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치155(569·628·715·732)·156(449·475·625·750)·157(134·644·661·708)·158(61·130·135·553·690)은 scratch ko155~158.json 초안(네 개 모두 --check 단독 통과·서로 충돌 0) — 155부터 준비; 159(276·451·481·699·707·780) 초안도 있음(씨앗 2줄이 155~158 준비 뒤에 채워짐); 남은 약 1,160건은 30건 이하 아카이브 | 상태: 수용

2026-09-28 | story-158 | 배치155~158 | 진척21,765/22,919(95.0%); 제품 BLUE 6264c87770ed5f9f4929dd6de5697dfaa6b174863f666d5426e3e994cb3874f9 / RED 62b6489dd9d12f810da5c063413e9f77d9015b342dacd2afc147369b48f07bdc, 포인터606워드 | 게이트 PASS(대사21,765·선택지578줄·용어47개+칩181개4,528회), 벤치49케이스, 정적 검증 BLUE21,720/RED21,723, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: ① 아카이브9·10 보류 수수께끼 해소 — 거꾸로 읽기 びなのりどみ／んさありえんうた=みどりのナビ タウンエリア3、나선 읽기(오른쪽 위에서 시계 방향) がしてみるは／さ!なだんな／をかなのばた=はなたばのなかをさがしてみるんだな! — 원문 글자를 남김없이 써서 문장이 되므로 해독 확정 ② 딸꾹질 표기 통일(ヒック 9건 중 히끅 3건: 032·039·157의 うぃ~、ヒック) ③ 배치159(276·451·481·699·707·780, 97)·160(273·536·544·597·600·660·745, 96)·161(127·634·648·719·768, 85)은 scratch ko159~161.json 초안, 셋 다 --check 통과 — 159부터 준비 | 상태: 수용

2026-09-28 | story-162 | 배치159~162+수수께끼 해소 | 진척22,144/22,919(96.6%); 제품 BLUE 49fda6c1604528768021467914b8034028739691fbef48e269c11e9213299120 / RED 4ae757cffb2cd4521da59e67583e22154d787202685c80edc878cc6f15acde9f, 포인터638워드 | 게이트 PASS(대사22,144·선택지578줄·용어49개+칩181개4,611회), 벤치51케이스, 정적 검증 BLUE22,099/RED22,102, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 남은 약 630건(보류 63번 146건 제외)을 작은 아카이브로 계속 — 저작 틀은 author/patch 스크립트 쌍, patch 빠뜨리면 앞 배치 메타데이터가 섞인다 | 상태: 수용

2026-09-28 | story-166 | 배치163~166 | 진척22,433/22,919(97.9%); 제품 BLUE f918be03302cc70c0a3907174c2513d6dd5f477a0df06f9416246037dcdd1e0e / RED 5a07b9ee7c9ca4e10ed16135f18e1fbfc6d4d2c1ddba3e71738ef2a6128eeaf7, 포인터655워드 | 게이트 PASS(대사22,433·선택지578줄·용어49개+칩181개4,665회), 벤치51케이스, 정적 검증 BLUE22,388/RED22,391, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 남은 약 340건(보류 63번 146건·56·57 제외)은 1~10줄 아카이브 | 상태: 수용

2026-09-28 | story-170 | 배치167~170 | 진척22,681/22,919(99.0%); 제품 BLUE feb301fedcaea0f64237208d800c095855cf4ed7876a5828136b99b2ecc41eb4 / RED 15c8339c6972d5e1a123a9cbc9050dba9663d74d8cb90ed205dcae4692c6a33c, 포인터701워드 | 게이트 PASS(대사22,681·선택지578줄·용어49개+칩181개4,694회), 벤치51케이스, 정적 검증 BLUE22,636/RED22,639, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 배치171(남은 소형 44개 아카이브 90건)은 scratch ko171.json, --check 통과; 그 뒤 남는 건 보류 63번 146건·도달 불가 56·57 | 상태: 수용

2026-09-28 | story-171 | 배치171 | 진척22,771/22,919(99.4%); 제품 BLUE a66858e3cf0789f3097355d7e68b2f411ef2db991b0d3edb18f47980881fadd1 / RED 5f21bc817bc953537d04115babda688eeabd7ea675a645c62b3fb7f274192c18, 포인터914워드 | 게이트 PASS(대사22,771·선택지578줄·용어49개+칩181개4,709회), 벤치51케이스, 정적 검증 BLUE22,726/RED22,729, 두 판본 부팅 DRAWS, 콜드 경로 각107/107, 11개 메시지18줄 픽셀 일치 | 다음: 보류 아카이브63(146건) 사유 재검토; 56·57은 도달 불가; 그다음 선택지 폭 실측·전체 통과 QA | 상태: 수용

2026-10-04 | ui-labels-1004 | 사용자 스크린샷 대응: 메뉴 글꼴·그림 라벨·메일·크레딧 | 제품 BLUE af114921b5e4b09ab7a91a79f54eb73d18aabea4a4c9cc1b4051e33c000f9de1 / RED f97bfc2c8c0a3afc9b5e1267f5761d1edb29497fece45cac1448ab490a6c2453 | 메뉴 타일 글꼴을 EXE1 한글판 8×16 글리프로(tools/exe1k_hangul.py, 사용자 선택: EXE3처럼); 칩 폴더 v2 + 아카이브42(칩 256~310)·통신 화면 캐시 초기화; PET 메뉴 그림 라벨 8개(tools/pet_labels.py)·록맨 탭 머리말 3개(tools/tab_labels.py) 재작화; 메일 결함 수정 — 한국어 아카이브7(17,492B)이 0x02028000 의 12,288B 자리를 넘쳐 아카이브6에 덮였음 → 6을 0x0202C800 으로, RAM 한도 게이트(tools/ram_budgets.py); ROM 비례폭 렌더러 F9 FC 한글 처리기(tools/rom_renderer_hangul.py, 반환은 pop {pc}); 메뉴 빌더 압축 아카이브·명령 낀 라벨(목록 형식)·[MB] 토큰 지원; 번역 추가: 통신 메뉴·록맨 상태·도감 탭·폴더 이름·가방·프로그램 40·메일 머리 101·크레딧 70 | 정적 검증 PASS, 단위 테스트 7종 OK, 두 판본 부팅 DRAWS, 콜드 107/107, 사용자 세이브(레드선)로 PET·폴더·록맨·통신·도감·메일 화면 확인 | 다음: 압축 라벨 4(트레이닝)·15(P.A 메모)·61(지역 이름)은 도달 가능한 세이브 필요; 187·193·141~149 미확인; 크레딧·프로그램 이름은 화면 미확인; 블루문 화면 확인은 블루문 세이브 필요 | 상태: needs_review
