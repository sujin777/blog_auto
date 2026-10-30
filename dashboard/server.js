const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');

const PORT = 3000;
const DASHBOARD_DIR = __dirname;
const ROOT_DIR = path.resolve(DASHBOARD_DIR, '..');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8'
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = decodeURIComponent(url.pathname);

  // 1. API: 최신 생성된 마크다운 포스트 목록 조회
  if (pathname === '/api/posts' && req.method === 'GET') {
    const outputDir = path.join(ROOT_DIR, 'output');
    const results = [];
    if (fs.existsSync(outputDir)) {
      const folders = fs.readdirSync(outputDir).filter(f => f.startsWith('2') && fs.statSync(path.join(outputDir, f)).isDirectory());
      folders.sort().reverse();
      for (const f of folders) {
        const fPath = path.join(outputDir, f);
        const files = fs.readdirSync(fPath).filter(file => file.endsWith('.md') && file !== 'ingest.md');
        for (const file of files) {
          results.push({
            folder: f,
            filename: file,
            path: `output/${f}/${file}`
          });
        }
      }
    }
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify({ success: true, posts: results }));
  }

  // 1-0. API: 기획 주제 영구 보존 조회 및 저장
  if (pathname === '/api/topics') {
    const topicsFile = path.join(DASHBOARD_DIR, 'topics.json');
    if (req.method === 'GET') {
      let topics = [];
      if (fs.existsSync(topicsFile)) {
        try {
          topics = JSON.parse(fs.readFileSync(topicsFile, 'utf-8'));
        } catch (e) {
          topics = [];
        }
      }
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ success: true, topics }));
    }

    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        try {
          const data = JSON.parse(body || '{}');
          const topics = Array.isArray(data.topics) ? data.topics : [];
          fs.writeFileSync(topicsFile, JSON.stringify(topics, null, 2), 'utf-8');
          console.log(`[기획 주제 영구 보존 완료] 총 ${topics.length}개 주제 저장됨`);
          res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
          return res.end(JSON.stringify({ success: true, topics }));
        } catch (err) {
          res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
          return res.end(JSON.stringify({ success: false, error: err.message }));
        }
      });
      return;
    }
  }

  // 1-1. API: 특정 마크다운 포스트 내용 조회
  if (pathname === '/api/post-content' && req.method === 'GET') {
    const fileRel = url.searchParams.get('file');
    if (!fileRel) {
      res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ success: false, error: 'No file specified' }));
    }
    const absPath = path.resolve(ROOT_DIR, fileRel);
    if (!absPath.startsWith(ROOT_DIR) || !fs.existsSync(absPath)) {
      res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ success: false, error: 'File not found' }));
    }
    const content = fs.readFileSync(absPath, 'utf-8');
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify({ success: true, file: fileRel, content }));
  }

  // 1-2. API: 마크다운 포스트 본문 수정 및 저장
  if (pathname === '/api/save-post' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const data = JSON.parse(body || '{}');
        const fileRel = data.file;
        const newContent = data.content;

        if (!fileRel || typeof newContent !== 'string') {
          res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
          return res.end(JSON.stringify({ success: false, error: 'file and content are required' }));
        }

        const absPath = path.resolve(ROOT_DIR, fileRel);
        if (!absPath.startsWith(ROOT_DIR) || !fs.existsSync(absPath)) {
          res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' });
          return res.end(JSON.stringify({ success: false, error: 'File not found' }));
        }

        fs.writeFileSync(absPath, newContent, 'utf-8');
        console.log(`[포스트 수정 저장 완료] ${fileRel} (${newContent.length} chars)`);

        res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
        return res.end(JSON.stringify({ success: true, message: 'Saved successfully', file: fileRel }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
        return res.end(JSON.stringify({ success: false, error: err.message }));
      }
    });
    return;
  }

  // 2. API: 수동 네이버 블로그 발행 트리거
  if (pathname === '/api/publish' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const data = JSON.parse(body || '{}');
        const mdFile = data.file;
        const mode = data.mode || 'publish'; // 'publish' or 'draft'

        if (!mdFile) {
          res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
          return res.end(JSON.stringify({ success: false, error: 'No file specified' }));
        }

        const absMdPath = path.resolve(ROOT_DIR, mdFile);
        if (!fs.existsSync(absMdPath)) {
          res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' });
          return res.end(JSON.stringify({ success: false, error: 'File not found' }));
        }

        const scriptPath = path.join(ROOT_DIR, '.agents', 'skills', 'publish-to-naver', 'scripts', 'naver_publish.py');
        const args = ['python', `"${scriptPath}"`, `--md-file "${absMdPath}"`, '--headed'];
        if (mode === 'publish') args.push('--publish');

        const cmd = args.join(' ');
        console.log(`[수동 발행 실행] ${cmd}`);

        exec(cmd, { cwd: ROOT_DIR }, (err, stdout, stderr) => {
          if (err) {
            console.error('[발행 에러]', err.message);
            res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
            return res.end(JSON.stringify({ success: false, error: err.message, log: stdout }));
          }
          console.log('[발행 성공]', stdout);
          res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
          return res.end(JSON.stringify({ success: true, log: stdout }));
        });
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify({ success: false, error: e.message }));
      }
    });
    return;
  }

  // 3. 정적 파일 서빙 (대시보드 및 output 하위 이미지)
  let filePath = path.join(DASHBOARD_DIR, pathname === '/' ? 'index.html' : pathname);
  
  // output/ 디렉토리 요청 지원
  if (pathname.startsWith('/output/')) {
    filePath = path.join(ROOT_DIR, pathname);
  }

  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    return fs.createReadStream(filePath).pipe(res);
  }

  res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('404 Not Found');
});

server.listen(PORT, () => {
  console.log(`=======================================================`);
  console.log(`  🤖 블로그 모니터링 대시보드 로컬 서버 시작됨`);
  console.log(`  👉 접속 주소: http://localhost:${PORT}`);
  console.log(`=======================================================`);
});
