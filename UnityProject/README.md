# 사계절 에셋 — Unity 프로젝트

Blender로 만든 사실적인 사계절 디오라마 타일 4개와 소품 팩을 Unity 프로젝트로 옮긴 것.
열면 데모 씬이 자동으로 만들어지고, 키 하나로 계절을 바꿔 볼 수 있다.

![four seasons](Docs/seasons_overview.png)

## 열기

1. **Unity Hub → Add → Add project from disk → 이 `UnityProject` 폴더** 선택.
   - 기준 버전은 Unity 6 (`6000.0.23f1`). 다른 Unity 6 / 2022.3 LTS로 열어도 된다
     (Hub가 버전을 물으면 설치된 버전을 고르면 됨).
2. 처음 열 때 Package Manager가 **glTFast**(`com.unity.cloud.gltfast`, Unity 공식 glTF 임포터)를
   자동으로 설치하고 `.glb` 두 개를 임포트한다.
3. 임포트가 끝나면 `Assets/Seasons/Scenes/Seasons.unity`가 **자동으로 생성되어 열린다.**
   안 열리면 메뉴 **Seasons → Build Demo Scene**.
4. ▶ Play.

> glTFast 버전(`Packages/manifest.json`의 `6.8.0`)을 찾지 못한다는 오류가 나면
> Package Manager → **+ → Add package by name → `com.unity.cloud.gltfast`** 로 최신 버전을 설치하면 된다.

## 조작 (Play 모드)

| 키 / 마우스 | 동작 |
|---|---|
| `1` `2` `3` `4` | 봄 / 여름 / 가을 / 겨울 타일만 보기 (계절별 태양·하늘·안개로 바뀜) |
| `0` | 네 계절 나란히 보기 |
| `P` | 소품 팩 보기 |
| 우클릭(또는 좌클릭) 드래그 | 회전 |
| 휠클릭 드래그 / Shift + 드래그 | 이동 |
| 휠 | 줌 |
| `WASD` / 방향키 | 시점 이동 |
| `H` | 도움말 숨기기 |

## 들어 있는 것

| 경로 | 내용 |
|---|---|
| `Assets/Seasons/Models/realistic_seasons.glb` | 7 m × 7 m 타일 4개 (`Spring_Tile` … `Winter_Tile`), 약 31만 폴리곤, 텍스처 포함 |
| `Assets/Seasons/Models/realistic_props.glb` | 소품 22종 (`Prop_*`), 약 6만 폴리곤, 가로등 점광원 포함 |
| `Assets/Seasons/Scripts/SeasonSwitcher.cs` | 계절 전환 + 계절별 조명 프리셋(인스펙터에서 수정 가능) |
| `Assets/Seasons/Scripts/OrbitCamera.cs` | 회전·이동·줌 카메라 |
| `Assets/Seasons/Scripts/InputCompat.cs` | 구 Input Manager / 새 Input System 둘 다 지원 |
| `Assets/Seasons/Editor/SeasonsSceneBuilder.cs` | 데모 씬 생성기 (메뉴 `Seasons`) |
| `Blender/` | 에셋 생성 스크립트 (Unity는 이 폴더를 무시함) |
| `Docs/` | Blender 렌더 이미지 |

씬 생성기는 GLB에 같이 들어 있는 Blender 카메라와 태양은 꺼 두고, Unity용 태양(Directional Light,
소프트 섀도)과 카메라를 새로 만든다. 프로젝트 색 공간은 Linear로, 그림자 거리는 최소 90 m로 늘린다.

## 타일

| 봄 Spring | 여름 Summer | 가을 Autumn | 겨울 Winter |
|---|---|---|---|
| ![spring](Docs/spring_tile.png) | ![summer](Docs/summer_tile.png) | ![autumn](Docs/autumn_tile.png) | ![winter](Docs/winter_tile.png) |
| 벚꽃 만개, 들꽃, 떨어진 꽃잎 | 짙은 잎, 키 큰 풀, 부들, 연잎 | 단풍, 마른 풀, 낙엽, 버섯, 호박 | 눈 덮인 가지·가문비·바위, 얼어붙은 연못, 고드름 |

- 흙 단면은 유기층 → 표토 → 점토층 → 풍화암층, 바위는 쪼개진 면이 있는 화강암(광물 입자·균열·지의류).
  봄~가을에는 바위 윗면에 이끼, 겨울에는 눈이 쌓인다.
- 잎·꽃·솔잎은 알파 클립 카드(glTF `MASK`), 잔디는 실제 블레이드 메시.
- 단위 미터, 지형 윗면 ≈ y 0, 흙 단면 바닥 y = −1.4.

![soil and rock close-up](Docs/spring_closeup.png)

## 소품 팩

![props trees](Docs/props_trees.png)

| 종류 | 소품 |
|---|---|
| 나무 | 자작나무 4계절, 관목 4계절 |
| 건물 | 통나무 오두막, 돌 우물, 아치형 나무 다리 (각각 일반 + 겨울) |
| 작은 소품 | 벤치(+겨울), 가로등, 장작더미(+겨울), 건초 더미, 디딤돌, 눈사람 |

각 소품의 루트는 `Prop_<이름>` 오브젝트라 따로 떼어 프리팹으로 만들기 쉽다.

## 에셋 다시 만들기 (Blender)

`Blender/realistic_seasons.py`(타일)와 `Blender/realistic_props.py`(소품, 앞 파일의 도구를 재사용)를
Blender 5.x Scripting 탭에서 실행한 뒤 glTF Binary(`.glb`)로 내보내 `Assets/Seasons/Models/`에 덮어쓰면 된다.
텍스처는 전부 스크립트가 직접 합성한 이미지라 외부 파일이 필요 없다.
