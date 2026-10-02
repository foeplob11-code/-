# 우서 월드 (Useo World) — 온라인 2D 픽셀 상황극 게임

여러 명이 같은 도시에 접속해 돌아다니고, 채팅하고, 음성으로 대화하고, 맵을 함께 꾸미는 멀티플레이 상황극 게임.

- 2D + 픽셀, Canvas 렌더
- 성별 기반 교복 고등학생 기본 캐릭터 + 픽셀로 옷/악세사리 커스터마이즈
- 도시/학교/상점 기본맵 + 모든 블록을 쓰는 맵 에디터(실시간 공유 편집)
- 실시간 멀티플레이(위치/채팅/외형 동기화)
- WebRTC 실시간 음성 채팅 + TTS 읽기
- 한국어 / English / 日本語

## 내 PC에서 실행 (혼자 또는 같은 와이파이)
```bash
node server.js
```
- 이 PC에서: `http://localhost:4173`
- 같은 와이파이의 친구: `http://<내-PC-IP>:4173` (예: `http://192.168.0.5:4173`)
  - 내 IP 확인: Windows `ipconfig` → IPv4 주소

## 인터넷에 출시(전 세계 친구와 플레이)

### 방법 A — 지금 당장 (배포 없이, 무료, HTTPS) ⚡ 추천
1. 게임 서버 실행: `node server.js`
2. 새 터미널에서 터널 실행 (둘 중 하나):
   - **Cloudflare Tunnel**: `cloudflared tunnel --url http://localhost:4173`
   - **ngrok**: `ngrok http 4173`
3. 출력되는 `https://...` 주소를 친구에게 공유 → 끝.
   - HTTPS라서 🎤 **음성 채팅도 동작**합니다.

### 방법 B — 24시간 켜진 서버로 영구 배포 (무료 티어)
이 폴더를 GitHub에 올린 뒤 아래 중 하나에 연결하면 자동 빌드됩니다.
`process.env.PORT`를 이미 사용하므로 **추가 설정 없이** 그대로 배포됩니다.

| 호스트 | 방법 | WebSocket | HTTPS(음성) |
|---|---|---|---|
| **Render** | New → Web Service → 이 repo 연결 (Start: `node server.js`) | ✅ | ✅ |
| **Railway** | New Project → Deploy from repo | ✅ | ✅ |
| **Fly.io** | `fly launch` → `fly deploy` | ✅ | ✅ |
| **Replit** | Import → Run → Deploy | ✅ | ✅ |

> 셋 다 `npm start`(= `node server.js`)를 자동 인식합니다. 의존성이 없어 빌드도 빠릅니다.

## 조작
- 이동: WASD / 방향키
- 메뉴: ESC (위에서 두 번째 = 설정)
- 채팅: Enter
- 맵 에디터: 좌클릭 칠하기 · 우클릭 지우기 · 방향키 화면 이동
- 음성 채팅: 채팅창의 📞 버튼 (온라인 + HTTPS/localhost 필요)

## 구조
- `index.html`, `style.css`, `game.js` — 클라이언트(게임)
- `server.js` — 정적 파일 + WebSocket 멀티플레이 + WebRTC 시그널링 (의존성 0)

## 3D 사계절 에셋 (Unity)
`UnityProject/` 폴더는 사실적인 사계절 디오라마 타일과 소품 팩을 담은 별도의 Unity 프로젝트입니다.
Unity Hub에서 이 폴더를 열면 데모 씬이 자동으로 만들어집니다. 자세한 내용은 [`UnityProject/README.md`](UnityProject/README.md).
