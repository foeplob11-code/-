/* =========================================================
   우서 월드 - 온라인 멀티플레이 서버 (의존성 없음, Node 내장)
   - 정적 파일 서빙(index.html / game.js / style.css)
   - WebSocket 실시간 동기화(위치/채팅/맵/외형)
   - WebRTC 음성 채팅 시그널링 중계
   실행:  node server.js     접속:  http://localhost:4173
   ========================================================= */
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = __dirname;
const PORT = process.env.PORT || 4173;
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png', '.ico': 'image/x-icon', '.json': 'application/json'
};

/* ---------------- 정적 파일 ---------------- */
const server = http.createServer((req, res) => {
  let p = decodeURIComponent((req.url || '/').split('?')[0]);
  if (p === '/') p = '/index.html';
  const file = path.join(ROOT, p);
  if (!file.startsWith(ROOT)) { res.writeHead(403); return res.end('forbidden'); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  });
});

/* ---------------- 게임 상태 ---------------- */
const clients = new Map();   // id -> conn
let nextId = 1;
let world = null;            // 공유 월드 { w, h, tiles:[] }

function broadcast(obj, exceptId) {
  const s = JSON.stringify(obj);
  clients.forEach((c) => { if (c.joined && c.id !== exceptId) sendRaw(c.socket, s); });
}
function playerList(exceptId) {
  const out = [];
  clients.forEach((c) => { if (c.joined && c.id !== exceptId) out.push({ id: c.id, name: c.name, x: c.x, y: c.y, char: c.char }); });
  return out;
}

function onMessage(conn, text) {
  let m; try { m = JSON.parse(text); } catch (e) { return; }
  switch (m.t) {
    case 'join': {
      conn.joined = true;
      conn.name = (m.name || '플레이어').slice(0, 16);
      conn.char = m.char || {};
      conn.x = 0; conn.y = 0;
      // 첫 접속자의 맵을 공유 월드로 채택
      if (!world && m.world && Array.isArray(m.world.tiles)) {
        world = { w: m.world.w, h: m.world.h, tiles: m.world.tiles };
      }
      sendObj(conn.socket, { t: 'init', id: conn.id, world: world, players: playerList(conn.id) });
      broadcast({ t: 'join', id: conn.id, name: conn.name, x: conn.x, y: conn.y, char: conn.char }, conn.id);
      log(conn.name + ' 입장 (현재 ' + countJoined() + '명)');
      break;
    }
    case 'move': {
      conn.x = m.x; conn.y = m.y;
      broadcast({ t: 'move', id: conn.id, x: m.x, y: m.y }, conn.id);
      break;
    }
    case 'char': {
      conn.char = m.char || conn.char;
      broadcast({ t: 'char', id: conn.id, char: conn.char }, conn.id);
      break;
    }
    case 'chat': {
      broadcast({ t: 'chat', id: conn.id, name: conn.name, text: String(m.text || '').slice(0, 400) }, conn.id);
      break;
    }
    case 'tile': {
      if (world && m.x >= 0 && m.y >= 0 && m.x < world.w && m.y < world.h) {
        world.tiles[m.y * world.w + m.x] = m.v;
      }
      broadcast({ t: 'tile', x: m.x, y: m.y, v: m.v }, conn.id);
      break;
    }
    case 'rtc': {   // WebRTC 시그널링 중계
      const target = clients.get(m.to);
      if (target && target.joined) sendObj(target.socket, { t: 'rtc', from: conn.id, data: m.data });
      break;
    }
  }
}

function onClose(conn) {
  if (!clients.has(conn.id)) return;
  clients.delete(conn.id);
  if (conn.joined) { broadcast({ t: 'leave', id: conn.id }); log(conn.name + ' 퇴장 (현재 ' + countJoined() + '명)'); }
}
function countJoined() { let n = 0; clients.forEach(c => { if (c.joined) n++; }); return n; }
function log(s) { console.log('[' + new Date().toLocaleTimeString() + '] ' + s); }

/* ---------------- WebSocket (핸드셰이크 + 프레임) ---------------- */
server.on('upgrade', (req, socket) => {
  const key = req.headers['sec-websocket-key'];
  if (!key) { socket.destroy(); return; }
  const accept = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
  socket.write(
    'HTTP/1.1 101 Switching Protocols\r\n' +
    'Upgrade: websocket\r\n' +
    'Connection: Upgrade\r\n' +
    'Sec-WebSocket-Accept: ' + accept + '\r\n\r\n'
  );
  socket.setNoDelay(true);

  const conn = { id: nextId++, socket, joined: false, name: '', x: 0, y: 0, char: {} };
  clients.set(conn.id, conn);

  let buf = Buffer.alloc(0);
  let frags = []; let fragOp = 0;
  socket.on('data', (d) => {
    buf = Buffer.concat([buf, d]);
    while (true) {
      if (buf.length < 2) break;
      const b0 = buf[0], b1 = buf[1];
      const fin = (b0 & 0x80) !== 0;
      const op = b0 & 0x0f;
      const masked = (b1 & 0x80) !== 0;
      let len = b1 & 0x7f, off = 2;
      if (len === 126) { if (buf.length < 4) break; len = buf.readUInt16BE(2); off = 4; }
      else if (len === 127) { if (buf.length < 10) break; len = Number(buf.readBigUInt64BE(2)); off = 10; }
      let mask;
      if (masked) { if (buf.length < off + 4) break; mask = buf.slice(off, off + 4); off += 4; }
      if (buf.length < off + len) break;
      let payload = buf.slice(off, off + len);
      if (masked) {
        const out = Buffer.allocUnsafe(len);
        for (let i = 0; i < len; i++) out[i] = payload[i] ^ mask[i & 3];
        payload = out;
      }
      buf = buf.slice(off + len);

      if (op === 0x8) { try { socket.end(); } catch (e) {} onClose(conn); return; }  // close
      if (op === 0x9) { sendFrame(socket, 0xA, payload); continue; }                  // ping->pong
      if (op === 0xA) { continue; }                                                   // pong
      if (op === 0x1 || op === 0x2) { frags = [payload]; fragOp = op; }
      else if (op === 0x0) { frags.push(payload); }
      if (fin) {
        const full = Buffer.concat(frags); frags = [];
        if (fragOp === 0x1) { try { onMessage(conn, full.toString('utf8')); } catch (e) {} }
      }
    }
  });
  socket.on('close', () => onClose(conn));
  socket.on('error', () => onClose(conn));
});

function sendFrame(socket, op, payload) {
  const len = payload.length;
  let header;
  if (len < 126) { header = Buffer.from([0x80 | op, len]); }
  else if (len < 65536) { header = Buffer.allocUnsafe(4); header[0] = 0x80 | op; header[1] = 126; header.writeUInt16BE(len, 2); }
  else { header = Buffer.allocUnsafe(10); header[0] = 0x80 | op; header[1] = 127; header.writeBigUInt64BE(BigInt(len), 2); }
  try { socket.write(Buffer.concat([header, payload])); } catch (e) {}
}
function sendRaw(socket, str) { sendFrame(socket, 0x1, Buffer.from(str, 'utf8')); }
function sendObj(socket, obj) { sendRaw(socket, JSON.stringify(obj)); }

/* ---------------- 시작 ---------------- */
server.listen(PORT, () => {
  console.log('=====================================');
  console.log('  우서 월드 온라인 서버 시작!');
  console.log('  이 PC:        http://localhost:' + PORT);
  console.log('  같은 와이파이: http://<이 PC IP>:' + PORT);
  console.log('=====================================');
});
