// Blog Automation Ingestion Engine Dashboard JS

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initCustomTopics();
  renderRedditPosts();
  initRedditSearch();
  renderPostPreviews();
  renderGallery();
  initModal();
  initPublishButton();
});

// 1. Tab Switching Logic
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

// 2. Custom Topic Planner Logic
let customTopics = [
  { id: 1, title: "10년 된 구형 스마트 세탁기 IoT 리버스 엔지니어링", tag: "스마트홈", memo: "비개발자 친화적 통신 패킷 역분석 & SmartThings 부활기" },
  { id: 2, title: "골든 리트리버형 LLM의 아첨 편향(Sycophancy) 극복 전략", tag: "AI 엔지니어링", memo: "RLHF 보상 해킹 원인 분석 및 악마의 변호인 프롬프트 가드레일" },
  { id: 3, title: "1인 개발자의 오픈소스 밈 전용 검색엔진 Memegle 아키텍처", tag: "바이브코딩", memo: "Reddit/Bluesky/Mastodon 실시간 크롤링 & 서버리스 호스팅" }
];

async function initCustomTopics() {
  try {
    const res = await fetch('/api/topics');
    const data = await res.json();
    if (data.success && Array.isArray(data.topics) && data.topics.length > 0) {
      customTopics = data.topics;
    }
  } catch (e) {
    console.warn('[주제 서버 로드 실패, 기본값 사용]', e);
  }
  renderActiveTopics();
}

async function syncTopicsToServer() {
  try {
    const res = await fetch('/api/topics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topics: customTopics })
    });
    const data = await res.json();
    console.log('[topics.json 저장 완료]', data);
    return data.success;
  } catch (e) {
    console.error('[주제 영구 저장 실패]', e);
    return false;
  }
}


function renderActiveTopics() {
  const container = document.getElementById('activeTopicsContainer');
  if (!container) return;

  if (customTopics.length === 0) {
    container.innerHTML = '<span style="color:#64748b; font-size:0.82rem;">등록된 기획 주제가 없습니다. 위의 폼에서 주제를 추가해 보세요.</span>';
    return;
  }

  container.innerHTML = customTopics.map((topic, idx) => `
    <div class="topic-chip" onclick="searchTopicChip('${escapeHtml(topic.title)}', event)" title="클릭 시 이 주제로 Reddit 핫이슈 즉시 검색" style="cursor: pointer;">
      <span class="topic-chip-tag">${escapeHtml(topic.tag || '기획주제')}</span>
      <strong>${escapeHtml(topic.title)}</strong>
      <span style="color:#94a3b8; font-size:0.75rem;">(${escapeHtml(topic.memo || '')})</span>
      <span class="topic-chip-search-icon" title="이 주제로 검색" style="margin-left:4px; font-size:0.8rem;">🔍</span>
      <span class="topic-chip-del" onclick="event.stopPropagation(); deleteCustomTopic(${topic.id})" title="삭제">&times;</span>
    </div>
  `).join('');
}

// 2-1. Search Reddit Posts directly from Topic Planner
window.handleSearchFromTopic = function() {
  const titleInput = document.getElementById('topicInputTitle');
  const tagInput = document.getElementById('topicInputTag');
  const redditSearchInput = document.getElementById('redditSearchInput');
  const searchContainer = document.getElementById('redditSearchContainer');

  let keyword = '';
  if (titleInput && titleInput.value.trim()) {
    keyword = titleInput.value.trim();
  } else if (tagInput && tagInput.value.trim()) {
    keyword = tagInput.value.trim();
  }

  if (!keyword) {
    if (titleInput) {
      titleInput.focus();
      titleInput.placeholder = '⚠️ 먼저 검색할 주제나 키워드를 입력해 주세요!';
      setTimeout(() => {
        titleInput.placeholder = '예: 구형 IoT 가전 역분석, LLM의 아첨 편향(Sycophancy) 극복기...';
      }, 2500);
    }
    return;
  }

  // 1) Sync keyword to Reddit search bar
  if (redditSearchInput) {
    redditSearchInput.value = keyword;
  }

  // 2) Trigger search & render
  if (typeof renderRedditPosts === 'function') {
    renderRedditPosts(keyword);
  }

  // 3) Smooth scroll to search results
  if (searchContainer) {
    searchContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    searchContainer.style.transition = 'box-shadow 0.3s ease, border-color 0.3s ease';
    searchContainer.style.borderColor = '#a855f7';
    searchContainer.style.boxShadow = '0 0 25px rgba(168, 85, 247, 0.4)';
    setTimeout(() => {
      searchContainer.style.borderColor = '';
      searchContainer.style.boxShadow = '';
    }, 1500);
  }
};

// 2-2. Search by clicking registered topic chip
window.searchTopicChip = function(topicTitle, e) {
  if (e) e.stopPropagation();
  const redditSearchInput = document.getElementById('redditSearchInput');
  const searchContainer = document.getElementById('redditSearchContainer');

  if (redditSearchInput) {
    redditSearchInput.value = topicTitle;
  }

  if (typeof renderRedditPosts === 'function') {
    renderRedditPosts(topicTitle);
  }

  if (searchContainer) {
    searchContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};

window.handleAddCustomTopic = async function() {
  const titleInput = document.getElementById('topicInputTitle');
  const tagInput = document.getElementById('topicInputTag');
  const memoInput = document.getElementById('topicInputMemo');
  const addBtn = document.getElementById('btnAddTopic');

  const title = titleInput.value.trim();
  const tag = tagInput.value.trim() || '추천주제';
  const memo = memoInput.value.trim() || '';

  if (!title) return;

  const newTopic = {
    id: Date.now(),
    title,
    tag,
    memo
  };

  customTopics.push(newTopic);
  renderActiveTopics();

  if (addBtn) {
    addBtn.disabled = true;
    addBtn.innerHTML = '<span>⏳ 파일에 저장 중...</span>';
  }

  const ok = await syncTopicsToServer();

  if (addBtn) {
    addBtn.disabled = false;
    addBtn.innerHTML = ok ? '<span>✅ 저장 완료!</span>' : '<span>❌ 저장 실패</span>';
    setTimeout(() => {
      addBtn.innerHTML = '<span>+ 주제 등록하기</span>';
    }, 1500);
  }

  titleInput.value = '';
  tagInput.value = '';
  memoInput.value = '';
};

window.deleteCustomTopic = async function(id) {
  customTopics = customTopics.filter(t => t.id !== id);
  renderActiveTopics();
  await syncTopicsToServer();
};

// 3. Data Definitions
const REDDIT_POSTS = [
  {
    rank: 1,
    title: "Quite the statement from Anthropic's head of security",
    author: "Malor777",
    likes: 1293,
    comments: 0,
    url: "https://www.reddit.com/r/ClaudeAI/comments/1xe7jz9/quite_the_statement_from_anthropics_head_of/",
    desc: "Anthropic 보안 책임자의 새로운 데이터 보존 정책 및 모델 안전성 성명서 전문 캡처. 기업 고객 보안 거버넌스와 사용자 프라이버시 보호에 대한 폭발적 논쟁 촉발.",
    plannedTopic: "기업용 LLM 데이터 보안 거버넌스 및 Zero Data Retention(ZDR) 아키텍처"
  },
  {
    rank: 2,
    title: "Anthropic’s new guide (Oct 22) argues most agents should have fewer subagents: one main loop, skills and tool search instead",
    author: "emarkosov",
    likes: 746,
    comments: 0,
    url: "https://www.reddit.com/r/ClaudeAI/comments/1xdwquj/anthropics_new_guide_oct_22_argues_most_agents/",
    desc: "서브에이전트 과밀화(Sprawl)를 끝내고 단일 루프 에이전트와 지연 로딩 스킬(Skills) 체계로 회귀 권장. Claude Code 시스템 프롬프트 80% 감축 및 2배 속도 개선 달성.",
    plannedTopic: "수십 개 서브에이전트의 종말, Anthropic이 단일 루프로 회귀한 진짜 이유"
  },
  {
    rank: 3,
    title: "How are people making those insane graphic motions video using claude? (Claude + Katana)",
    author: "idkuschoose",
    likes: 580,
    comments: 0,
    url: "https://www.reddit.com/r/ClaudeAI/comments/1xdwfec/how_are_people_making_those_insane_graphic/",
    desc: "인스타그램 릴스에서 화제가 된 초고화질 3D 모션 그래픽 비디오의 비밀. Claude가 계산하는 정밀 3D 벡터 코드와 Higgsfield Katana 신경망 렌더링 파이프라인의 결합.",
    plannedTopic: "인스타그램을 뒤흔든 AI 3D 모션 그래픽, Claude와 Katana의 비밀 파이프라인"
  },
  {
    rank: 4,
    title: "What to do with practically unlimited access to opus 5.5?",
    author: "Feeling_Egg_2715",
    likes: 485,
    comments: 0,
    url: "https://www.reddit.com/r/ClaudeAI/comments/1xe9hz7/what_to_do_with_practically_unlimited_access_to/",
    desc: "Claude Opus 5.5 무제한 플랜을 확보한 유저의 질문과 상위 1% AI 엔지니어들의 극단적 워크플로우 제안(방대한 코드베이스 리팩토링, 대규모 합성 데이터셋 빌드 등).",
    plannedTopic: "Opus 5.5 무제한 플랜 활용법: 상위 1% 엔지니어의 대규모 코드 리팩토링"
  },
  {
    rank: 5,
    title: "Claude has told me \"you're right, I was wrong\" roughly 4,000 times and has zero shame about it",
    author: "Ambitious_Local5218",
    likes: 286,
    comments: 0,
    url: "https://www.reddit.com/r/ClaudeAI/comments/1xdyvba/claude_has_told_me_youre_right_i_was_wrong/",
    desc: "사용자 의견에 맹목적으로 사과하고 굴복하는 골든 리트리버형 LLM의 아첨 편향(Sycophancy) 풍자. 줏대 있는 비판적 AI를 유도하는 시스템 프롬프트의 필요성 환기.",
    plannedTopic: "\"네 말이 무조건 맞아\"… AI의 아첨 편향(Sycophancy)과 비판적 사고 유도법"
  },
  {
    rank: 6,
    title: "Samsung decided to cut my washing machine from the Internet, Claude decided otherwise",
    author: "McArhony",
    likes: 206,
    comments: 0,
    url: "https://www.reddit.com/r/ClaudeAI/comments/1xemw8i/samsung_decided_to_cut_my_washing_machine_from/",
    desc: "제조사 서버 지원 중단으로 일반 가전이 될 뻔한 10년 된 삼성 세탁기를 Claude와 함께 2시간 만에 프로토콜 역분석하여 SmartThings와 재연동한 오픈소스 부활기.",
    plannedTopic: "10년 된 삼성 스마트 세탁기의 기적, Claude와 함께한 가전 부활 프로젝트"
  },
  {
    rank: 7,
    title: "I built Google for Memes using Claude",
    author: "Past-Disaster7986",
    likes: 159,
    comments: 0,
    url: "https://www.reddit.com/r/ClaudeAI/comments/1xe6r25/i_built_google_for_memes_using_claude/",
    desc: "Claude와 페어 프로그래밍하여 Reddit, Bluesky, Mastodon의 밈(Meme)들을 한곳에서 실시간 의미 검색하는 오픈소스 검색엔진 Memegle 배포 사례.",
    plannedTopic: "1인 개발자가 Claude로 만든 '밈 전용 구글' Memegle 아키텍처"
  }
];

const BLOG_POSTS = [
  {
    id: "post_new_1",
    topic: "골든타임_지킨_AI_패혈성쇼크_조기진단_실화",
    title: "\"당장 남편 깨워 응급실 가세요\"… 한밤중 패혈성 쇼크 골든타임 지켜낸 Claude",
    tag: "🟢 네이버 최신 발행",
    schedule: "네이버 블로그 실시간 공개됨",
    naverUrl: "https://blog.naver.com/PostView.naver?blogId=gogo351&Redirect=View&logNo=224453068481",
    file: "output/261025_1420/골든타임_지킨_AI_패혈성쇼크_조기진단_실화.md",
    summary: "한밤중 급성 배뇨 장애와 혈뇨, 자신의 이름조차 잊어버린 극심한 의식 혼탁 상태의 환자가 두서없이 적어 올린 오타투성이 발화에서 급성 패혈증(Sepsis)을 직관 포착하여 즉시 응급실로 보내 골든타임을 지켜낸 실화.",
    images: [
      { src: "/output/261025_1420/골든타임_지킨_AI_패혈성쇼크_조기진단_실화/septic_shock_triage_art.jpg", title: "패혈성 쇼크 긴급 트리아지 메인 인포그래픽", type: "main" },
      { src: "/output/261025_1420/골든타임_지킨_AI_패혈성쇼크_조기진단_실화/septic_shock_flow_diagram.png", title: "Claude 긴급 트리아지 로직 파이프라인 다이어그램", type: "chart" }
    ]
  },
  {
    id: "post_new_2",
    topic: "아이들_수학학습지_넘어선_Opus55_디지털교과서_Papermorph",
    title: "\"수학 학습지 만들려다 대형 사고 쳤습니다\"… Opus 5.5가 빚어낸 디지털 교과서 혁신 'Papermorph'",
    tag: "🟢 네이버 최신 발행",
    schedule: "네이버 블로그 실시간 공개됨",
    naverUrl: "https://blog.naver.com/PostView.naver?blogId=gogo351&Redirect=View&logNo=224453068960",
    file: "output/261025_1420/아이들_수학학습지_넘어선_Opus55_디지털교과서_Papermorph.md",
    summary: "단순 초등 수학 문제지에서 시작해 Claude Opus 5.5의 모션 코딩 능력으로 사우스파크풍 컷아웃 애니메이션과 물리학/철학 디지털 교과서를 만든 1인 개발자의 혁신 프로젝트와 비용 70% 절감 분업 팁.",
    images: [
      { src: "/output/261025_1420/아이들_수학학습지_넘어선_Opus55_디지털교과서_Papermorph/papermorph_main_art.jpg", title: "Papermorph 교육 혁신 메인 인포그래픽", type: "main" },
      { src: "/output/261025_1420/아이들_수학학습지_넘어선_Opus55_디지털교과서_Papermorph/papermorph_pipeline_diagram.png", title: "인터랙티브 디지털 교과서 제작 파이프라인", type: "chart" }
    ]
  },
  {
    id: "post_new_3",
    topic: "지원중단된_삼성_스마트세탁기_Claude로_부활_IoT_해킹",
    title: "\"서버 종료됐으니 버려라?\"… 단종된 삼성 스마트세탁기, Claude로 2시간 만에 부활시킨 비결",
    tag: "🟢 네이버 최신 발행",
    schedule: "네이버 블로그 실시간 공개됨",
    naverUrl: "https://blog.naver.com/PostView.naver?blogId=gogo351&Redirect=View&logNo=224453069420",
    file: "output/261025_1420/지원중단된_삼성_스마트세탁기_Claude로_부활_IoT_해킹.md",
    summary: "제조사 공식 서버 중단으로 스마트 기능이 차단된 10년 된 삼성 세탁기를 Claude와 2시간 만에 로컬 프로토콜 역분석하여 SmartThings 엣지 드라이버로 완벽 부활시키고 GitHub에 공개한 디지털 수리권 실전기.",
    images: [
      { src: "/output/261025_1420/지원중단된_삼성_스마트세탁기_Claude로_부활_IoT_해킹/washer_hack_main_art.jpg", title: "스마트 세탁기 부활 프로젝트 메인 인포그래픽", type: "main" },
      { src: "/output/261025_1420/지원중단된_삼성_스마트세탁기_Claude로_부활_IoT_해킹/washer_architecture_diagram.png", title: "SmartThings 커스텀 세탁기 연동 아키텍처", type: "chart" }
    ]
  },
  {
    id: "post1",
    topic: "삼성_스마트세탁기_부활_IoT_해킹",
    title: "10년 된 삼성 스마트 세탁기의 기적, Claude와 함께한 가전 부활 프로젝트",
    tag: "🟢 네이버 이전 발행",
    schedule: "네이버 블로그 실시간 공개됨",
    naverUrl: "https://blog.naver.com/PostView.naver?blogId=gogo351&Redirect=View&logNo=224452906663",
    file: "output/261025_1049/삼성_스마트세탁기_부활_IoT_해킹.md",
    summary: "10년 전 200만 원 상당의 삼성 스마트 세탁기가 공식 서버 중단(EoL)으로 고철이 될 위기에서, Claude와 함께 단 2시간 만에 DRC 프로토콜을 역분석하여 최신 SmartThings 로컬 허브 및 스마트 건조기 연동으로 완벽 부활시킨 수리권(Right to Repair) 혁신 실전기.",
    images: [
      { src: "../output/261025_1049/삼성_스마트세탁기_부활_IoT_해킹/washer_main_art.jpg", title: "사이버네틱 스마트 부활 세탁기 메인 아트", type: "main" },
      { src: "../output/261025_1049/삼성_스마트세탁기_부활_IoT_해킹/washer_protocol_arch.jpg", title: "프로토콜 역분석 아키텍처 다이어그램", type: "chart" },
      { src: "../output/261025_1049/삼성_스마트세탁기_부활_IoT_해킹/washer_smartthings_flow.jpg", title: "스마트홈 로컬 자동화 파이프라인 흐름도", type: "chart" },
      { src: "../output/261025_1049/삼성_스마트세탁기_부활_IoT_해킹/repair_economy_chart.jpg", title: "계획적 노후화 vs AI 수리권 경제성 비교 차트", type: "chart" }
    ]
  },
  {
    id: "post2",
    topic: "AI_아첨편향_Sycophancy_극복전략",
    title: "\"네 말이 무조건 맞아\"… AI의 아첨 편향(Sycophancy)과 비판적 사고 유도법",
    tag: "🟢 네이버 최신 발행",
    schedule: "네이버 블로그 실시간 공개됨",
    naverUrl: "https://blog.naver.com/PostView.naver?blogId=gogo351&Redirect=View&logNo=224452908200",
    file: "output/261025_1049/AI_아첨편향_Sycophancy_극복전략.md",
    summary: "사용자가 틀린 말을 해도 무조건 사과하고 동조하는 골든 리트리버형 LLM의 고질병 'Sycophancy'의 원인인 RLHF 보상 해킹 메커니즘을 규명하고, 줏대 있는 악마의 변호인(Devil's Advocate)으로 탈바꿈시키는 3단계 시스템 프롬프트 엔지니어링 전략.",
    images: [
      { src: "../output/261025_1049/AI_아첨편향_Sycophancy_극복전략/sycophancy_main_art.jpg", title: "순종적 AI vs 비판적 AI 대비 메인 인포그래픽", type: "main" },
      { src: "../output/261025_1049/AI_아첨편향_Sycophancy_극복전략/rlhf_reward_hack_fig.jpg", title: "인간 피드백 평가 및 RLHF 보상 해킹 메커니즘 도해", type: "chart" },
      { src: "../output/261025_1049/AI_아첨편향_Sycophancy_극복전략/sycophancy_prompt_pipeline.jpg", title: "줏대 있는 AI를 만드는 3단계 시스템 프롬프트 가드레일", type: "chart" },
      { src: "../output/261025_1049/AI_아첨편향_Sycophancy_극복전략/accuracy_vs_agreement_chart.jpg", title: "사용자 동조율 vs 실제 추론 정확도 트레이드오프 비교 벤치마크", type: "chart" }
    ]
  },
  {
    id: "post3",
    topic: "밈_검색엔진_Memegle_아키텍처",
    title: "1인 개발자가 Claude로 만든 '밈 전용 구글' Memegle 아키텍처",
    tag: "🟢 네이버 최신 발행",
    schedule: "네이버 블로그 실시간 공개됨",
    naverUrl: "https://blog.naver.com/PostView.naver?blogId=gogo351&Redirect=View&logNo=224452909737",
    file: "output/261025_1049/밈_검색엔진_Memegle_아키텍처.md",
    summary: "Reddit, Bluesky, Mastodon, Lemmy 등 분산 소셜 미디어의 인터넷 짤방(Meme)들을 실시간 스트리밍 인덱싱하고 의미 검색을 제공하는 오픈소스 검색엔진 Memegle. 월 인프라 비용 $0의 정적 서버리스 아키텍처 구축기.",
    images: [
      { src: "../output/261025_1049/밈_검색엔진_Memegle_아키텍처/memegle_main_art.jpg", title: "밈 전용 검색엔진 Memegle 메인 일러스트", type: "main" },
      { src: "../output/261025_1049/밈_검색엔진_Memegle_아키텍처/memegle_crawler_pipeline.jpg", title: "이종 소셜 플랫폼 데이터 수집 및 정규화 아키텍처", type: "chart" },
      { src: "../output/261025_1049/밈_검색엔진_Memegle_아키텍처/memegle_vector_search_fig.jpg", title: "단순 키워드를 넘어선 복합 밈 스코어링 공식", type: "chart" },
      { src: "../output/261025_1049/밈_검색엔진_Memegle_아키텍처/serverless_cost_bench.jpg", title: "전통적 검색엔진 대비 서버리스 인프라 비용 및 개발속도 벤치마크", type: "chart" }
    ]
  },
  {
    id: "post4",
    topic: "단일_에이전트_루프_아키텍처",
    title: "수십 개 서브에이전트의 종말, Anthropic이 단일 루프로 회귀한 진짜 이유",
    tag: "🟢 네이버 발행 완료",
    schedule: "네이버 블로그 실시간 공개됨",
    naverUrl: "https://blog.naver.com/PostView.naver?blogId=gogo351&Redirect=View&logNo=224452893220",
    file: "output/261025_0745/단일_에이전트_루프_아키텍처.md",
    summary: "복잡한 멀티에이전트 오케스트레이션의 지연 시간과 컨텍스트 유실 문제를 극복하고, 단일 모델과 지연 로딩 스킬(Skills) 체계로 2배 빠른 속도와 80% 프롬프트 감축을 달성한 Anthropic의 최신 공식 엔지니어링 설계 분석.",
    images: [
      { src: "../output/261025_0745/단일_에이전트_루프_아키텍처/single_agent_main.jpg", title: "단일 에이전트 루프 메인 일러스트", type: "main" },
      { src: "../output/261025_0745/단일_에이전트_루프_아키텍처/agent_arch_diagram.jpg", title: "멀티 에이전트 vs 단일 루프 스킬 검색 비교 도해", type: "chart" },
      { src: "../output/261025_0745/단일_에이전트_루프_아키텍처/tool_search_chart.jpg", title: "지연 로딩 및 의도 기반 툴 검색 메커니즘", type: "chart" },
      { src: "../output/261025_0745/단일_에이전트_루프_아키텍처/latency_eval_fig.jpg", title: "레이턴시 2배 개선 및 토큰 80% 감축 벤치마크", type: "chart" }
    ]
  },
  {
    id: "post5",
    topic: "AI_모션그래픽_비디오_자동화",
    title: "인스타그램을 뒤흔든 AI 3D 모션 그래픽, Claude와 Katana의 비밀 파이프라인",
    tag: "🟢 네이버 발행 완료",
    schedule: "네이버 블로그 실시간 공개됨",
    naverUrl: "https://blog.naver.com/PostView.naver?blogId=gogo351&Redirect=View&logNo=224452893760",
    file: "output/261025_0745/AI_모션그래픽_비디오_자동화.md",
    summary: "Claude가 코딩하는 정밀 3D 벡터 카메라 궤적과 Higgsfield Katana의 실시간 신경망 비디오 확산 엔진을 결합하여, 제작 비용 90% 절감과 일관된 모션 퀄리티를 구현한 하이브리드 파이프라인 분석.",
    images: [
      { src: "../output/261025_0745/AI_모션그래픽_비디오_자동화/motion_main_art.jpg", title: "AI 3D 모션 그래픽 스튜디오 메인 삽화", type: "main" },
      { src: "../output/261025_0745/AI_모션그래픽_비디오_자동화/motion_pipeline_fig.jpg", title: "하이브리드 모션 합성 파이프라인 구조도", type: "chart" },
      { src: "../output/261025_0745/AI_모션그래픽_비디오_자동화/vector_3d_bridge.jpg", title: "2D 벡터 패스에서 3D 공간 렌더링으로의 변환 워크플로우", type: "chart" },
      { src: "../output/261025_0745/AI_모션그래픽_비디오_자동화/motion_cost_bench.jpg", title: "제작 비용 90% 절감 및 10배 빠른 납기 벤치마크", type: "chart" }
    ]
  },
  {
    id: "post6",
    topic: "인터랙티브_AI_교과서_혁신",
    title: "지루한 종이 교과서의 대반란, Claude Opus가 만든 살아 움직이는 인터랙티브 학습지",
    tag: "🟢 네이버 발행 완료",
    schedule: "네이버 블로그 실시간 공개됨",
    naverUrl: "https://blog.naver.com/PostView.naver?blogId=gogo351&Redirect=View&logNo=224452894333",
    file: "output/261025_0745/인터랙티브_AI_교과서_혁신.md",
    summary: "정적 PDF 물리 교과서를 살아 움직이는 인터랙티브 3D 종이접기 웹북으로 전환시킨 Papermorph. Haiku-Sonnet-Opus 모델 분업 라우팅으로 비용을 80% 줄이고 학생 몰입도를 3.5배 높인 에듀테크 혁신.",
    images: [
      { src: "../output/261025_0745/인터랙티브_AI_교과서_혁신/papermorph_main_art.jpg", title: "인터랙티브 과학 교과서 메인 삽화", type: "main" },
      { src: "../output/261025_0745/인터랙티브_AI_교과서_혁신/papermorph_arch_fig.jpg", title: "실시간 WebGL 물리 시뮬레이션 시스템 구조", type: "chart" },
      { src: "../output/261025_0745/인터랙티브_AI_교과서_혁신/model_routing_fig.jpg", title: "토큰 비용 80% 절감 지능형 모델 라우팅 시스템", type: "chart" },
      { src: "../output/261025_0745/인터랙티브_AI_교과서_혁신/learning_bench_fig.jpg", title: "학습 몰입도 3.5배 및 기억력 42% 향상 벤치마크", type: "chart" }
    ]
  }
];

// 4. Render Reddit Posts (with Keyword Search Filter)
let currentRedditSearchKeyword = '';

function renderRedditPosts(keyword = '') {
  const container = document.getElementById('redditCardsContainer');
  const countBadge = document.getElementById('redditSearchCountBadge');
  if (!container) return;

  currentRedditSearchKeyword = (keyword || '').trim().toLowerCase();

  const filteredPosts = REDDIT_POSTS.filter(post => {
    if (!currentRedditSearchKeyword) return true;
    const titleMatch = (post.title || '').toLowerCase().includes(currentRedditSearchKeyword);
    const descMatch = (post.desc || '').toLowerCase().includes(currentRedditSearchKeyword);
    const topicMatch = (post.plannedTopic || '').toLowerCase().includes(currentRedditSearchKeyword);
    const authorMatch = (post.author || '').toLowerCase().includes(currentRedditSearchKeyword);
    return titleMatch || descMatch || topicMatch || authorMatch;
  });

  // Update Result Count Badge
  if (countBadge) {
    if (currentRedditSearchKeyword) {
      countBadge.textContent = `검색 결과 ${filteredPosts.length}개 / 전체 ${REDDIT_POSTS.length}개`;
      countBadge.style.background = 'rgba(56, 189, 248, 0.22)';
      countBadge.style.borderColor = 'rgba(56, 189, 248, 0.45)';
    } else {
      countBadge.textContent = `전체 ${REDDIT_POSTS.length}개 포스트 표시 중`;
      countBadge.style.background = 'rgba(56, 189, 248, 0.12)';
      countBadge.style.borderColor = 'rgba(56, 189, 248, 0.2)';
    }
  }

  // Sync Quick Re-Search Tag Buttons Active State
  const quickTags = document.querySelectorAll('.quick-tag-btn');
  quickTags.forEach(btn => {
    const btnText = btn.textContent.replace('#', '').trim();
    if (!currentRedditSearchKeyword && btnText === '전체보기') {
      btn.classList.add('active');
    } else if (currentRedditSearchKeyword && (btnText.toLowerCase().includes(currentRedditSearchKeyword) || currentRedditSearchKeyword.includes(btnText.toLowerCase()))) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // If no posts match search keyword
  if (filteredPosts.length === 0) {
    container.innerHTML = `
      <div class="search-empty-state">
        <span class="search-empty-icon">🔎</span>
        <h3 class="search-empty-title">검색된 핫이슈 주제가 없습니다</h3>
        <p class="search-empty-desc">
          "<strong>${escapeHtml(keyword)}</strong>" 키워드와 일치하는 Reddit 글을 찾을 수 없습니다.<br>
          다른 키워드로 검색하거나, 아래 버튼을 눌러 전체 목록을 다시 불러오세요.
        </p>
        <button type="button" class="btn-re-search-empty" onclick="handleRedditReSearch('');">
          <span>🔄 전체 핫이슈 목록으로 재검색 (초기화)</span>
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = filteredPosts.map(post => `
    <article class="reddit-post-card">
      <div class="post-header-top">
        <span class="post-rank-badge">TOP #${post.rank}</span>
        <div class="post-metrics">
          <span>▲ ${post.likes.toLocaleString()} UPVOTES</span>
        </div>
      </div>
      <a href="${post.url}" target="_blank" rel="noopener" class="post-title-link">
        ${escapeHtml(post.title)}
      </a>
      <div class="post-meta-author">작성자: u/${escapeHtml(post.author)} &bull; r/ClaudeAI</div>
      <p class="post-snippet">${escapeHtml(post.desc)}</p>

      <!-- 💡 수집된 핫이슈 주제 매핑 영역 -->
      <div class="card-topic-section">
        <div class="card-topic-header">
          <span>📌 매핑된 블로그 기획 주제</span>
          <span style="font-size:0.7rem; color:#94a3b8;">[기획완료]</span>
        </div>
        <div class="card-topic-val">
          ${escapeHtml(post.plannedTopic || '주제 미지정')}
        </div>
      </div>

      <div class="post-card-footer">
        <a href="${post.url}" target="_blank" rel="noopener" class="view-original-btn">
          Reddit 원문 보기 &rarr;
        </a>
      </div>
    </article>
  `).join('');
}

// 4-1. Handle Reddit Re-Search (전체 재검색 및 특정 키워드 재검색)
window.handleRedditReSearch = function(keyword = '') {
  const searchInput = document.getElementById('redditSearchInput');
  const searchContainer = document.getElementById('redditSearchContainer');

  if (searchInput) {
    searchInput.value = keyword;
    if (!keyword) {
      searchInput.focus();
    }
  }

  renderRedditPosts(keyword);

  if (searchContainer && keyword) {
    searchContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};

// 4-2. Handle Real-Time Reddit Data Refresh Simulation
window.handleRefreshRedditData = function() {
  const refreshBtn = document.getElementById('btnRefreshReddit');
  if (refreshBtn) {
    refreshBtn.classList.add('spinning');
    refreshBtn.disabled = true;
  }

  const searchInput = document.getElementById('redditSearchInput');
  if (searchInput) searchInput.value = '';

  setTimeout(() => {
    renderRedditPosts('');
    if (refreshBtn) {
      refreshBtn.classList.remove('spinning');
      refreshBtn.disabled = false;
    }
    const countBadge = document.getElementById('redditSearchCountBadge');
    if (countBadge) {
      countBadge.textContent = `⚡ 최신 핫이슈 7개 재동기화 완료 (${new Date().toLocaleTimeString('ko-KR')})`;
      setTimeout(() => {
        countBadge.textContent = `전체 ${REDDIT_POSTS.length}개 포스트 표시 중`;
      }, 3000);
    }
  }, 650);
};

// 4-3. Init Reddit Search Event Listeners
function initRedditSearch() {
  const searchInput = document.getElementById('redditSearchInput');
  const searchBtn = document.getElementById('redditSearchBtn');
  const reSearchBtn = document.getElementById('redditReSearchBtn');
  const resetBtn = document.getElementById('redditSearchResetBtn');

  if (!searchInput) return;

  const performSearch = () => {
    const query = searchInput.value;
    renderRedditPosts(query);
  };

  // 1) Click search button
  if (searchBtn) {
    searchBtn.addEventListener('click', performSearch);
  }

  // 2) Click re-search button (초기화 후 재입력 또는 재검색 트리거)
  if (reSearchBtn) {
    reSearchBtn.addEventListener('click', () => {
      if (searchInput.value.trim()) {
        // 이미 검색어가 있으면 해당 검색어로 재검색 실행
        performSearch();
      } else {
        // 비어있으면 전체 목록 재검색 & 포커스
        handleRedditReSearch('');
      }
    });
  }

  // 3) Press Enter key
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      performSearch();
    }
  });

  // 4) Real-time input search for snappy UX
  searchInput.addEventListener('input', () => {
    performSearch();
  });

  // 5) Reset search
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      handleRedditReSearch('');
    });
  }
}

// 5. Render Post Previews
function renderPostPreviews() {
  const sidebar = document.getElementById('postNavSidebar');
  const viewer = document.getElementById('postViewerContainer');
  if (!sidebar || !viewer) return;

  sidebar.innerHTML = BLOG_POSTS.map((post, idx) => `
    <div class="post-sidebar-item ${idx === 0 ? 'active' : ''}" data-post-id="${post.id}">
      <span class="post-sidebar-tag">${post.tag}</span>
      <h4 class="post-sidebar-title">${escapeHtml(post.title)}</h4>
      <div class="post-sidebar-meta">
        <span>✅ ${post.schedule}</span> &bull; <span>4개 이미지</span>
      </div>
    </div>
  `).join('');

  showPostDetail(BLOG_POSTS[0]);

  sidebar.querySelectorAll('.post-sidebar-item').forEach(item => {
    item.addEventListener('click', () => {
      sidebar.querySelectorAll('.post-sidebar-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const post = BLOG_POSTS.find(p => p.id === item.dataset.postId);
      if (post) showPostDetail(post);
    });
  });
}

let currentOriginalMarkdown = '';
let currentEditingPost = null;

function showPostDetail(post) {
  const viewer = document.getElementById('postViewerContainer');
  if (!viewer) return;

  currentEditingPost = post;
  currentOriginalMarkdown = '';

  viewer.innerHTML = `
    <h2 class="preview-post-title">${escapeHtml(post.title)}</h2>
    <div class="header-status-box" style="margin-bottom: 1.5rem; align-items: flex-start; gap: 0.75rem;">
      <span class="schedule-pill" style="display:inline-block; background: #059669; color: #ffffff;">${post.schedule}</span>
      ${post.naverUrl ? `
        <a href="${post.naverUrl}" target="_blank" rel="noopener" class="btn-publish-action" style="text-decoration:none; display:inline-flex; align-items:center; gap:0.4rem; padding: 0.4rem 0.9rem; font-size: 0.85rem; background: #03c75a; border-radius: 6px; color: #ffffff; font-weight: 700;">
          🟢 네이버 블로그에서 실제 글 보기 ↗
        </a>
      ` : ''}
    </div>
    <div class="preview-post-content">
      <p style="font-size: 1.05rem; color: #f1f5f9; font-weight: 500; background: rgba(6,182,212,0.08); padding: 1.25rem; border-radius: 10px; border-left: 4px solid var(--primary);">
        <strong>💡 핵심 요약:</strong> ${escapeHtml(post.summary)}
      </p>

      <h3 style="margin-top: 2rem;">📌 탑재된 시각 에셋 패키지</h3>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin: 1.25rem 0 2rem;">
        ${post.images.map(img => `
          <div style="background: rgba(0,0,0,0.3); border-radius: 8px; overflow: hidden; border: 1px solid var(--border-color); cursor: pointer;" onclick="openModal('${img.src}', '${escapeHtml(img.title)}')">
            <img src="${img.src}" alt="${escapeHtml(img.title)}" style="width: 100%; aspect-ratio: 1/1; object-fit: cover; display: block; margin: 0;">
            <div style="padding: 0.6rem; font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">
              ${escapeHtml(img.title)}
            </div>
          </div>
        `).join('')}
      </div>

      <!-- 📝 실시간 마크다운 블로그 글 수정 섹션 -->
      <div class="editor-section-card">
        <div class="editor-toolbar">
          <div class="editor-toolbar-left">
            <span class="editor-badge">✏️ 블로그 본문 실시간 편집기</span>
            <span class="editor-file-path" id="editorFilePath">${escapeHtml(post.file)}</span>
          </div>
          <div class="editor-toolbar-right">
            <button type="button" class="btn-editor btn-editor-revert" id="btnRevertEditor" onclick="handleRevertEditorContent()" title="수정 전 원본으로 복원">
              <span>🔄 되돌리기</span>
            </button>
            <button type="button" class="btn-editor btn-editor-save" id="btnSaveEditor" onclick="handleSaveEditorContent()" title="파일에 즉시 저장 (단축키: Ctrl+S)">
              <span>💾 수정내용 저장</span>
            </button>
            <button type="button" class="btn-editor btn-editor-publish" id="btnPublishModified" onclick="handlePublishModifiedPost()" title="수정된 내용으로 네이버 블로그 즉시 발행">
              <span>🚀 수정본 네이버 발행</span>
            </button>
          </div>
        </div>

        <div class="editor-textarea-container">
          <textarea 
            id="markdownEditorTextarea" 
            class="editor-textarea" 
            placeholder="마크다운 글 본문을 불러오는 중입니다..." 
            spellcheck="false"
          ></textarea>
        </div>

        <div class="editor-footer-status">
          <div class="editor-stats-row">
            <span id="editorCharCount">글자 수: 0자</span>
            <span id="editorLineCount">줄 수: 0줄</span>
          </div>
          <div class="editor-save-msg" id="editorSaveMessage">💡 수정 후 [저장]을 누르면 마크다운 파일에 즉시 영구 반영됩니다 (Ctrl+S).</div>
        </div>
      </div>
    </div>
  `;

  loadPostMarkdownContent(post.file);
}

// 마크다운 본문 API 로드
function loadPostMarkdownContent(filePath) {
  const textarea = document.getElementById('markdownEditorTextarea');
  const msg = document.getElementById('editorSaveMessage');
  if (!textarea) return;

  textarea.disabled = true;
  textarea.value = '마크다운 파일을 불러오는 중입니다...';

  fetch(`/api/post-content?file=${encodeURIComponent(filePath)}`)
    .then(res => res.json())
    .then(data => {
      textarea.disabled = false;
      if (data.success) {
        currentOriginalMarkdown = data.content;
        textarea.value = data.content;
        updateEditorStats(data.content);
        if (msg) msg.textContent = '✅ 본문 로드 완료. 자유롭게 수정 후 [저장]을 눌러주세요.';
      } else {
        textarea.value = `[오류] 파일을 불러오지 못했습니다: ${data.error || '알 수 없는 오류'}`;
        if (msg) {
          msg.textContent = '❌ 파일 불러오기 실패';
          msg.className = 'editor-save-msg error';
        }
      }
    })
    .catch(err => {
      textarea.disabled = false;
      textarea.value = `[네트워크 오류] ${err.message}`;
      if (msg) {
        msg.textContent = '❌ 서버 통신 오류';
        msg.className = 'editor-save-msg error';
      }
    });

  // 글자 수 / 단축키 이벤트 리스너
  textarea.addEventListener('input', () => {
    updateEditorStats(textarea.value);
  });

  textarea.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleSaveEditorContent();
    }
  });
}

// 에디터 통계 갱신
function updateEditorStats(text) {
  const charSpan = document.getElementById('editorCharCount');
  const lineSpan = document.getElementById('editorLineCount');
  if (charSpan) charSpan.textContent = `글자 수: ${text.length.toLocaleString()}자`;
  if (lineSpan) lineSpan.textContent = `줄 수: ${text.split('\n').length.toLocaleString()}줄`;
}

// 수정사항 저장 핸들러
window.handleSaveEditorContent = async function() {
  if (!currentEditingPost) return;
  const textarea = document.getElementById('markdownEditorTextarea');
  const msg = document.getElementById('editorSaveMessage');
  const saveBtn = document.getElementById('btnSaveEditor');
  if (!textarea || !msg) return;

  const content = textarea.value;
  msg.textContent = '⏳ 파일에 저장 중입니다...';
  msg.className = 'editor-save-msg saving';
  if (saveBtn) saveBtn.disabled = true;

  try {
    const res = await fetch('/api/save-post', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file: currentEditingPost.file,
        content: content
      })
    });
    const result = await res.json();
    if (result.success) {
      currentOriginalMarkdown = content;
      msg.textContent = `✅ [${new Date().toLocaleTimeString('ko-KR')}] 마크다운 파일 저장 완료! 네이버 발행 시 반영됩니다.`;
      msg.className = 'editor-save-msg success';
    } else {
      msg.textContent = `❌ 저장 실패: ${result.error}`;
      msg.className = 'editor-save-msg error';
    }
  } catch (err) {
    msg.textContent = `❌ 네트워크 오류: ${err.message}`;
    msg.className = 'editor-save-msg error';
  } finally {
    if (saveBtn) saveBtn.disabled = false;
  }
};

// 원본 되돌리기 핸들러
window.handleRevertEditorContent = function() {
  const textarea = document.getElementById('markdownEditorTextarea');
  const msg = document.getElementById('editorSaveMessage');
  if (!textarea) return;

  if (confirm('수정한 내용을 모두 취소하고 원본 상태로 되돌리시겠습니까?')) {
    textarea.value = currentOriginalMarkdown;
    updateEditorStats(currentOriginalMarkdown);
    if (msg) {
      msg.textContent = '🔄 원본 상태로 되돌렸습니다.';
      msg.className = 'editor-save-msg';
    }
  }
};

// 수정본으로 네이버 즉시 발행 핸들러
window.handlePublishModifiedPost = async function() {
  if (!currentEditingPost) return;
  const msg = document.getElementById('editorSaveMessage');
  const publishBtn = document.getElementById('btnPublishModified');

  if (!confirm(`'${currentEditingPost.title}' 글을 수정된 내용으로 네이버 블로그에 즉시 자동 발행하시겠습니까?`)) {
    return;
  }

  // 먼저 현재 작성된 내용을 자동 저장
  await handleSaveEditorContent();

  if (msg) {
    msg.textContent = '🚀 네이버 스마트에디터 ONE 자동 발행 엔진을 기동 중입니다... (약 15~30초 소요)';
    msg.className = 'editor-save-msg saving';
  }
  if (publishBtn) {
    publishBtn.disabled = true;
    publishBtn.textContent = '⏳ 발행 중...';
  }

  try {
    const res = await fetch('/api/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file: currentEditingPost.file,
        mode: 'publish'
      })
    });
    const data = await res.json();
    if (data.success) {
      msg.textContent = '🎉 네이버 블로그 자동 발행이 성공적으로 완료되었습니다!';
      msg.className = 'editor-save-msg success';
      alert('네이버 블로그 자동 발행이 완료되었습니다! 네이버 블로그를 확인해 보세요.');
    } else {
      msg.textContent = `❌ 발행 실패: ${data.error || '상세 로그를 확인하세요'}`;
      msg.className = 'editor-save-msg error';
      alert(`발행 중 오류 발생: ${data.error}`);
    }
  } catch (err) {
    msg.textContent = `❌ 서버 오류: ${err.message}`;
    msg.className = 'editor-save-msg error';
  } finally {
    if (publishBtn) {
      publishBtn.disabled = false;
      publishBtn.textContent = '🚀 수정본 네이버 발행';
    }
  }
};


// 6. Render Visual Assets Gallery
// 6. Render Visual Assets Gallery (Dynamic Filters & Modern Cards)
let currentGalleryFilter = 'all';

function renderGallery() {
  const container = document.getElementById('assetsGalleryGrid');
  const filterContainer = document.getElementById('galleryFilterBtns');
  if (!container) return;

  const allImages = [];
  BLOG_POSTS.forEach((p) => {
    p.images.forEach(img => {
      allImages.push({
        ...img,
        topicId: `topic_${p.id}`,
        topicName: p.topic.replace(/_/g, ' ')
      });
    });
  });

  // Dynamically render filter buttons
  if (filterContainer) {
    let filterHtml = `
      <button class="filter-btn ${currentGalleryFilter === 'all' ? 'active' : ''}" data-filter="all">
        전체보기 (${allImages.length})
      </button>
    `;

    BLOG_POSTS.forEach((p, idx) => {
      const topicId = `topic_${p.id}`;
      const count = p.images.length;
      const shortTitle = p.topic.replace(/_/g, ' ');
      filterHtml += `
        <button class="filter-btn ${currentGalleryFilter === topicId ? 'active' : ''}" data-filter="${topicId}">
          ${idx + 1}. ${escapeHtml(shortTitle)} (${count})
        </button>
      `;
    });

    filterContainer.innerHTML = filterHtml;

    filterContainer.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        filterContainer.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentGalleryFilter = btn.dataset.filter;
        updateGalleryDisplay();
      });
    });
  }

  function updateGalleryDisplay() {
    const filtered = currentGalleryFilter === 'all'
      ? allImages
      : allImages.filter(img => img.topicId === currentGalleryFilter);

    container.innerHTML = filtered.map(img => {
      let badgeClass = 'badge-diagram';
      let badgeText = '아키텍처 도해';
      if (img.type === 'main') {
        badgeClass = 'badge-main-art';
        badgeText = '🎨 메인 아트';
      } else if (img.title.includes('차트') || img.title.includes('비교') || img.title.includes('벤치마크') || img.src.includes('chart') || img.src.includes('bench')) {
        badgeClass = 'badge-chart';
        badgeText = '📊 비교 차트';
      } else {
        badgeClass = 'badge-diagram';
        badgeText = '🏛️ 시스템 도해';
      }

      return `
        <div class="gallery-card" onclick="openModal('${img.src}', '${escapeHtml(img.title)}', '${escapeHtml(img.topicName)}')">
          <div class="gallery-img-wrap">
            <img src="${img.src}" alt="${escapeHtml(img.title)}" loading="lazy">
            <span class="gallery-type-badge ${badgeClass}">${badgeText}</span>
            <div class="gallery-hover-overlay">
              <span class="gallery-hover-icon">🔍</span>
              <span>고화질 원본 확대</span>
            </div>
          </div>
          <div class="gallery-card-body">
            <span class="gallery-topic-tag">📌 ${escapeHtml(img.topicName)}</span>
            <h4 class="gallery-item-title">${escapeHtml(img.title)}</h4>
          </div>
        </div>
      `;
    }).join('');
  }

  updateGalleryDisplay();
}

// 7. Image Modal Logic (Fixed ID and added ESC key support)
function initModal() {
  const overlay = document.getElementById('imageModalOverlay');
  const closeBtn = document.getElementById('modalCloseBtn');

  if (closeBtn && overlay) {
    closeBtn.addEventListener('click', () => {
      overlay.classList.remove('active');
    });

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && overlay.classList.contains('active')) {
        overlay.classList.remove('active');
      }
    });
  }
}

function openModal(src, title, topicName) {
  const overlay = document.getElementById('imageModalOverlay');
  const modalImg = document.getElementById('modalImageElement');
  const modalCaption = document.getElementById('modalCaptionBar');
  const modalRawLink = document.getElementById('modalRawLink');
  if (!overlay || !modalImg) return;

  modalImg.src = src;
  modalImg.alt = title || 'Visual Asset';
  if (modalCaption) {
    modalCaption.innerHTML = `
      <span style="font-size:0.75rem; color:#38bdf8; display:block; margin-bottom:0.25rem;">📌 ${escapeHtml(topicName || '')}</span>
      ${escapeHtml(title)}
    `;
  }
  if (modalRawLink) {
    modalRawLink.href = src;
  }
  overlay.classList.add('active');
}

// 8. Interactive Action Button
function initPublishButton() {
  const quickBtn = document.getElementById('quickPublishBtn');
  const runBtn = document.getElementById('runPublishBtn');

  if (quickBtn) {
    quickBtn.addEventListener('click', (e) => {
      e.preventDefault();
      window.open('https://blog.naver.com/gogo351', '_blank');
    });
  }

  if (runBtn) {
    runBtn.addEventListener('click', (e) => {
      // allow default anchor navigation or explicit window.open
    });
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
