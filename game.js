/* =========================================================
   우서 월드 - 상황극 게임 (2D + 픽셀, Canvas)
   - 맵 에디터(모든 블록) / 캐릭터 픽셀 커스터마이즈
   - 성별 기반 기본 캐릭터(교복 고등학생)
   - 도시/학교/상점 기본맵 / 이름·언어 / 채팅 + 보이스
   ========================================================= */
(function () {
  'use strict';

  /* ---------------- 다국어 ---------------- */
  const I18N = {
    ko: {
      _name: '한국어',
      tagline: '나만의 도시에서 펼치는 상황극',
      lang: '언어', nameLabel: '이름', namePh: '캐릭터 이름 입력',
      genderLabel: '성별', male: '남자', female: '여자',
      start: '시작하기', continue: '이어하기',
      startHint: '성별에 따라 교복 입은 고등학생으로 시작해요. 모든 건 나중에 바꿀 수 있어요.',
      hud: 'ESC: 메뉴   WASD/방향키: 이동   Enter: 채팅',
      menuTitle: '메뉴', resume: '계속하기', settings: '설정',
      charEdit: '캐릭터 꾸미기', mapEdit: '맵 만들기', chat: '채팅',
      save: '저장하기', toTitle: '처음으로',
      volume: '소리 크기', tts: '음성 읽기(TTS)', mic: '음성 입력(마이크)',
      on: '켜짐', off: '꺼짐',
      controlsHelp: '조작: 이동 WASD/방향키 · 메뉴 ESC · 채팅 Enter · 맵 에디터에서 좌클릭 칠하기, 우클릭 지우기.',
      wipe: '저장 초기화', back: '돌아가기',
      skin: '피부', hair: '머리', layer: '레이어',
      clothes: '옷', accessory: '악세사리',
      tool: '도구', pen: '펜', erase: '지우개', fill: '채우기',
      color: '색', addColor: '색 추가', clearLayer: '레이어 비우기',
      random: '랜덤', apply: '적용하기',
      charCanvasHint: '클릭/드래그로 픽셀을 찍어 옷·악세사리를 만들어요.',
      resetCity: '도시 복원', clearMap: '맵 비우기', done: '완료',
      mapHint: '좌클릭: 칠하기 · 우클릭: 지우기 · 방향키: 화면 이동',
      send: '전송', chatPh: '메시지 입력...',
      saved: '저장되었어요!', applied: '캐릭터가 적용되었어요!',
      wiped: '저장이 초기화되었어요.', mapSaved: '맵이 저장되었어요!',
      micNo: '이 브라우저는 음성 입력을 지원하지 않아요.',
      micHttp: '음성 입력은 로컬 서버(localhost) 또는 https에서 동작해요.',
      npcs: ['민준', '서연', '하준', '지우', '가게 주인', '선생님'],
      npcLines: [
        '안녕! 오늘 학교 어땠어?', '우와, 그 옷 새로 산 거야?',
        '상점에 신상 들어왔대!', '같이 옥상 갈래?',
        '오늘 날씨 진짜 좋다.', '방과 후에 뭐 할 거야?'
      ],
      narrator: '내레이터',
      welcome: '에 도착했다. 도시를 자유롭게 돌아다녀 보자.',
      online: '온라인', offline: '오프라인',
      sysJoinedRoom: '온라인 월드에 접속했어요.', sysEnter: ' 님이 입장했어요.', sysLeave: ' 님이 나갔어요.',
      needOnline: '먼저 온라인에 접속하세요.', voiceOn: '음성 채팅 켜짐',
      micDenied: '마이크 권한이 거부됐어요.',
      voiceTitle: '음성 채팅'
    },
    en: {
      _name: 'English',
      tagline: 'Roleplay adventures in your own city',
      lang: 'Language', nameLabel: 'Name', namePh: 'Enter character name',
      genderLabel: 'Gender', male: 'Male', female: 'Female',
      start: 'Start', continue: 'Continue',
      startHint: 'You start as a high-school student in uniform based on gender. Everything is changeable later.',
      hud: 'ESC: Menu   WASD/Arrows: Move   Enter: Chat',
      menuTitle: 'Menu', resume: 'Resume', settings: 'Settings',
      charEdit: 'Customize Character', mapEdit: 'Map Editor', chat: 'Chat',
      save: 'Save', toTitle: 'Main Menu',
      volume: 'Volume', tts: 'Voice (TTS)', mic: 'Voice input (Mic)',
      on: 'ON', off: 'OFF',
      controlsHelp: 'Controls: Move WASD/Arrows · Menu ESC · Chat Enter · In map editor left-click paint, right-click erase.',
      wipe: 'Reset Save', back: 'Back',
      skin: 'Skin', hair: 'Hair', layer: 'Layer',
      clothes: 'Clothes', accessory: 'Accessory',
      tool: 'Tool', pen: 'Pen', erase: 'Eraser', fill: 'Fill',
      color: 'Color', addColor: 'Add color', clearLayer: 'Clear layer',
      random: 'Random', apply: 'Apply',
      charCanvasHint: 'Click/drag to place pixels for clothes & accessories.',
      resetCity: 'Restore City', clearMap: 'Clear Map', done: 'Done',
      mapHint: 'Left: paint · Right: erase · Arrows: pan',
      send: 'Send', chatPh: 'Type a message...',
      saved: 'Saved!', applied: 'Character applied!',
      wiped: 'Save reset.', mapSaved: 'Map saved!',
      micNo: 'This browser does not support voice input.',
      micHttp: 'Voice input needs localhost or https.',
      npcs: ['Minjun', 'Seoyeon', 'Hajun', 'Jiwoo', 'Shopkeeper', 'Teacher'],
      npcLines: [
        'Hey! How was school today?', 'Whoa, is that a new outfit?',
        'The shop got new stuff!', 'Wanna go to the rooftop?',
        'The weather is so nice today.', 'What are you doing after class?'
      ],
      narrator: 'Narrator',
      welcome: ' has arrived. Wander the city freely.',
      online: 'Online', offline: 'Offline',
      sysJoinedRoom: 'Connected to the online world.', sysEnter: ' joined.', sysLeave: ' left.',
      needOnline: 'Connect online first.', voiceOn: 'Voice chat ON',
      micDenied: 'Microphone blocked.',
      voiceTitle: 'Voice chat'
    },
    ja: {
      _name: '日本語',
      tagline: '自分だけの街で繰り広げるロールプレイ',
      lang: '言語', nameLabel: '名前', namePh: 'キャラ名を入力',
      genderLabel: '性別', male: '男', female: '女',
      start: 'はじめる', continue: 'つづきから',
      startHint: '性別に応じて制服の高校生で始まります。あとで全部変えられます。',
      hud: 'ESC: メニュー   WASD/矢印: 移動   Enter: チャット',
      menuTitle: 'メニュー', resume: '再開', settings: '設定',
      charEdit: 'キャラ編集', mapEdit: 'マップ作成', chat: 'チャット',
      save: 'セーブ', toTitle: 'タイトルへ',
      volume: '音量', tts: '音声読み上げ', mic: '音声入力(マイク)',
      on: 'ON', off: 'OFF',
      controlsHelp: '操作: 移動 WASD/矢印 · メニュー ESC · チャット Enter · マップ編集 左クリックで描く、右クリックで消す。',
      wipe: 'セーブ初期化', back: 'もどる',
      skin: '肌', hair: '髪', layer: 'レイヤー',
      clothes: '服', accessory: 'アクセサリー',
      tool: '道具', pen: 'ペン', erase: '消しゴム', fill: '塗り',
      color: '色', addColor: '色を追加', clearLayer: 'レイヤーを消す',
      random: 'ランダム', apply: '適用',
      charCanvasHint: 'クリック/ドラッグで服やアクセを描けます。',
      resetCity: '街を復元', clearMap: 'マップを消す', done: '完了',
      mapHint: '左:描く · 右:消す · 矢印:画面移動',
      send: '送信', chatPh: 'メッセージを入力...',
      saved: 'セーブしました！', applied: 'キャラを適用しました！',
      wiped: 'セーブを初期化しました。', mapSaved: 'マップを保存しました！',
      micNo: 'このブラウザは音声入力に対応していません。',
      micHttp: '音声入力は localhost か https で動作します。',
      npcs: ['ミンジュン', 'ソヨン', 'ハジュン', 'ジウ', '店主', '先生'],
      npcLines: [
        'やあ！今日の学校どうだった？', 'わ、その服新しいの？',
        'お店に新商品が入ったって！', '屋上行かない？',
        '今日いい天気だね。', '放課後なにするの？'
      ],
      narrator: 'ナレーター',
      welcome: 'が到着した。街を自由に歩こう。',
      online: 'オンライン', offline: 'オフライン',
      sysJoinedRoom: 'オンラインワールドに接続しました。', sysEnter: ' さんが入室しました。', sysLeave: ' さんが退室しました。',
      needOnline: '先にオンライン接続してください。', voiceOn: 'ボイスチャット ON',
      micDenied: 'マイクがブロックされています。',
      voiceTitle: 'ボイスチャット'
    }
  };
  let lang = 'ko';
  const t = (k) => (I18N[lang] && I18N[lang][k] != null ? I18N[lang][k] : (I18N.en[k] != null ? I18N.en[k] : k));

  /* ---------------- 저장 ---------------- */
  const SAVE_KEY = 'useo_world_v1';
  function persist() {
    try {
      localStorage.setItem(SAVE_KEY, JSON.stringify({
        name: G.name, lang,
        settings: G.settings,
        character: {
          gender: char.gender, skin: char.skin, hair: char.hair,
          clothes: char.clothes, acc: char.acc
        },
        world: { w: world.w, h: world.h, tiles: Array.from(world.tiles) },
        player: { tx: Math.round(player.px / TILE), ty: Math.round(player.py / TILE) }
      }));
    } catch (e) { /* localStorage 차단 환경 무시 */ }
  }
  function loadSave() {
    try { return JSON.parse(localStorage.getItem(SAVE_KEY) || 'null'); }
    catch (e) { return null; }
  }
  function hasSave() { return !!loadSave(); }

  /* ---------------- 타일(블록) ---------------- */
  const TILE = 64;          // 화면상 한 블록 픽셀 크기(고해상 픽셀아트)
  const TILES = [];
  function deftile(ko, en, ja, solid, draw) { TILES.push({ ko, en, ja, solid, draw }); return TILES.length - 1; }
  function tname(i) { const x = TILES[i]; return x[lang] || x.en; }

  // 그리기 헬퍼: 16x16 가상 격자
  function mk(draw) {
    return function (ctx, X, Y, S) {
      const u = S / 16;
      const r = (gx, gy, gw, gh, c) => { ctx.fillStyle = c; ctx.fillRect(X + gx * u, Y + gy * u, gw * u, gh * u); };
      draw(r, X, Y, S, u);
    };
  }

  const GRASS = deftile('잔디', 'Grass', '草', false, mk((r) => {
    r(0, 0, 16, 16, '#5fa84f'); r(2, 3, 1, 2, '#4f9441'); r(6, 6, 1, 2, '#4f9441');
    r(11, 2, 1, 2, '#6cba5b'); r(13, 9, 1, 2, '#4f9441'); r(4, 12, 1, 2, '#6cba5b');
  }));
  const ROAD = deftile('도로', 'Road', '道路', false, mk((r) => {
    r(0, 0, 16, 16, '#3b3f45'); r(7, 1, 2, 3, '#d8c24a'); r(7, 7, 2, 3, '#d8c24a'); r(7, 13, 2, 3, '#d8c24a');
  }));
  const SIDEWALK = deftile('보도', 'Sidewalk', '歩道', false, mk((r) => {
    r(0, 0, 16, 16, '#b9b2a3'); r(0, 7, 16, 1, '#9b9485'); r(7, 0, 1, 16, '#9b9485');
  }));
  const CROSS = deftile('횡단보도', 'Crosswalk', '横断歩道', false, mk((r) => {
    r(0, 0, 16, 16, '#3b3f45'); for (let i = 0; i < 16; i += 4) r(i, 0, 2, 16, '#e9e9e9');
  }));
  const BWALL = deftile('건물 벽', 'Building Wall', '建物の壁', true, mk((r) => {
    r(0, 0, 16, 16, '#8a8f98'); r(0, 5, 16, 1, '#6f747d'); r(0, 11, 16, 1, '#6f747d'); r(7, 0, 1, 16, '#6f747d');
  }));
  const BWIN = deftile('건물 창문', 'Building Window', '建物の窓', true, mk((r) => {
    r(0, 0, 16, 16, '#8a8f98'); r(2, 2, 5, 5, '#7fd1ff'); r(9, 2, 5, 5, '#7fd1ff');
    r(2, 9, 5, 5, '#7fd1ff'); r(9, 9, 5, 5, '#7fd1ff');
  }));
  const ROOF = deftile('지붕', 'Roof', '屋根', true, mk((r) => {
    r(0, 0, 16, 16, '#7a4a3a'); r(0, 0, 16, 4, '#8d5848'); for (let i = 0; i < 16; i += 4) r(i, 5, 1, 11, '#633a2d');
  }));
  const DOOR = deftile('문', 'Door', 'ドア', false, mk((r) => {
    r(0, 0, 16, 16, '#8a8f98'); r(4, 3, 8, 13, '#5a3a26'); r(5, 4, 6, 12, '#6e4a30'); r(9, 9, 1, 2, '#e8c558');
  }));
  const SCHOOL = deftile('학교 벽', 'School Wall', '校舎の壁', true, mk((r) => {
    r(0, 0, 16, 16, '#cdb48c'); r(0, 6, 16, 1, '#b39a72'); r(2, 2, 4, 4, '#a8d8ff'); r(10, 2, 4, 4, '#a8d8ff');
  }));
  const SCHOOLSIGN = deftile('학교 간판', 'School Sign', '学校の看板', true, mk((r) => {
    r(0, 0, 16, 16, '#cdb48c'); r(2, 4, 12, 8, '#2c4a8a'); r(4, 6, 8, 1, '#fff'); r(4, 8, 8, 1, '#fff');
  }));
  const SHOP = deftile('상점 벽', 'Shop Wall', '店の壁', true, mk((r) => {
    r(0, 0, 16, 16, '#9a6fb0'); r(0, 0, 16, 3, '#7a4f90'); r(2, 6, 12, 8, '#ffe7a8'); r(2, 6, 12, 8, '#ffe7a8');
    r(3, 7, 4, 6, '#caa2e0'); r(9, 7, 4, 6, '#caa2e0');
  }));
  const SHOPSIGN = deftile('상점 간판', 'Shop Sign', '店の看板', true, mk((r) => {
    r(0, 0, 16, 16, '#9a6fb0');
    for (let i = 0; i < 16; i += 4) { r(i, 4, 2, 5, '#ff5d7a'); r(i + 2, 4, 2, 5, '#fff'); }
    r(3, 10, 10, 4, '#3a2050');
  }));
  const TREE = deftile('나무', 'Tree', '木', true, mk((r) => {
    r(0, 0, 16, 16, '#5fa84f'); r(7, 10, 2, 5, '#6b4a2c');
    r(4, 2, 8, 8, '#2f7d3a'); r(3, 4, 10, 5, '#3a9147'); r(6, 1, 4, 3, '#3a9147');
  }));
  const FLOWER = deftile('꽃밭', 'Flowers', '花畑', false, mk((r) => {
    r(0, 0, 16, 16, '#5fa84f'); r(3, 4, 2, 2, '#ff6b8a'); r(8, 3, 2, 2, '#ffd24a');
    r(11, 9, 2, 2, '#7e8bff'); r(5, 11, 2, 2, '#ff6b8a');
  }));
  const BUSH = deftile('덤불', 'Bush', '茂み', true, mk((r) => {
    r(0, 0, 16, 16, '#5fa84f'); r(2, 6, 12, 8, '#357d3f'); r(4, 4, 8, 4, '#3f9149'); r(6, 8, 2, 2, '#2c6b34');
  }));
  const WATER = deftile('물', 'Water', '水', true, mk((r) => {
    r(0, 0, 16, 16, '#3a78c4'); r(1, 3, 5, 1, '#6fa6e0'); r(9, 7, 5, 1, '#6fa6e0'); r(3, 11, 5, 1, '#6fa6e0');
  }));
  const SAND = deftile('모래', 'Sand', '砂', false, mk((r) => {
    r(0, 0, 16, 16, '#e3d39b'); r(3, 4, 1, 1, '#cdbb80'); r(10, 9, 1, 1, '#cdbb80'); r(6, 12, 1, 1, '#cdbb80');
  }));
  const FLOOR = deftile('나무 바닥', 'Wood Floor', '木の床', false, mk((r) => {
    r(0, 0, 16, 16, '#b07b46'); r(0, 5, 16, 1, '#946033'); r(0, 11, 16, 1, '#946033');
  }));
  const TILEFLOOR = deftile('타일 바닥', 'Tile Floor', 'タイル床', false, mk((r) => {
    r(0, 0, 16, 16, '#dfe3ea'); r(0, 0, 8, 8, '#c9ced8'); r(8, 8, 8, 8, '#c9ced8');
  }));
  const FENCE = deftile('울타리', 'Fence', 'フェンス', true, mk((r) => {
    r(0, 0, 16, 16, '#5fa84f'); r(0, 6, 16, 2, '#caa56a'); r(2, 2, 2, 12, '#b08a4e'); r(12, 2, 2, 12, '#b08a4e');
  }));
  const BENCH = deftile('벤치', 'Bench', 'ベンチ', true, mk((r) => {
    r(0, 0, 16, 16, '#b9b2a3'); r(2, 6, 12, 3, '#8a5a32'); r(2, 9, 12, 2, '#6e4626'); r(3, 11, 2, 3, '#5a3a22'); r(11, 11, 2, 3, '#5a3a22');
  }));
  const LAMP = deftile('가로등', 'Street Lamp', '街灯', true, mk((r) => {
    r(0, 0, 16, 16, '#b9b2a3'); r(7, 4, 2, 11, '#55585f'); r(5, 2, 6, 3, '#ffe9a0'); r(6, 1, 4, 2, '#cfd3da');
  }));
  const BRICK = deftile('벽돌길', 'Brick', 'レンガ', false, mk((r) => {
    r(0, 0, 16, 16, '#b5503e'); r(0, 5, 16, 1, '#8e3b2d'); r(0, 11, 16, 1, '#8e3b2d'); r(7, 0, 1, 5, '#8e3b2d'); r(3, 11, 1, 5, '#8e3b2d');
  }));
  const PATH = deftile('흙길', 'Dirt Path', '土の道', false, mk((r) => {
    r(0, 0, 16, 16, '#b08a5a'); r(3, 4, 2, 1, '#9a744a'); r(10, 8, 2, 1, '#9a744a'); r(6, 12, 2, 1, '#9a744a');
  }));

  /* ---------------- 캐릭터 ---------------- */
  const CW = 16, CH = 24;                       // 캐릭터 픽셀 격자
  const char = {
    gender: 'male', skin: '#f0c89b', hair: '#2a2118',
    clothes: new Array(CW * CH).fill(null),     // 사용자 픽셀 레이어
    acc: new Array(CW * CH).fill(null),
    base: new Array(CW * CH).fill(null)         // 자동 생성 기본(교복)
  };
  function lset(layer, x, y, c) { if (x >= 0 && x < CW && y >= 0 && y < CH) layer[y * CW + x] = c; }
  function lrect(layer, x0, y0, x1, y1, c) { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) lset(layer, x, y, c); }

  function buildBaseFor(c) {
    const b = new Array(CW * CH).fill(null);
    const skin = c.skin, hair = c.hair;
    const blazer = '#27314f', shirt = '#f2f3f7', shoes = '#1c1c22';
    const pants = '#3a3f4b', skirt = '#2b2f49', tie = '#7a2230', ribbon = '#c0303f', socks = '#eef0f5';
    const female = c.gender === 'female';

    if (female) lrect(b, 3, 3, 12, 17, hair);          // 긴 머리 배경
    lrect(b, 5, 3, 10, 8, skin);                        // 얼굴
    lrect(b, 5, 2, 10, 3, hair);                        // 머리 윗부분
    lrect(b, 5, 3, 10, 3, hair);                        // 앞머리
    if (!female) { lset(b, 5, 4, hair); lset(b, 10, 4, hair); }
    else { lrect(b, 4, 4, 4, 13, hair); lrect(b, 11, 4, 11, 13, hair); }
    lset(b, 6, 5, '#222'); lset(b, 9, 5, '#222');       // 눈
    lset(b, 7, 7, '#b06a5a');                            // 입
    lset(b, 7, 8, skin); lset(b, 8, 8, skin);            // 목

    lrect(b, 4, 9, 11, 15, blazer);                     // 상의(블레이저)
    lset(b, 6, 9, shirt); lset(b, 9, 9, shirt);          // 셔츠 깃
    if (female) { lset(b, 7, 9, ribbon); lset(b, 8, 9, ribbon); lset(b, 7, 10, ribbon); lset(b, 8, 10, ribbon); }
    else { lrect(b, 7, 9, 8, 12, tie); }                 // 넥타이
    lrect(b, 3, 9, 3, 13, blazer); lrect(b, 12, 9, 12, 13, blazer); // 팔
    lset(b, 3, 14, skin); lset(b, 12, 14, skin);         // 손

    if (female) {
      lrect(b, 4, 16, 11, 18, skirt);                   // 치마
      lset(b, 5, 16, '#1f2238'); lset(b, 8, 16, '#1f2238'); lset(b, 11, 16, '#1f2238');
      lrect(b, 6, 19, 7, 20, skin); lrect(b, 8, 19, 9, 20, skin); // 다리
      lrect(b, 6, 21, 7, 22, socks); lrect(b, 8, 21, 9, 22, socks);
      lrect(b, 6, 23, 7, 23, shoes); lrect(b, 8, 23, 9, 23, shoes);
    } else {
      lrect(b, 5, 16, 10, 21, pants);                   // 바지
      lset(b, 7, 16, '#2f333d'); lset(b, 8, 16, '#2f333d');
      lrect(b, 5, 22, 7, 23, shoes); lrect(b, 8, 22, 10, 23, shoes);
    }
    return b;
  }
  function buildBase() { char.base = buildBaseFor(char); }

  function drawCharOf(ctx, ox, oy, scale, bob, c) {
    bob = bob || 0;
    const layers = [c.base, c.clothes, c.acc];
    for (const L of layers) {
      if (!L) continue;
      for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
        const col = L[y * CW + x]; if (!col) continue;
        ctx.fillStyle = col;
        ctx.fillRect(Math.floor(ox + x * scale), Math.floor(oy + y * scale + bob), Math.ceil(scale), Math.ceil(scale));
      }
    }
  }
  function drawChar(ctx, ox, oy, scale, bob) { drawCharOf(ctx, ox, oy, scale, bob, char); }

  // 원격 플레이어 외형 직렬화/역직렬화
  function serializeChar() {
    return { gender: char.gender, skin: char.skin, hair: char.hair, clothes: char.clothes, acc: char.acc };
  }
  function makeRemote(p) {
    const r = { id: p.id, name: p.name || '?', x: p.x || 0, y: p.y || 0, tx: p.x || 0, ty: p.y || 0, bob: 0 };
    applyRemoteChar(r, p.char || {});
    return r;
  }
  function applyRemoteChar(r, c) {
    r.gender = c.gender || 'male'; r.skin = c.skin || '#f0c89b'; r.hair = c.hair || '#2a2118';
    r.clothes = Array.isArray(c.clothes) ? c.clothes : new Array(CW * CH).fill(null);
    r.acc = Array.isArray(c.acc) ? c.acc : new Array(CW * CH).fill(null);
    r.base = buildBaseFor(r);
  }

  /* ---------------- 월드 ---------------- */
  const world = { w: 48, h: 48, tiles: null };
  const idx = (x, y) => y * world.w + x;
  function inB(x, y) { return x >= 0 && y >= 0 && x < world.w && y < world.h; }
  function getTile(x, y) { return inB(x, y) ? world.tiles[idx(x, y)] : BWALL; }
  function setTile(x, y, v) { if (inB(x, y)) world.tiles[idx(x, y)] = v; }

  function genCity() {
    const W = world.w, H = world.h;
    const a = new Uint8Array(W * H);
    a.fill(GRASS);
    const put = (x, y, v) => { if (x >= 0 && y >= 0 && x < W && y < H) a[y * W + x] = v; };
    const at = (x, y) => a[y * W + x];

    // 도로 격자(8칸 간격)
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if (x % 8 === 0 || y % 8 === 0) put(x, y, ROAD);
    }
    // 교차로 횡단보도
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if ((x % 8 === 0) && (y % 8 === 1 || y % 8 === 7)) put(x, y, CROSS);
      if ((y % 8 === 0) && (x % 8 === 1 || x % 8 === 7)) put(x, y, CROSS);
    }
    // 보도(도로 옆 잔디)
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if (at(x, y) !== GRASS) continue;
      const near = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => {
        const nx = x + dx, ny = y + dy; return nx >= 0 && ny >= 0 && nx < W && ny < H && (at(nx, ny) === ROAD || at(nx, ny) === CROSS);
      });
      if (near) put(x, y, SIDEWALK);
    }

    // 블록(도로 사이 7x7 내부)에 건물 배치
    const blocksX = Math.floor((W - 1) / 8), blocksY = Math.floor((H - 1) / 8);
    let placedSchool = false, placedShop = false;
    for (let by = 0; by < blocksY; by++) {
      for (let bx = 0; bx < blocksX; bx++) {
        const ox = bx * 8 + 2, oy = by * 8 + 2;     // 내부 시작
        const bw = 4, bh = 3;                         // 건물 크기
        let kind = 'house';
        if (!placedSchool && bx === 1 && by === 1) { kind = 'school'; placedSchool = true; }
        else if (!placedShop && bx === 2 && by === 1) { kind = 'shop'; placedShop = true; }
        else if (Math.random() < 0.18 && !placedSchool) { kind = 'school'; placedSchool = true; }
        else if (Math.random() < 0.2 && !placedShop) { kind = 'shop'; placedShop = true; }

        const wall = kind === 'school' ? SCHOOL : kind === 'shop' ? SHOP : BWALL;
        const win = kind === 'school' ? SCHOOLSIGN : kind === 'shop' ? SHOPSIGN : BWIN;
        // 지붕
        for (let x = ox; x < ox + bw; x++) put(x, oy, ROOF);
        // 벽 + 창문/간판
        for (let y = oy + 1; y < oy + bh; y++) for (let x = ox; x < ox + bw; x++) {
          put(x, y, (y === oy + 1) ? win : wall);
        }
        // 문(아래 가운데)
        const doorX = ox + Math.floor(bw / 2);
        put(doorX, oy + bh, DOOR);
        // 앞마당 깔끔하게
        for (let x = ox - 1; x < ox + bw + 1; x++) {
          if (at(x, oy + bh + 1) === GRASS) put(x, oy + bh + 1, BRICK);
        }
        // 장식
        if (Math.random() < 0.6) put(ox - 1, oy + bh, TREE);
        if (Math.random() < 0.5) put(ox + bw, oy + bh + 1, FLOWER);
      }
    }

    // 보도 위 가로등/벤치/나무 흩뿌리기
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if (at(x, y) !== SIDEWALK) continue;
      const r = Math.random();
      if (r < 0.02) put(x, y, LAMP);
      else if (r < 0.035) put(x, y, BENCH);
      else if (r < 0.05) put(x, y, TREE);
    }
    // 작은 공원(연못)
    for (let y = 4; y < 7; y++) for (let x = 28; x < 31; x++) if (at(x, y) === GRASS) put(x, y, WATER);

    world.tiles = a;
  }

  function isSolidTile(v) { return TILES[v] && TILES[v].solid; }

  /* ---------------- 플레이어 / 카메라 ---------------- */
  const DRAW = 4;                 // 캐릭터 픽셀 배율(16x24 -> 64x96)
  const CHARW = CW * DRAW, CHARH = CH * DRAW;
  const player = { px: 0, py: 0, speed: 3.2, bob: 0, moving: false };
  const cam = { x: 0, y: 0 };
  const editorCam = { x: 0, y: 0 };

  function spawnPlayer(tx, ty) {
    if (tx == null) {
      // 비-고체 타일 탐색
      outer:
      for (let y = 6; y < world.h; y++) for (let x = 6; x < world.w; x++) {
        if (!isSolidTile(getTile(x, y))) { tx = x; ty = y; break outer; }
      }
    }
    player.px = tx * TILE + (TILE - CHARW) / 2;
    player.py = ty * TILE + (TILE - CHARH) / 2;
  }

  // 발밑 충돌 박스
  function blocked(px, py) {
    const bx0 = px + 14, bx1 = px + CHARW - 14;
    const by0 = py + CHARH - 18, by1 = py + CHARH - 2;
    const pts = [[bx0, by0], [bx1, by0], [bx0, by1], [bx1, by1]];
    for (const [x, y] of pts) {
      if (isSolidTile(getTile(Math.floor(x / TILE), Math.floor(y / TILE)))) return true;
    }
    return false;
  }

  /* ---------------- 상태 & DOM ---------------- */
  let state = 'start'; // start | play | menu | settings | character | map | (chat 오버레이는 play 위)
  const G = { name: '우서', settings: { vol: 0.8, tts: true, mic: false } };

  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const el = {
    start: $('#startScreen'), esc: $('#escMenu'), settings: $('#settingsPanel'),
    charEditor: $('#charEditor'), mapBar: $('#mapEditorBar'),
    chat: $('#chatPanel'), hud: $('#hud'), nameTag: $('#nameTag'), toast: $('#toast')
  };

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(window.innerWidth * dpr);
    canvas.height = Math.floor(window.innerHeight * dpr);
    canvas.style.width = window.innerWidth + 'px';
    canvas.style.height = window.innerHeight + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;
  }
  window.addEventListener('resize', resize);

  function toast(msg) {
    el.toast.textContent = msg; el.toast.classList.add('show');
    clearTimeout(toast._t); toast._t = setTimeout(() => el.toast.classList.remove('show'), 1600);
  }

  /* ---------------- 사운드(간단 비프 + TTS) ---------------- */
  let actx = null;
  function beep(freq, dur) {
    if (!G.settings.vol) return;
    try {
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      const o = actx.createOscillator(), g = actx.createGain();
      o.type = 'square'; o.frequency.value = freq || 440;
      g.gain.value = 0.04 * G.settings.vol;
      o.connect(g); g.connect(actx.destination);
      o.start(); o.stop(actx.currentTime + (dur || 0.05));
    } catch (e) {}
  }
  function speak(text) {
    if (!G.settings.tts || !('speechSynthesis' in window)) return;
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang === 'ko' ? 'ko-KR' : lang === 'ja' ? 'ja-JP' : 'en-US';
      u.volume = G.settings.vol; u.rate = 1;
      speechSynthesis.cancel(); speechSynthesis.speak(u);
    } catch (e) {}
  }

  /* ---------------- i18n 적용 ---------------- */
  function applyI18n() {
    $$('[data-i18n]').forEach(n => { n.textContent = t(n.dataset.i18n); });
    $$('[data-i18n-ph]').forEach(n => { n.placeholder = t(n.dataset.i18nPh); });
    document.documentElement.lang = lang;
    $('#ttsToggle').textContent = G.settings.tts ? t('on') : t('off');
    $('#micToggle').textContent = G.settings.mic ? t('on') : t('off');
    $('#ttsToggle').classList.toggle('active', G.settings.tts);
    $('#micToggle').classList.toggle('active', G.settings.mic);
    el.nameTag.textContent = G.name;
    buildMapPalette(); // 타일 이름 갱신
  }
  function fillLangSelect(sel) {
    sel.innerHTML = '';
    Object.keys(I18N).forEach(code => {
      const o = document.createElement('option');
      o.value = code; o.textContent = I18N[code]._name; sel.appendChild(o);
    });
    sel.value = lang;
  }

  /* ---------------- 패널 전환 ---------------- */
  function hideAllOverlays() {
    el.start.classList.add('hidden'); el.esc.classList.add('hidden');
    el.settings.classList.add('hidden'); el.charEditor.classList.add('hidden');
    el.mapBar.classList.remove('show');
  }
  function goPlay() {
    state = 'play'; hideAllOverlays();
    el.hud.classList.remove('hidden'); el.nameTag.classList.remove('hidden');
  }
  function openMenu() { state = 'menu'; el.esc.classList.remove('hidden'); }
  function closeMenu() { el.esc.classList.add('hidden'); goPlay(); }
  function openSettings() {
    state = 'settings'; el.esc.classList.add('hidden'); el.settings.classList.remove('hidden');
    fillLangSelect($('#langSelect')); $('#nameInput2').value = G.name;
    $('#volSlider').value = G.settings.vol;
  }
  function openCharEditor() {
    state = 'character'; el.esc.classList.add('hidden'); el.charEditor.classList.remove('hidden');
    syncCharEditorUI(); drawCharEditor();
  }
  function openMapEditor() {
    state = 'map'; hideAllOverlays(); el.mapBar.classList.add('show');
    el.hud.classList.add('hidden');
    editorCam.x = cam.x; editorCam.y = cam.y;
  }
  function backToMenu() { hideAllOverlays(); openMenu(); }

  /* ---------------- 입력 ---------------- */
  const keys = {};
  window.addEventListener('keydown', (e) => {
    const typing = document.activeElement && /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName);
    if (e.key === 'Escape') {
      if (state === 'play') { openMenu(); beep(520); }
      else if (state === 'menu') closeMenu();
      else if (state === 'settings' || state === 'character') backToMenu();
      else if (state === 'map') { /* 완료 버튼으로 */ }
      else if (state === 'start') { /* 무시 */ }
      e.preventDefault(); return;
    }
    if (typing) return;
    if (state === 'play' && (e.key === 'Enter')) { openChat(); e.preventDefault(); return; }
    keys[e.key.toLowerCase()] = true;
  });
  window.addEventListener('keyup', (e) => { keys[e.key.toLowerCase()] = false; });

  function axis() {
    let dx = 0, dy = 0;
    if (keys['a'] || keys['arrowleft']) dx -= 1;
    if (keys['d'] || keys['arrowright']) dx += 1;
    if (keys['w'] || keys['arrowup']) dy -= 1;
    if (keys['s'] || keys['arrowdown']) dy += 1;
    return [dx, dy];
  }

  /* ---------------- 업데이트 ---------------- */
  function update() {
    if (state === 'play') {
      const [dx, dy] = axis();
      const sp = player.speed;
      let moved = false;
      if (dx !== 0) { const nx = player.px + dx * sp; if (!blocked(nx, player.py)) { player.px = nx; moved = true; } }
      if (dy !== 0) { const ny = player.py + dy * sp; if (!blocked(player.px, ny)) { player.py = ny; moved = true; } }
      // 경계
      player.px = Math.max(0, Math.min(world.w * TILE - CHARW, player.px));
      player.py = Math.max(0, Math.min(world.h * TILE - CHARH, player.py));
      player.moving = moved;
      player.bob = moved ? Math.sin(performance.now() / 90) * 2 : 0;
      // 카메라
      const vw = window.innerWidth, vh = window.innerHeight;
      cam.x = clamp(player.px + CHARW / 2 - vw / 2, 0, Math.max(0, world.w * TILE - vw));
      cam.y = clamp(player.py + CHARH / 2 - vh / 2, 0, Math.max(0, world.h * TILE - vh));
      net.sendMove();
    } else if (state === 'map') {
      const [dx, dy] = axis();
      editorCam.x = clamp(editorCam.x + dx * 10, 0, Math.max(0, world.w * TILE - window.innerWidth));
      editorCam.y = clamp(editorCam.y + dy * 10, 0, Math.max(0, world.h * TILE - window.innerHeight));
    }
  }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  /* ---------------- 렌더 ---------------- */
  function renderWorld(camX, camY) {
    const vw = window.innerWidth, vh = window.innerHeight;
    ctx.fillStyle = '#0b0e16'; ctx.fillRect(0, 0, vw, vh);
    const x0 = Math.floor(camX / TILE), y0 = Math.floor(camY / TILE);
    const x1 = Math.ceil((camX + vw) / TILE), y1 = Math.ceil((camY + vh) / TILE);
    for (let ty = y0; ty <= y1; ty++) {
      for (let tx = x0; tx <= x1; tx++) {
        const sx = tx * TILE - camX, sy = ty * TILE - camY;
        const v = inB(tx, ty) ? getTile(tx, ty) : -1;
        if (v < 0) { ctx.fillStyle = '#0b0e16'; ctx.fillRect(sx, sy, TILE, TILE); continue; }
        TILES[v].draw(ctx, sx, sy, TILE);
      }
    }
  }
  function render() {
    if (state === 'start') return;
    if (state === 'map') {
      renderWorld(editorCam.x, editorCam.y);
      // 격자 + 커서
      const vw = window.innerWidth, vh = window.innerHeight;
      ctx.strokeStyle = 'rgba(255,255,255,.08)'; ctx.lineWidth = 1;
      for (let x = -editorCam.x % TILE; x < vw; x += TILE) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, vh); ctx.stroke(); }
      for (let y = -editorCam.y % TILE; y < vh; y += TILE) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(vw, y); ctx.stroke(); }
      if (mouse.tx != null) {
        const sx = mouse.tx * TILE - editorCam.x, sy = mouse.ty * TILE - editorCam.y;
        ctx.strokeStyle = '#5cc8ff'; ctx.lineWidth = 2; ctx.strokeRect(sx, sy, TILE, TILE);
      }
      // 다른 플레이어 + 내 위치
      renderOthers(editorCam.x, editorCam.y);
      drawChar(ctx, player.px - editorCam.x, player.py - editorCam.y, DRAW, 0);
      return;
    }
    // play / menu / settings / character: 월드 배경 유지
    renderWorld(cam.x, cam.y);
    renderOthers(cam.x, cam.y);
    drawChar(ctx, player.px - cam.x, player.py - cam.y, DRAW, player.bob);
    drawNameTag(G.name, player.px - cam.x, player.py - cam.y, '#5cc8ff');
  }

  // 원격 플레이어 렌더 + 이름표
  function renderOthers(camX, camY) {
    net.others.forEach((o) => {
      // 부드러운 이동 보간
      o.x += (o.tx - o.x) * 0.25; o.y += (o.ty - o.y) * 0.25;
      const sx = o.x - camX, sy = o.y - camY;
      if (sx < -CHARW || sy < -CHARH || sx > window.innerWidth || sy > window.innerHeight) return;
      drawCharOf(ctx, sx, sy, DRAW, 0, o);
      drawNameTag(o.name, sx, sy, o.voice ? '#69d98a' : '#ffffff');
    });
  }
  function drawNameTag(name, sx, sy, color) {
    ctx.font = '12px "Segoe UI",sans-serif'; ctx.textAlign = 'center';
    const w = ctx.measureText(name).width + 12;
    const cx = sx + CHARW / 2, ty = sy - 8;
    ctx.fillStyle = 'rgba(8,10,18,.6)';
    ctx.fillRect(cx - w / 2, ty - 13, w, 16);
    ctx.fillStyle = color; ctx.fillText(name, cx, ty);
    ctx.textAlign = 'left';
  }

  function loop() { update(); render(); requestAnimationFrame(loop); }

  /* ---------------- 채팅 ---------------- */
  function openChat() { el.chat.classList.add('show'); $('#chatInput').focus(); }
  function closeChat() { el.chat.classList.remove('show'); }
  function addMsg(text, who, cls) {
    const log = $('#chatLog');
    const d = document.createElement('div'); d.className = 'msg ' + cls;
    if (cls !== 'sys') { const w = document.createElement('div'); w.className = 'who'; w.textContent = who; d.appendChild(w); }
    const s = document.createElement('div'); s.textContent = text; d.appendChild(s);
    log.appendChild(d); log.scrollTop = log.scrollHeight;
    return d;
  }
  function sendChat() {
    const inp = $('#chatInput'); const txt = inp.value.trim(); if (!txt) return;
    addMsg(txt, G.name, 'me'); inp.value = '';
    speak(txt);
    if (net.connected) net.send({ t: 'chat', text: txt });   // 다른 플레이어에게 전송 (자동응답 봇 없음)
  }

  /* ---------------- 네트워크(온라인 멀티플레이) ---------------- */
  const net = {
    ws: null, id: null, connected: false, others: new Map(),
    lastSent: 0, lastX: -1, lastY: -1,

    available() { return location.protocol === 'http:' || location.protocol === 'https:'; },

    connect() {
      if (!net.available()) { updateOnlineBadge(); return; } // file:// 는 오프라인
      try {
        const proto = location.protocol === 'https:' ? 'wss' : 'ws';
        const ws = new WebSocket(proto + '://' + location.host);
        net.ws = ws;
        ws.onopen = () => {
          net.send({ t: 'join', name: G.name, char: serializeChar(),
            world: { w: world.w, h: world.h, tiles: Array.from(world.tiles) } });
        };
        ws.onmessage = (e) => { try { net.route(JSON.parse(e.data)); } catch (err) {} };
        ws.onclose = () => {
          net.connected = false; net.others.clear(); voice.stop(); updateOnlineBadge();
          setTimeout(() => { if (state !== 'start') net.connect(); }, 2500); // 자동 재접속
        };
        ws.onerror = () => {};
      } catch (e) {}
    },

    send(obj) { if (net.ws && net.ws.readyState === 1) { try { net.ws.send(JSON.stringify(obj)); } catch (e) {} } },

    sendMove() {
      if (!net.connected) return;
      const now = performance.now();
      if (now - net.lastSent < 60) return;
      const x = Math.round(player.px), y = Math.round(player.py);
      if (x === net.lastX && y === net.lastY) return;
      net.lastSent = now; net.lastX = x; net.lastY = y;
      net.send({ t: 'move', x: x, y: y });
    },

    sendChar() { if (net.connected) net.send({ t: 'char', char: serializeChar() }); },
    sendTile(x, y, v) { if (net.connected) net.send({ t: 'tile', x: x, y: y, v: v }); },

    route(m) {
      switch (m.t) {
        case 'init':
          net.id = m.id; net.connected = true;
          if (m.world && Array.isArray(m.world.tiles)) {
            world.w = m.world.w; world.h = m.world.h; world.tiles = Uint8Array.from(m.world.tiles);
            // 새 월드 안의 안전한 위치로
            if (isSolidTile(getTile(Math.floor((player.px + CHARW / 2) / TILE), Math.floor((player.py + CHARH) / TILE)))) spawnPlayer();
          }
          net.others.clear();
          (m.players || []).forEach(p => net.others.set(p.id, makeRemote(p)));
          updateOnlineBadge();
          addMsg(I18N[lang].sysJoinedRoom || 'Connected to online world.', '', 'sys');
          break;
        case 'join':
          net.others.set(m.id, makeRemote(m)); updateOnlineBadge();
          addMsg((m.name || '?') + (I18N[lang].sysEnter || ' joined.'), '', 'sys');
          voice.onPeerJoin(m.id);
          break;
        case 'leave': {
          const o = net.others.get(m.id);
          net.others.delete(m.id); voice.onPeerLeave(m.id); updateOnlineBadge();
          if (o) addMsg(o.name + (I18N[lang].sysLeave || ' left.'), '', 'sys');
          break;
        }
        case 'move': { const o = net.others.get(m.id); if (o) { o.tx = m.x; o.ty = m.y; } break; }
        case 'char': { const o = net.others.get(m.id); if (o) applyRemoteChar(o, m.char || {}); break; }
        case 'tile': setTile(m.x, m.y, m.v); break;
        case 'chat': {
          const o = net.others.get(m.id);
          const who = (o && o.name) || m.name || '?';
          addMsg(m.text, who, 'them'); speak(m.text);
          break;
        }
        case 'rtc': voice.onSignal(m.from, m.data); break;
      }
    }
  };

  function updateOnlineBadge() {
    const b = $('#onlineBadge'); if (!b) return;
    if (net.connected) {
      b.classList.remove('hidden');
      b.textContent = '🟢 ' + (I18N[lang].online || 'Online') + ' · ' + (net.others.size + 1);
    } else if (net.available()) {
      b.classList.remove('hidden'); b.textContent = '🔴 ' + (I18N[lang].offline || 'Offline');
    } else {
      b.classList.add('hidden');
    }
  }

  /* ---------------- 실시간 음성 채팅(WebRTC) ---------------- */
  const voice = {
    on: false, stream: null, peers: new Map(), audios: new Map(),
    ICE: [{ urls: 'stun:stun.l.google.com:19302' }],

    async toggle() {
      if (voice.on) { voice.stop(); return; }
      if (!net.connected) { toast(I18N[lang].needOnline || 'Connect online first.'); return; }
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { toast(t('micNo')); return; }
      try {
        voice.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        voice.on = true; $('#voiceBtn').classList.add('on');
        toast(I18N[lang].voiceOn || 'Voice chat ON');
        net.send({ t: 'char', char: serializeChar() }); // 외형 갱신 겸 핑
        net.others.forEach((o, id) => voice.callPeer(id, true)); // 기존 모두에게 발신
      } catch (e) { toast(I18N[lang].micDenied || 'Microphone blocked.'); }
    },
    stop() {
      voice.on = false; $('#voiceBtn') && $('#voiceBtn').classList.remove('on');
      if (voice.stream) { voice.stream.getTracks().forEach(t => t.stop()); voice.stream = null; }
      voice.peers.forEach(pc => { try { pc.close(); } catch (e) {} });
      voice.peers.clear();
      voice.audios.forEach(a => { try { a.pause(); } catch (e) {} }); voice.audios.clear();
    },
    pc(id) {
      let pc = voice.peers.get(id);
      if (pc) return pc;
      pc = new RTCPeerConnection({ iceServers: voice.ICE });
      if (voice.stream) voice.stream.getTracks().forEach(tk => pc.addTrack(tk, voice.stream));
      pc.onicecandidate = (e) => { if (e.candidate) net.send({ t: 'rtc', to: id, data: { ice: e.candidate } }); };
      pc.ontrack = (e) => {
        let a = voice.audios.get(id);
        if (!a) { a = new Audio(); a.autoplay = true; voice.audios.set(id, a); }
        a.srcObject = e.streams[0]; a.volume = G.settings.vol;
        const o = net.others.get(id); if (o) o.voice = true;
      };
      pc.onconnectionstatechange = () => { if (pc.connectionState === 'failed') { try { pc.close(); } catch (e) {} voice.peers.delete(id); } };
      voice.peers.set(id, pc);
      return pc;
    },
    async callPeer(id, initiator) {
      const pc = voice.pc(id);
      if (initiator) {
        const offer = await pc.createOffer(); await pc.setLocalDescription(offer);
        net.send({ t: 'rtc', to: id, data: { sdp: pc.localDescription } });
      }
    },
    onPeerJoin(id) { if (voice.on) voice.callPeer(id, true); },
    onPeerLeave(id) {
      const pc = voice.peers.get(id); if (pc) { try { pc.close(); } catch (e) {} voice.peers.delete(id); }
      const a = voice.audios.get(id); if (a) { try { a.pause(); } catch (e) {} voice.audios.delete(id); }
    },
    async onSignal(from, data) {
      if (!data) return;
      const pc = voice.pc(from);
      try {
        if (data.sdp) {
          await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
          if (data.sdp.type === 'offer') {
            if (voice.stream) voice.stream.getTracks().forEach(tk => { if (!pc.getSenders().some(s => s.track === tk)) pc.addTrack(tk, voice.stream); });
            const answer = await pc.createAnswer(); await pc.setLocalDescription(answer);
            net.send({ t: 'rtc', to: from, data: { sdp: pc.localDescription } });
          }
        } else if (data.ice) {
          await pc.addIceCandidate(new RTCIceCandidate(data.ice));
        }
      } catch (e) {}
    }
  };

  // 음성 입력(STT)
  let recog = null;
  function setupRecog() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const r = new SR(); r.continuous = false; r.interimResults = false;
    r.onresult = (e) => { const txt = e.results[0][0].transcript; $('#chatInput').value = txt; };
    r.onend = () => { $('#chatMic').classList.remove('rec'); };
    r.onerror = () => { $('#chatMic').classList.remove('rec'); };
    return r;
  }
  function micToggleAction() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { toast(t('micNo')); return; }
    if (location.protocol === 'file:') { toast(t('micHttp')); }
    recog = recog || setupRecog();
    try {
      recog.lang = lang === 'ko' ? 'ko-KR' : lang === 'ja' ? 'ja-JP' : 'en-US';
      recog.start(); $('#chatMic').classList.add('rec');
    } catch (e) { $('#chatMic').classList.remove('rec'); }
  }

  /* ---------------- 캐릭터 에디터 ---------------- */
  const ceCanvas = $('#charCanvas');
  const ceCtx = ceCanvas.getContext('2d');
  ceCtx.imageSmoothingEnabled = false;
  const CE_SCALE = 20; // 320/16
  const ce = { layer: 'clothes', tool: 'pen', color: '#ff6699', drawing: false };
  let palette = ['#ffffff', '#000000', '#ff4d6d', '#ff9f45', '#ffe066', '#69d98a', '#5cc8ff', '#7c83ff', '#c46bff', '#8a5a32', '#f0c89b', '#2a2118'];

  function buildPalette() {
    const wrap = $('#charPalette'); wrap.innerHTML = '';
    palette.forEach(c => {
      const s = document.createElement('div'); s.className = 'swatch' + (c === ce.color ? ' active' : '');
      s.style.background = c; s.title = c;
      s.onclick = () => { ce.color = c; buildPalette(); };
      wrap.appendChild(s);
    });
  }
  function drawCharEditor() {
    ceCtx.clearRect(0, 0, ceCanvas.width, ceCanvas.height);
    // 격자
    ceCtx.fillStyle = '#0e1320'; ceCtx.fillRect(0, 0, ceCanvas.width, ceCanvas.height);
    ceCtx.strokeStyle = 'rgba(255,255,255,.05)';
    for (let x = 0; x <= CW; x++) { ceCtx.beginPath(); ceCtx.moveTo(x * CE_SCALE, 0); ceCtx.lineTo(x * CE_SCALE, CH * CE_SCALE); ceCtx.stroke(); }
    for (let y = 0; y <= CH; y++) { ceCtx.beginPath(); ceCtx.moveTo(0, y * CE_SCALE); ceCtx.lineTo(CW * CE_SCALE, y * CE_SCALE); ceCtx.stroke(); }
    drawChar(ceCtx, 0, 0, CE_SCALE, 0);
  }
  function ceCellFromEvent(e) {
    const rect = ceCanvas.getBoundingClientRect();
    const sx = ceCanvas.width / rect.width, sy = ceCanvas.height / rect.height;
    const x = Math.floor((e.clientX - rect.left) * sx / CE_SCALE);
    const y = Math.floor((e.clientY - rect.top) * sy / CE_SCALE);
    return [x, y];
  }
  function cePaint(x, y) {
    if (x < 0 || y < 0 || x >= CW || y >= CH) return;
    const layer = ce.layer === 'clothes' ? char.clothes : char.acc;
    if (ce.tool === 'pen') layer[y * CW + x] = ce.color;
    else if (ce.tool === 'erase') layer[y * CW + x] = null;
    else if (ce.tool === 'fill') floodFill(layer, x, y, layer[y * CW + x], ce.color);
    drawCharEditor();
  }
  function floodFill(layer, x, y, target, repl) {
    if (target === repl) return;
    const st = [[x, y]];
    while (st.length) {
      const [cx, cy] = st.pop();
      if (cx < 0 || cy < 0 || cx >= CW || cy >= CH) continue;
      if (layer[cy * CW + cx] !== target) continue;
      layer[cy * CW + cx] = repl;
      st.push([cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]);
    }
  }
  function syncCharEditorUI() {
    $('#ceMale').classList.toggle('active', char.gender === 'male');
    $('#ceFemale').classList.toggle('active', char.gender === 'female');
    $('#skinColor').value = char.skin; $('#hairColor').value = char.hair;
    $('#layClothes').classList.toggle('active', ce.layer === 'clothes');
    $('#layAcc').classList.toggle('active', ce.layer === 'acc');
    ['pen', 'erase', 'fill'].forEach(tool =>
      $('#tool' + tool[0].toUpperCase() + tool.slice(1)).classList.toggle('active', ce.tool === tool));
    buildPalette();
  }

  /* ---------------- 맵 에디터 팔레트 ---------------- */
  let selectedTile = GRASS, mapEraseMode = false;
  function buildMapPalette() {
    const wrap = $('#mapPalette'); if (!wrap) return; wrap.innerHTML = '';
    TILES.forEach((tl, i) => {
      const b = document.createElement('button');
      b.className = 'tilebtn' + (i === selectedTile && !mapEraseMode ? ' active' : '');
      const c = document.createElement('canvas'); c.width = 34; c.height = 34;
      const cx = c.getContext('2d'); cx.imageSmoothingEnabled = false;
      tl.draw(cx, 0, 0, 34);
      b.appendChild(c);
      const n = document.createElement('span'); n.className = 'tn'; n.textContent = tname(i); b.appendChild(n);
      b.title = tname(i);
      b.onclick = () => { selectedTile = i; mapEraseMode = false; buildMapPalette(); beep(440); };
      wrap.appendChild(b);
    });
  }

  /* ---------------- 마우스(맵 에디터) ---------------- */
  const mouse = { tx: null, ty: null, down: false, btn: 0 };
  function mapCellFromEvent(e) {
    const wx = e.clientX + editorCam.x, wy = e.clientY + editorCam.y;
    return [Math.floor(wx / TILE), Math.floor(wy / TILE)];
  }
  canvas.addEventListener('contextmenu', (e) => { if (state === 'map') e.preventDefault(); });
  canvas.addEventListener('mousedown', (e) => {
    if (state !== 'map') return;
    mouse.down = true; mouse.btn = e.button;
    const [tx, ty] = mapCellFromEvent(e);
    paintMap(tx, ty, e.button === 2);
  });
  canvas.addEventListener('mousemove', (e) => {
    if (state !== 'map') return;
    const [tx, ty] = mapCellFromEvent(e); mouse.tx = tx; mouse.ty = ty;
    if (mouse.down) paintMap(tx, ty, mouse.btn === 2);
  });
  window.addEventListener('mouseup', () => { mouse.down = false; });
  function paintMap(tx, ty, erase) {
    if (!inB(tx, ty)) return;
    const v = (erase || mapEraseMode) ? GRASS : selectedTile;
    if (getTile(tx, ty) === v) return;
    setTile(tx, ty, v);
    net.sendTile(tx, ty, v);   // 함께 편집(동기화)
  }

  /* ---------------- 적용/시작 ---------------- */
  function startGame(fromSave) {
    G.name = ($('#nameInput').value.trim() || G.name || '우서').slice(0, 16);
    buildBase();
    if (!world.tiles) genCity();
    if (!fromSave) spawnPlayer();
    resize(); applyI18n();
    goPlay();
    net.connect();          // 온라인 접속 시도(http/https일 때)
    updateOnlineBadge();
    // 환영 메시지
    setTimeout(() => {
      openChat();
      addMsg(G.name + t('welcome'), t('narrator'), 'sys');
    }, 300);
  }

  /* ---------------- 이벤트 바인딩 ---------------- */
  function bind() {
    fillLangSelect($('#langSelectStart'));
    $('#langSelectStart').onchange = (e) => { lang = e.target.value; applyI18n(); };
    $('#langSelect').onchange = (e) => { lang = e.target.value; applyI18n(); fillLangSelect($('#langSelectStart')); };

    // 시작 화면 성별
    let pendingGender = 'male';
    const setG = (g) => {
      pendingGender = g; char.gender = g; buildBase();
      $('#gMale').classList.toggle('active', g === 'male');
      $('#gFemale').classList.toggle('active', g === 'female');
    };
    $('#gMale').onclick = () => setG('male');
    $('#gFemale').onclick = () => setG('female');
    setG('male');

    if (hasSave()) $('#continueBtn').classList.remove('hidden');
    $('#continueBtn').onclick = () => { applySave(loadSave()); startGame(true); };
    $('#startBtn').onclick = () => { startGame(false); };

    // ESC 메뉴
    $$('#escMenu [data-action]').forEach(b => b.onclick = () => {
      beep(480);
      const a = b.dataset.action;
      if (a === 'resume') closeMenu();
      else if (a === 'settings') openSettings();
      else if (a === 'character') openCharEditor();
      else if (a === 'map') openMapEditor();
      else if (a === 'chat') { goPlay(); openChat(); }
      else if (a === 'save') { persist(); toast(t('saved')); }
      else if (a === 'title') { persist(); location.reload(); }
    });

    // 뒤로
    $$('[data-back]').forEach(b => b.onclick = () => backToMenu());

    // 설정
    $('#volSlider').oninput = (e) => { G.settings.vol = parseFloat(e.target.value); };
    $('#ttsToggle').onclick = () => { G.settings.tts = !G.settings.tts; applyI18n(); };
    $('#micToggle').onclick = () => { G.settings.mic = !G.settings.mic; applyI18n(); };
    $('#nameInput2').oninput = (e) => { G.name = e.target.value.slice(0, 16) || G.name; el.nameTag.textContent = G.name; };
    $('#wipeBtn').onclick = () => { try { localStorage.removeItem(SAVE_KEY); } catch (e) {} toast(t('wiped')); };

    // 캐릭터 에디터
    $('#ceMale').onclick = () => { char.gender = 'male'; buildBase(); syncCharEditorUI(); drawCharEditor(); };
    $('#ceFemale').onclick = () => { char.gender = 'female'; buildBase(); syncCharEditorUI(); drawCharEditor(); };
    $('#skinColor').oninput = (e) => { char.skin = e.target.value; buildBase(); drawCharEditor(); };
    $('#hairColor').oninput = (e) => { char.hair = e.target.value; buildBase(); drawCharEditor(); };
    $('#layClothes').onclick = () => { ce.layer = 'clothes'; syncCharEditorUI(); };
    $('#layAcc').onclick = () => { ce.layer = 'acc'; syncCharEditorUI(); };
    $('#toolPen').onclick = () => { ce.tool = 'pen'; syncCharEditorUI(); };
    $('#toolErase').onclick = () => { ce.tool = 'erase'; syncCharEditorUI(); };
    $('#toolFill').onclick = () => { ce.tool = 'fill'; syncCharEditorUI(); };
    $('#addColor').onclick = () => { const c = $('#customColor').value; if (!palette.includes(c)) palette.push(c); ce.color = c; buildPalette(); };
    $('#clearLayer').onclick = () => {
      const layer = ce.layer === 'clothes' ? char.clothes : char.acc;
      for (let i = 0; i < layer.length; i++) layer[i] = null; drawCharEditor();
    };
    $('#randomLook').onclick = () => {
      const layer = char.clothes;
      for (let i = 0; i < layer.length; i++) layer[i] = null;
      const cols = palette.slice(0, 9);
      // 상의 영역 랜덤 색칠
      for (let y = 9; y <= 15; y++) for (let x = 4; x <= 11; x++)
        if (Math.random() < 0.5) layer[y * CW + x] = cols[Math.floor(Math.random() * cols.length)];
      char.hair = ['#2a2118', '#5a3a1a', '#c4732a', '#222', '#9a3b5a', '#3a5a9a'][Math.floor(Math.random() * 6)];
      buildBase(); $('#hairColor').value = char.hair; drawCharEditor();
    };
    $('#charSave').onclick = () => { persist(); net.sendChar(); toast(t('applied')); backToMenu(); };

    // 캐릭터 캔버스 그리기
    const startDraw = (e) => { ce.drawing = true; const [x, y] = ceCellFromEvent(e); cePaint(x, y); };
    const moveDraw = (e) => { if (!ce.drawing) return; const [x, y] = ceCellFromEvent(e); cePaint(x, y); };
    ceCanvas.addEventListener('mousedown', startDraw);
    ceCanvas.addEventListener('mousemove', moveDraw);
    window.addEventListener('mouseup', () => { ce.drawing = false; });
    ceCanvas.addEventListener('touchstart', (e) => { e.preventDefault(); startDraw(e.touches[0]); }, { passive: false });
    ceCanvas.addEventListener('touchmove', (e) => { e.preventDefault(); moveDraw(e.touches[0]); }, { passive: false });
    window.addEventListener('touchend', () => { ce.drawing = false; });

    // 맵 에디터 바
    $('#meErase').onclick = () => { mapEraseMode = !mapEraseMode; $('#meErase').classList.toggle('active', mapEraseMode); buildMapPalette(); };
    $('#meReset').onclick = () => { genCity(); toast(t('resetCity')); };
    $('#meClear').onclick = () => { world.tiles.fill(GRASS); };
    $('#meDone').onclick = () => { persist(); toast(t('mapSaved')); backToMenu(); };

    // 채팅
    $('#chatSend').onclick = sendChat;
    $('#chatInput').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.stopPropagation(); sendChat(); } });
    $('#chatClose').onclick = closeChat;
    $('#chatMic').onclick = micToggleAction;
    $('#chatTts').onclick = () => { G.settings.tts = !G.settings.tts; $('#chatTts').classList.toggle('on', G.settings.tts); applyI18n(); };
    $('#chatTts').classList.toggle('on', G.settings.tts);
    $('#voiceBtn').onclick = () => voice.toggle();
  }

  function applySave(s) {
    if (!s) return;
    if (s.lang && I18N[s.lang]) lang = s.lang;
    if (s.name) G.name = s.name;
    if (s.settings) G.settings = Object.assign(G.settings, s.settings);
    if (s.character) {
      char.gender = s.character.gender || 'male';
      char.skin = s.character.skin || char.skin;
      char.hair = s.character.hair || char.hair;
      if (Array.isArray(s.character.clothes)) char.clothes = s.character.clothes.slice(0, CW * CH);
      if (Array.isArray(s.character.acc)) char.acc = s.character.acc.slice(0, CW * CH);
    }
    if (s.world && Array.isArray(s.world.tiles)) {
      world.w = s.world.w; world.h = s.world.h;
      world.tiles = Uint8Array.from(s.world.tiles);
    }
    buildBase();
    if (s.player) spawnPlayer(s.player.tx, s.player.ty);
  }

  /* ---------------- 초기화 ---------------- */
  function init() {
    const s = loadSave();
    if (s && s.lang && I18N[s.lang]) lang = s.lang;
    if (s && s.name) { /* 이름은 시작 시 입력칸에 표시 */ }
    resize();
    bind();
    buildBase();
    applyI18n();
    buildMapPalette();
    if (s && s.name) $('#nameInput').value = s.name;
    requestAnimationFrame(loop);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
