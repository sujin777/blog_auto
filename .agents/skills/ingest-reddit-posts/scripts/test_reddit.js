const path = require('path');
// .env 환경변수 수동 파싱 및 process.env 주입 (dotenv 설치 생략 가능성 고려)
try {
  const fs = require('fs');
  const envPath = path.join(__dirname, '../../../../.env');
  if (fs.existsSync(envPath)) {
    const envConfig = fs.readFileSync(envPath, 'utf8');
    envConfig.split('\n').forEach(line => {
      const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
      if (match) {
        const key = match[1];
        let value = match[2] || '';
        if (value.length > 0 && value.charAt(0) === '"' && value.charAt(value.length - 1) === '"') {
          value = value.replace(/\\n/gm, '\n');
        }
        process.env[key] = value.replace(/(^['"]|['"]$)/g, '').trim();
      }
    });
  }
} catch (e) {
  console.warn('환경 변수 설정 중 오류 발생:', e.message);
}

const { fetchRedditTrends } = require('./reddit_posts');
const log = require('../../../../logger');

(async () => {
  log.section('Reddit Ingestion Test Runner');
  try {
    const posts = await fetchRedditTrends();
    log.ok(`총 ${posts.length}개의 어제자 탑 게시물이 성공적으로 수집 및 가공되었습니다.`);
  } catch (err) {
    log.err(`테스트 실행 중 치명적 에러 발생: ${err.message}`);
  }
})();
