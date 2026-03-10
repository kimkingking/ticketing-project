const API_KEY = "76bdb5ba111645e394169b887d8a5e33";

window.onload = function() {
    // 1. 인터넷 주소창(URL)에서 '?id=PF12345' 부분의 'id' 값을 뽑아옵니다.
    const urlParams = new URLSearchParams(window.location.search);
    const performanceId = urlParams.get('id');

    if (performanceId) {
        // ID가 있으면 API 호출 함수를 실행합니다.
        fetchPerformanceDetail(performanceId);
    } else {
        document.getElementById('detailContainer').innerHTML = "<div class='loading'>잘못된 접근입니다 (공연 ID가 없습니다).</div>";
    }
};

async function fetchPerformanceDetail(id) {
    const container = document.getElementById('detailContainer');

    // 상세 API 주소 구성
    const targetUrl = encodeURIComponent(`http://www.kopis.or.kr/openApi/restful/pblprfr/${id}?service=${API_KEY}`);
    const url = `https://corsproxy.io/?${targetUrl}`;

    try {
        const response = await fetch(url);
        const textData = await response.text();
        console.log(response);    
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(textData, "text/xml");
        
        // 상세 데이터는 <db> 태그 하나 안에 모두 들어있습니다.
        const db = xmlDoc.getElementsByTagName("db")[0];

        if (!db) {
            container.innerHTML = "<div class='loading'>상세 정보를 찾을 수 없습니다.</div>";
            return;
        }

        // 2. 알려주신 출력결과 필드를 바탕으로 필요한 정보 추출
        const title = db.getElementsByTagName("prfnm")[0]?.textContent || '제목 없음';
        const poster = db.getElementsByTagName("poster")[0]?.textContent || '';
        const startDate = db.getElementsByTagName("prfpdfrom")[0]?.textContent || '';
        const endDate = db.getElementsByTagName("prfpdto")[0]?.textContent || '';
        const facility = db.getElementsByTagName("fcltynm")[0]?.textContent || '';
        const cast = db.getElementsByTagName("prfcast")[0]?.textContent || '미상';
        const runtime = db.getElementsByTagName("prfruntime")[0]?.textContent || '정보 없음';
        const age = db.getElementsByTagName("prfage")[0]?.textContent || '정보 없음';
        const price = db.getElementsByTagName("pcseguidance")[0]?.textContent || '가격 정보 없음';
        const timeGuide = db.getElementsByTagName("dtguidance")[0]?.textContent || '정보 없음';

        // 3. 예매처 링크(relates) 추출
        const relatesNodes = db.getElementsByTagName("relate");
        let bookingLinksHtml = '';
        for (let i = 0; i < relatesNodes.length; i++) {
            const relName = relatesNodes[i].getElementsByTagName("relatenm")[0]?.textContent || '예매하기';
            const relUrl = relatesNodes[i].getElementsByTagName("relateurl")[0]?.textContent || '#';
            bookingLinksHtml += `<a href="javascript:void(0)" onclick="startPreBooking('${relUrl}')" class="booking-btn">🎟️ ${relName}</a>`;
        }

        // 4. 소개 이미지(styurls) 추출
        const styurlNodes = db.getElementsByTagName("styurl");
        let introImagesHtml = '';
        for (let i = 0; i < styurlNodes.length; i++) {
            const imgUrl = styurlNodes[i].textContent;
            if (imgUrl.trim() !== '') {
                introImagesHtml += `<img src="${imgUrl}" alt="공연 상세 이미지">`;
            }
        }

        // 5. HTML 화면 조립
        container.innerHTML = `
            <div class="info-section">
                <img src="${poster}" alt="${title} 포스터" class="poster-img" onerror="this.src='https://via.placeholder.com/300x420?text=No+Image'">
                <div class="text-info">
                    <h1>${title}</h1>
                    <div class="info-row"><span class="info-label">공연기간</span> ${startDate} ~ ${endDate}</div>
                    <div class="info-row"><span class="info-label">공연장소</span> ${facility}</div>
                    <div class="info-row"><span class="info-label">출연진</span> ${cast}</div>
                    <div class="info-row"><span class="info-label">관람연령</span> ${age}</div>
                    <div class="info-row"><span class="info-label">런타임</span> ${runtime}</div>
                    <div class="info-row"><span class="info-label">공연시간</span> ${timeGuide}</div>
                    <div class="info-row"><span class="info-label">티켓가격</span> <span class="price">${price}</span></div>
                    
                    ${bookingLinksHtml ? `<div class="booking-links">${bookingLinksHtml}</div>` : ''}
                </div>
            </div>

            ${introImagesHtml ? `
            <div class="intro-images">
                <h2>공연 상세 소개</h2>
                ${introImagesHtml}
            </div>
            ` : ''}
        `;

    } catch (error) {
        console.error(error);
        container.innerHTML = "<div class='loading'>데이터를 불러오는 중 오류가 발생했습니다.</div>";
    }
}

let waitingInterval;
let targetBookingUrl = ""; // 최종 이동할 주소를 저장할 변수
// [예매 시작] '예매하기' 버튼을 누르면 줄서기를 시작합니다.
function startPreBooking(url) {
    targetBookingUrl = url; // 클릭한 예매처의 실제 주소 저장
    
    // 기다리는 창(모달)을 화면에 띄웁니다.
    document.getElementById('waitingModal').style.display = 'flex';
    document.getElementById('captchaModal').style.display = 'none';
    
    let count = Math.floor(Math.random() * 150) + 50; 
    let progress = 0;
    const countEl = document.getElementById('waitingCount');
    const progressEl = document.getElementById('progressBar')
    
    countEl.innerText = count;
    progressEl.style.width = '0%';

    // 0.4초마다 숫자를 줄이고 막대기를 채우는 타이머를 돌립니다.
    // 이거는 일단 기능만 넣은거라 나중에 서버 테스트할 때 수정 필요 
    waitingInterval = setInterval(() => {
       count -= Math.floor(Math.random() * 10) + 3; // 숫자가 점점 줄어듦
        progress += Math.random() * 8 + 4; // 막대기가 점점 길어짐

        if (count <= 0 || progress >= 100) {
            clearInterval(waitingInterval); // 줄서기 끝! 타이머 정지
            setTimeout(() => {
                document.getElementById('waitingModal').style.display = 'none'; // 대기창 닫기
                showCaptchaModal(); // 다음 단계인 '보안문자 입력창' 띄우기
            }, 500);
        }
        countEl.innerText = count < 0 ? 0 : count; // 대기 인원 숫자 업데이트
        progressEl.style.width = `${progress}%`;    // 파란색 바 길이 업데이트
    }, 400);
}

function showCaptchaModal() {
    document.getElementById('captchaModal').style.display = 'flex'; 
    generateCaptcha();
    document.getElementById('captchaInput').value = '';
}



function generateCaptcha() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let captcha = '';
    for(let i = 0; i < 6; i++) {
        captcha += chars.charAt(Math.floor(Math.random() * chars.length)) + ' ';
    }
    document.getElementById('captchaText').innerText = captcha.trim();
}

// [보안 확인] 로봇인지 확인하기 위해 문자를 검사합니다.
function verifyCaptcha() {
    const input = document.getElementById('captchaInput').value.replace(/\s/g, '').toUpperCase(); // 내가 친 글자
    const actual = document.getElementById('captchaText').innerText.replace(/\s/g, ''); // 정답 글자
    
    if (input === actual) {
        alert('✅ 인증 성공! 좌석 선택 페이지로 이동합니다.');
        // 기존 targetBookingUrl 대신 내가 만든 좌석 페이지로 이동
        window.location.href = "seat_selection.html"; 
    } else {
        alert('❌ 문자가 틀렸습니다.');
        generateCaptcha(); // 글자를 새로 바꿉니다.
    }
}

function closeModals() {
    document.getElementById('waitingModal').style.display = 'none';
    document.getElementById('captchaModal').style.display = 'none';
    clearInterval(waitingInterval);
}