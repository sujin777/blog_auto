const fs = require('fs');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');

// 명령어 인자 처리
const args = process.argv.slice(2);
let mdFilePath = '';

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--md-file' && args[i + 1]) {
    mdFilePath = args[i + 1];
    break;
  }
}

if (!mdFilePath) {
  console.error('❌ 에러: --md-file 인자가 누락되었습니다.');
  console.log('사용법: node .agents/skills/publish-to-tistory/scripts/upload_images.js --md-file <마크다운_파일_경로>');
  process.exit(1);
}

const mdAbsPath = path.resolve(mdFilePath);
if (!fs.existsSync(mdAbsPath)) {
  console.error(`❌ 에러: 파일을 찾을 수 없습니다: ${mdAbsPath}`);
  process.exit(1);
}

const mdDir = path.dirname(mdAbsPath);
let content = fs.readFileSync(mdAbsPath, 'utf8');

// .env 환경변수 수동 파싱 및 process.env 주입
try {
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
  console.warn('⚠️ 환경 변수 설정 중 오류 발생:', e.message);
}

const blogName = process.env.TISTORY_BLOG_NAME || 'your-blog-name';

// 동적 쿠키 파일 로딩 시도 (scratch/cookies.json)
let cookieStr = '__T_=1; __T_SECURE=1;';
try {
  const cookieJsonPath = path.join(__dirname, '../../../../scratch/cookies.json');
  if (fs.existsSync(cookieJsonPath)) {
    const cookies = JSON.parse(fs.readFileSync(cookieJsonPath, 'utf8'));
    cookieStr = Object.entries(cookies).map(([k, v]) => `${k}=${v}`).join('; ');
    console.log('🔑 scratch/cookies.json 에서 최신 세션 쿠키를 성공적으로 로드했습니다.');
  } else {
    console.warn('⚠️ scratch/cookies.json 파일이 없습니다. 기존 기본 쿠키를 적용합니다.');
  }
} catch (e) {
  console.warn('⚠️ 쿠키 파일 로드 오류:', e.message);
}

const HEADERS = {
  'Accept': 'application/json, text/plain, */*',
  'Cookie': cookieStr,
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
  'Origin': `https://${blogName}.tistory.com`,
  'Referer': `https://${blogName}.tistory.com/manage/newpost/15?type=post`
};


async function uploadImage(imagePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(imagePath));

  try {
    const response = await axios.post(
      `https://${blogName}.tistory.com/manage/post/attach.json`,
      form,
      {
        headers: {
          ...HEADERS,
          ...form.getHeaders()
        }
      }
    );

    if (response.status === 200 && response.data) {
      const { key, filename } = response.data;
      if (key && filename) {
        return `[##_Image|kage@${key}/${filename}|alignCenter|width="100%"|_##]`;
      }
    }
    console.error(`⚠️ 업로드 실패 (응답 데이터 이상):`, response.data);
  } catch (error) {
    console.error(`❌ 업로드 API 요청 중 에러 발생 (${imagePath}):`, error.message);
    if (error.response) {
      console.error(`  - 응답 코드: ${error.response.status}`);
      console.error(`  - 응답 데이터:`, error.response.data);
    }
  }
  return null;
}

async function main() {
  // 본문 이미지 패턴 매칭 (![alt](path))
  const imageRegex = /!\[(.*?)\]\((.*?)\)/g;
  const matches = [];
  let match;

  while ((match = imageRegex.exec(content)) !== null) {
    const [fullMatch, altText, imgPath] = match;
    // 외부 URL은 제외하고 로컬 경로만 추출
    if (!imgPath.startsWith('http://') && !imgPath.startsWith('https://')) {
      matches.push({ fullMatch, altText, imgPath });
    }
  }

  if (matches.length === 0) {
    console.log('ℹ️ 본문 내에 업로드할 로컬 이미지가 없습니다.');
    const outPath = mdAbsPath.replace('.md', '_replaced.md');
    fs.writeFileSync(outPath, content, 'utf8');
    console.log(`✅ 파일 복사 완료 (치환 없음): ${outPath}`);
    return;
  }

  console.log(`📡 총 ${matches.length}개의 로컬 이미지를 티스토리 서버에 업로드합니다.`);

  let replacedContent = content;

  for (const item of matches) {
    let absImgPath = item.imgPath;
    if (!path.isAbsolute(item.imgPath)) {
      absImgPath = path.resolve(mdDir, item.imgPath);
    }

    if (!fs.existsSync(absImgPath)) {
      console.warn(`⚠️ 경고: 이미지 파일을 찾을 수 없습니다: ${absImgPath}`);
      continue;
    }

    console.log(`📤 업로드 중: ${path.basename(absImgPath)}...`);
    const tistoryTag = await uploadImage(absImgPath);

    if (tistoryTag) {
      console.log(`  └─ ✅ 성공! 치환 태그: ${tistoryTag}`);
      // 기존 마크다운 이미지 태그를 티스토리 이미지 태그로 치환
      replacedContent = replacedContent.replace(item.fullMatch, tistoryTag);
    } else {
      console.log(`  └─ ❌ 업로드 실패: ${path.basename(absImgPath)}`);
    }
  }

  const outPath = mdAbsPath.replace('.md', '_replaced.md');
  fs.writeFileSync(outPath, replacedContent, 'utf8');
  console.log(`\n🎉 업로드 및 치환 완료! 결과 파일: ${outPath}`);
}

main();
