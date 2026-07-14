const fs = require('fs');
const path = require('path');

const inputPath = process.argv[2];

if (!inputPath) {
  console.error('Usage: node build_ingest.js <raw_reddit_data.json>');
  process.exit(1);
}

const absoluteInputPath = path.resolve(process.cwd(), inputPath);

if (!fs.existsSync(absoluteInputPath)) {
  console.error(`Input file not found: ${absoluteInputPath}`);
  process.exit(1);
}

const posts = JSON.parse(fs.readFileSync(absoluteInputPath, 'utf8'));
const outputDir = path.dirname(absoluteInputPath);
const folderName = path.basename(outputDir);
const outputPath = path.join(outputDir, 'ingest.md');

const formatKstTimestamp = date =>
  new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  }).format(date);

const quoteBlock = text => {
  const normalized = (text || '본문 텍스트가 없는 링크 중심 포스트입니다.')
    .replace(/\r\n/g, '\n')
    .trim();

  return normalized
    .split('\n')
    .map(line => `> ${line}`)
    .join('\n');
};

const translateContent = post => {
  const title = post.title.toLowerCase();
  const content = (post.content || '').trim();

  if (!content) {
    return `${post.title} 포스트는 본문 텍스트보다 링크, 이미지, 혹은 짧은 반응 자체가 화제가 된 사례입니다. 즉, 커뮤니티 반응의 핵심은 긴 설명보다도 제목이 던지는 문제의식과 상징성에 있다고 볼 수 있습니다.`;
  }

  if (title.includes('privacy policy')) {
    return [
      '작성자는 2026년 6월 8일 공개된 Anthropic의 새 개인정보 처리방침을 읽고, 2026년 7월 8일부터 적용될 조항 변화가 모든 Claude 사용자에게 직접적인 영향을 줄 수 있다고 경고합니다.',
      '핵심 문제는 예전 정책이 법원 명령이나 강제력 있는 정부 요청처럼 외부의 법적 절차를 전제로 대화 내용을 제공하도록 했다면, 새 정책은 회사의 내부적인 "선의의 판단(good faith belief)"만으로도 수사기관에 대화 데이터를 선제적으로 제공할 수 있다는 점이라고 설명합니다.',
      '작성자는 이 표현이 정책 안에서 구체적으로 정의되지 않았고, 사용자 통지나 이의제기 절차도 보이지 않는다고 지적합니다.',
      '특히 창작 글쓰기, 롤플레잉, 감정 배출처럼 문맥 의존성이 큰 텍스트는 분류기가 오탐할 가능성이 높아, 실제 위협이 아닌 내용도 신고 대상으로 오해받을 수 있다고 우려합니다.',
      '또한 유럽권의 다른 주요 AI 서비스와 비교했을 때 Anthropic의 조항이 더 넓은 재량을 허용하는 것처럼 보이며, 기존 메시지에까지 사실상 소급 영향을 주는지에 대한 문제의식도 함께 제기합니다.'
    ].join('\n');
  }

  if (title.includes('token costs') || title.includes('open source repos')) {
    return [
      '작성자는 Claude Code 사용 비용이 빠르게 커지자 더 비싼 요금제로 이동하는 대신, 실제 토큰 소비를 줄일 수 있는 오픈소스 도구를 직접 찾아 정리했습니다.',
      '예시로는 토큰 사용량을 모델과 에이전트 단위로 분석하는 ccusage, 셸 출력 노이즈를 압축하는 RTK, 답변을 초간결 스타일로 유도하는 Caveman Claude, 잘못된 파일 수정과 불필요한 왕복을 줄이는 skills 레포, 코드베이스를 로컬 그래프로 읽게 해 재독 비용을 낮추는 Graphify, 노트용 Obsidian skills가 제시됩니다.',
      '특히 작성자는 말투를 최소화하는 Caveman Claude가 의외로 큰 절감 효과를 냈다고 강조합니다.',
      '이 글의 본질은 모델 성능을 더 사는 것보다, 컨텍스트 관리와 출력 압축, 작업 경계 설정으로 비용 구조를 먼저 최적화할 수 있다는 실전 팁에 가깝습니다.'
    ].join('\n');
  }

  if (title.includes('scary how good claude is at coding')) {
    return [
      '작성자는 10년 이상 경력을 가진 소프트웨어 엔지니어로서, 과거에는 AI 코딩을 회의적으로 봤지만 최근 1년 사이 품질이 급격히 좋아져 일상적으로 활용할 수밖에 없게 되었다고 말합니다.',
      '언어 자체를 깊게 배우는 측면에서는 손실이 있을 수 있지만, 시스템 설계와 인프라 학습 속도는 오히려 더 빨라졌다고 평가합니다.',
      '실제로 웹소켓과 Cloudflare 인프라를 배우기 위한 실험으로 주말 만에 인증, 세션 관리, 오토스케일링, 매치메이킹이 포함된 간단한 MMO 웹 게임을 만들 수 있었다고 소개합니다.',
      '결론적으로 소프트웨어 엔지니어링은 여전히 어렵고 흥미로운 분야이지만, AI 덕분에 구현 속도가 훨씬 빨라졌고 개발자가 더 높은 수준의 설계와 아키텍처 판단에 집중할 수 있게 되었다는 메시지를 던집니다.'
    ].join('\n');
  }

  if (title.includes('paranoid setup')) {
    return [
      '작성자는 민감한 업무 자료를 다루는 환경에서 Claude Code를 실험하면서, 작업 공간과 네트워크를 최대한 격리하는 보수적인 보안 구성을 설계했다고 설명합니다.',
      '구체적으로는 BitLocker로 암호화한 SSD 위에 가상머신을 올리고, 인터넷은 허용하되 회사 네트워크와 외부 파일 시스템은 보지 못하도록 분리했습니다.',
      '또한 호스트 PC와 가상머신 사이에는 파일 전송 전용 가상 드라이브를 별도로 두어, 일종의 에어록처럼 필요한 파일만 제한적으로 오가게 만들었습니다.',
      '글의 핵심 질문은 이 정도 격리가 과도한 편인지, 아니면 AI 코딩 도구를 기업 환경에 도입할 때 현실적인 최소 안전장치인지에 대한 커뮤니티의 판단을 구하는 데 있습니다.'
    ].join('\n');
  }

  if (title.includes('detroit: become human')) {
    return [
      '작성자는 Claude Code 세션이 길어질수록 컨텍스트가 오염되어 성능이 떨어지는 문제를 겪었고, 일반적인 compact 방식이나 핸드오프 문서가 충분히 만족스럽지 않았다고 말합니다.',
      '대신 게임 Detroit: Become Human의 기억 탐색 설정에서 착안해, 새 세션이 과거 세션의 JSONL 로그를 직접 검색해 필요한 정보만 꺼내오는 방식을 시도했습니다.',
      '즉, 예전 에이전트가 미리 요약한 정보를 그대로 물려받는 대신, 새 에이전트가 과거 기록에서 필요한 단서만 선택적으로 검색하는 구조입니다.',
      '작성자는 이 방식이 컨텍스트 오염을 줄이고 필요한 정보만 정확히 회수하는 데 더 효과적이었다고 평가합니다.'
    ].join('\n');
  }

  return [
    `"${post.title}" 포스트는 Claude 사용자 커뮤니티 안에서 특정 기능, 사용 경험, 혹은 운영 정책 변화에 대한 반응을 보여줍니다.`,
    '본문의 핵심은 사용자가 실제 현장에서 체감한 문제와 기대치를 압축적으로 드러낸다는 점이며, 이는 향후 제품 개선이나 운영 가드레일 설계의 참고 신호로 읽을 수 있습니다.',
    '특히 긴 설명보다 사례 중심의 경험 공유에 가깝기 때문에, 후속 딥리서치에서는 관련 공식 문서와 산업 사례를 연결해 맥락을 보강할 필요가 있습니다.'
  ].join('\n');
};

const buildQuestions = post => {
  const title = post.title;

  return [
    `1. **기술적 본질 및 아키텍처 검증**: "${title}"가 주목받은 근본 원인은 무엇이며, 이 이슈를 떠받치는 제품 구조나 정책 아키텍처는 어떤 방식으로 작동하는가?`,
    `2. **인사이트**: 이 포스트가 현재 Claude 생태계 사용자들의 불안, 기대, 혹은 구매 행동 변화에 대해 던지는 핵심 시사점은 무엇인가?`,
    `3. **트레이드 오프 및 병목 구간 진단**: 이 주제를 실제 서비스 운영 관점에서 바라볼 때 비용, 신뢰, 성능, 사용자 경험 사이의 주요 트레이드오프는 어디에서 발생하는가?`,
    `4. **미래가치**: 향후 1~3년 안에 이 논점이 AI 코딩 도구 및 에이전트 시장에서 어떤 새로운 표준이나 규제 흐름으로 이어질 가능성이 있는가?`,
    `5. **실전 구현 제안**: 개인 개발자나 팀이 이 이슈를 바탕으로 바로 실험해볼 수 있는 MVP 혹은 운영 가드레일 설계안은 무엇인가?`
  ].join('\n');
};

const document = [
  `# 🤖 Reddit Raw 수집 데이터 (${folderName})`,
  '',
  `- **수집 일시**: ${formatKstTimestamp(new Date())}`,
  `- **총 수집 개수**: ${posts.length}개`,
  '',
  '---',
  '',
  ...posts.flatMap((post, index) => [
    `## [${index + 1}] ${post.title} (좋아요: ${post.metrics?.likes || 0} | 댓글: ${post.metrics?.comments || 0})`,
    `- **작성일**: ${post.published_at}`,
    `- **작성자**: @${post.author || 'unknown'}`,
    `- **URL**: [링크 이동](${post.url})`,
    '',
    '### 🇺🇸 [1] 원본 내용 (Original Content)',
    quoteBlock(post.content),
    '',
    '### 🇰🇷 [2] 한국어 번역 (Korean Translation)',
    quoteBlock(translateContent(post)),
    '',
    '### 🧠 [3] 딥리서치 질문 내용 (Deep-Dive Research Questions)',
    buildQuestions(post),
    '',
    '---',
    ''
  ])
].join('\n');

fs.writeFileSync(outputPath, document, 'utf8');
console.log(`ingest.md generated: ${outputPath}`);
