const axios = require('axios');
const fs = require('fs');
const path = require('path');
const log = require('../../../../logger');

/**
 * 폴더 및 파일명에 쓸 YYMMDD_시간 포맷 구하기 (예: 15시 47분이면 1547)
 */
const getFormattedDateTime = () => {
  const now = new Date();
  const yy = String(now.getFullYear()).slice(-2);
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const hh = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  return `${yy}${mm}${dd}_${hh}${min}`;
};

/**
 * Apify Actor의 실행이 성공적으로 끝날 때까지 주기적으로 상태를 폴링하여 대기합니다.
 * 터미널을 호출하지 않고 순수 Node.js 단에서 Axios를 통해 동기식으로 상태를 조회합니다.
 */
const waitForApifyRun = async (runId, token) => {
  const maxRetries = 60; // 3초씩 최대 3분 대기
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await axios.get(`https://api.apify.com/v2/actor-runs/${runId}`, {
        params: { token },
        timeout: 5000
      });
      const status = response.data?.data?.status;
      log.step(`Apify Actor [${runId}] 상태 확인 중... (${status})`);

      if (status === 'SUCCEEDED') {
        const datasetId = response.data?.data?.defaultDatasetId;
        if (!datasetId) throw new Error('성공했으나 defaultDatasetId를 찾지 못했습니다.');
        return datasetId;
      }

      if (['FAILED', 'ABORTED', 'TIMED-OUT'].includes(status)) {
        throw new Error(`Actor 실행이 비정상 종료되었습니다: ${status}`);
      }
    } catch (e) {
      if (e.message.includes('비정상 종료')) throw e;
      log.warn(`폴링 중 일시적 오류: ${e.message}`);
    }
    await new Promise(r => setTimeout(r, 3000));
  }
  throw new Error('Apify Actor 실행 대기 시간 초과(Timeout)');
};

/**
 * Reddit r/ClaudeAI 서브레디트의 어제자 가장 인기있는 포스트를 수집하고 raw md 파일로 조립합니다.
 */
const fetchRedditTrends = async () => {
  log.step('Reddit r/ClaudeAI 트렌드 수집 시작...');
  const results = [];
  let formattedPosts = [];

  const tokenReddit = process.env.APIFY_TOKEN_REDDIT;

  if (!tokenReddit) {
    log.warn('APIFY_TOKEN_REDDIT가 .env에 없습니다. 수집을 스킵합니다.');
  } else {
    try {
      log.step('Apify Reddit Scraper (harshmaur/reddit-scraper) Actor 기동 중...');
      
      // 사용자 지정 강제 적용 우회법 Payload 100% 하드코딩 반영
      const apiPayload = {
        "startUrls": [
          {
            "url": "https://www.reddit.com/r/ClaudeAI/top/?t=day"
          }
        ],
        "maxPostsCount": 10,
        "proxy": {
          "useApifyProxy": true,
          "apifyProxyGroups": [
            "RESIDENTIAL"
          ]
        }
      };

      log.step('전송할 API Payload 정보:');
      console.log(JSON.stringify(apiPayload, null, 2));

      // harshmaur/reddit-scraper Actor 실행 엔드포인트 호출
      const redditRunRes = await axios.post(`https://api.apify.com/v2/acts/harshmaur~reddit-scraper/runs?token=${tokenReddit}`, apiPayload, { timeout: 30000 });

      const runId = redditRunRes.data?.data?.id;
      if (!runId) throw new Error('Apify Reddit Run ID 생성에 실패했습니다.');

      // 실행 완료 시까지 대기 후 데이터셋 ID 추출
      const datasetId = await waitForApifyRun(runId, tokenReddit);
      log.step(`데이터셋 수집 성공! ID: ${datasetId}`);

      // 데이터셋 아이템 가져오기
      const datasetItemsRes = await axios.get(`https://api.apify.com/v2/datasets/${datasetId}/items`, {
        params: { token: tokenReddit },
        timeout: 30000
      });

      const redditItems = datasetItemsRes.data || [];
      log.step(`Apify 수집 원본 데이터 개수: ${redditItems.length}개`);

      // 1단계: 원본 전체 파싱 및 규격화 (동영상 포스트 원천 제외)
      let allPosts = redditItems
        .filter(item => {
          const isVideo = item.postType === 'video' || item.isVideo || item.is_video || (item.url && item.url.includes('v.redd.it'));
          return (item.dataType === 'post' || item.title) && !isVideo;
        })
        .map(item => {
          const upvotes = parseInt(item.upVotes || item.score || item.ups || 0, 10);
          const comments = parseInt(item.numberOfComments || item.numComments || item.num_comments || 0, 10);
          const author = item.username || item.author || item.authorName || 'unknown';
          const title = item.title || 'No Title';
          const body = item.body || item.selftext || item.text || '';
          
          return {
            source: 'Reddit',
            title: title,
            author: author,
            content: body,
            url: item.url || item.postUrl || '',
            published_at: item.createdAt ? new Date(item.createdAt).toISOString() : new Date().toISOString(),
            metrics: { likes: upvotes, comments }
          };
        });

      // 중복 배제
      const seenUrls = new Set();
      allPosts = allPosts.filter(post => {
        if (!post.url || seenUrls.has(post.url)) return false;
        seenUrls.add(post.url);
        return true;
      });

      // top/?t=day 에서 가져온 최신 인기 포스트를 그대로 채택
      log.step(`인기 포스트 10개 수집 중...`);

      // 최종 좋아요(likes) 순 내림차순 정렬 후 최대 10개 슬라이스
      formattedPosts = allPosts
        .sort((a, b) => b.metrics.likes - a.metrics.likes)
        .slice(0, 10);

      results.push(...formattedPosts);
      log.ok(`Apify Reddit Scraper 연동 수집 완료 (${formattedPosts.length}개 추출)`);
    } catch (err) {
      log.err(`Reddit Apify 수집 중 오류 발생: ${err.message}`);
    }
  }

  // 3. Raw JSON 데이터 저장 자동화 (에이전트가 이후 단계에서 직접 마크다운 빌드)
  if (formattedPosts.length > 0) {
    try {
      const dateTimeStr = getFormattedDateTime();
      const outputDirPath = path.join(process.cwd(), 'output', dateTimeStr);

      if (!fs.existsSync(outputDirPath)) {
        fs.mkdirSync(outputDirPath, { recursive: true });
      }

      const finalPath = path.join(outputDirPath, 'raw_reddit_data.json');
      fs.writeFileSync(finalPath, JSON.stringify(formattedPosts, null, 2), 'utf8');
      log.ok(`Reddit raw 데이터 저장 완료: output/${dateTimeStr}/raw_reddit_data.json`);
      log.step(`에이전트(나)는 이 JSON 파일을 기반으로 직접 번역과 5대 질문을 추론하여 ingest.md 파일을 생성해야 합니다.`);

    } catch (err) {
      log.err(`결과 JSON 파일 저장 실패: ${err.message}`);
    }
  } else {
    log.warn('수집된 데이터가 없어 JSON 파일을 생성하지 않았습니다.');
  }

  return results;
};

module.exports = {
  fetchRedditTrends
};
