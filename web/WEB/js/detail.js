// 파일 최상단 또는 전역에 백엔드 주소 설정
const BACKEND_URL = "/api/reservations/reserve"; 
const API_KEY = "76bdb5ba111645e394169b887d8a5e33";

let currentPerformanceData = null;

// ==========================================
// [0] 코어 유틸리티
// ==========================================
const getText = (element, tagName, defaultValue = '정보 없음') => {
    const node = element?.getElementsByTagName(tagName)[0];
    return node && node.textContent.trim() ? node.textContent.trim() : defaultValue;
};

async function fetchXMLWithCache(endpoint, cacheKey, ttlMinutes = 10) {
    const cachedData = localStorage.getItem(cacheKey);
    if (cachedData) {
        try {
            const { timestamp, xmlString } = JSON.parse(cachedData);
            if (Date.now() - timestamp < ttlMinutes * 60 * 1000) {
                return new DOMParser().parseFromString(xmlString, "text/xml");
            }
        } catch (e) { localStorage.removeItem(cacheKey); }
    }

    const targetUrl = `http://www.kopis.or.kr${endpoint}`;
    const proxies = [
        `/kopis-api${endpoint}`,
        `https://corsproxy.io/?${encodeURIComponent(targetUrl)}`,
        `https://api.allorigins.win/raw?url=${encodeURIComponent(targetUrl)}`
    ];

    for (const proxy of proxies) {
        try {
            const response = await fetch(proxy);
            if (!response.ok) continue;

            const text = await response.text();
            if (!text || text.toLowerCase().includes('<!doctype html>')) continue;

            if (text.includes('<?xml') || text.includes('<dbs>') || text.includes('<boxofs>')) {
                localStorage.setItem(cacheKey, JSON.stringify({ timestamp: Date.now(), xmlString: text }));
                return new DOMParser().parseFromString(text, "text/xml");
            }
        } catch (e) { console.warn("통로 실패:", proxy); }
    }
    throw new Error("데이터를 불러올 수 없습니다.");
}

// ==========================================
// [1] 초기화 로직
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
    updateHeaderUI();
    if (typeof lucide !== 'undefined') lucide.createIcons();
    
    const urlParams = new URLSearchParams(window.location.search);
    let performanceId = urlParams.get('id') || 'TEST_ID';

    await fetchPerformanceDetail(performanceId);
});

// ==========================================
// [2] 헤더 UI 동적 렌더링
// ==========================================
function updateHeaderUI() {
    const authMenu = document.getElementById('auth-menu');
    if (!authMenu) return; 

    const userName = sessionStorage.getItem('ename');

    if (userName) {
        authMenu.innerHTML = `
            <div class="flex items-center gap-4 animate-fade-in">
                <div class="flex items-center gap-1.5 text-gray-900 text-sm font-medium">
                    <i data-lucide="user" class="w-4 h-4 text-purple-600"></i>
                    <span class="text-purple-600 font-bold">${userName}</span>님
                </div>
                <div class="w-[1px] h-3 bg-gray-200"></div>
                <button onclick="location.href='mypage.html'" class="flex items-center gap-1.5 text-gray-600 hover:text-purple-600 transition-colors text-xs font-semibold">
                    <i data-lucide="ticket" class="w-4 h-4"></i> 예약내역
                </button>
                <div class="w-[1px] h-3 bg-gray-200"></div>
                <button id="logoutBtn" class="flex items-center gap-1.5 text-gray-400 hover:text-red-500 transition-colors text-xs font-semibold">
                    <i data-lucide="log-out" class="w-4 h-4"></i> 로그아웃
                </button>
            </div>
        `;
        document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);
    } else {
        authMenu.innerHTML = `
            <div class="flex items-center gap-4 animate-fade-in">
                <button onclick="location.href='login.html'" class="flex items-center gap-1.5 text-gray-600 hover:text-purple-600 transition-colors text-xs font-semibold">
                    <i data-lucide="log-in" class="w-4 h-4"></i> 로그인
                </button>
                <div class="w-[1px] h-3 bg-gray-200"></div>
                <button onclick="location.href='login.html'" class="flex items-center gap-1.5 text-gray-600 hover:text-purple-600 transition-colors text-xs font-semibold">
                    <i data-lucide="search" class="w-4 h-4"></i> 예약내역 조회
                </button>
            </div>
        `;
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function handleLogout() {
    if (confirm("로그아웃 하시겠습니까?")) {
        sessionStorage.clear(); 
        alert("로그아웃 되었습니다.");
        location.href = 'index.html'; 
    }
}

// ==========================================
// [3] 데이터 통신 로직 (이미지 보안 경고 해결)
// ==========================================
async function fetchPerformanceDetail(id) {
    const container = document.getElementById('detailContainer');
    
    if (container) {
        container.innerHTML = `
            <div class="w-full py-32 flex flex-col items-center justify-center animate-pulse">
                <i data-lucide="loader-2" class="w-10 h-10 text-purple-500 animate-spin mb-4"></i>
                <p class="text-purple-600 font-bold text-lg">공연 상세 정보를 불러오는 중입니다...</p>
            </div>
        `;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    const endpoint = `/openApi/restful/pblprfr/${id}?service=${API_KEY}`;
    let data = {};
    let introImagesHtml = '';

    try {
        if (id === 'TEST_ID') throw new Error("Fallback 트리거");

        const cacheKey = `perf_detail_${id}`;
        const xmlDoc = await fetchXMLWithCache(endpoint, cacheKey, 60);
        const db = xmlDoc.getElementsByTagName("db")[0];

        if (!db) throw new Error("KOPIS 데이터 없음");

        // 💡 Mixed Content (HTTP 이미지 차단) 방지를 위해 https:// 로 강제 치환
        data = {
            id: id,
            title: getText(db, "prfnm"),
            poster: getText(db, "poster", "https://via.placeholder.com/300x420?text=No+Image").replace("http://", "https://"),
            genre: getText(db, "genrenm"),
            startDate: getText(db, "prfpdfrom"),
            endDate: getText(db, "prfpdto"),
            facility: getText(db, "fcltynm"),
            cast: getText(db, "prfcast"),
            runtime: getText(db, "prfruntime"),
            price: getText(db, "pcseguidance"),
            state: getText(db, "prfstate")
        };

        const styurlNodes = db.getElementsByTagName("styurl");
        for (let i = 0; i < styurlNodes.length; i++) {
            const imgUrl = styurlNodes[i].textContent.trim().replace("http://", "https://");
            if (imgUrl) introImagesHtml += `<img src="${imgUrl}" alt="상세 이미지" loading="lazy" class="w-full max-w-3xl mb-4 rounded-xl shadow-sm">`;
        }

    } catch (error) {
        data = {
            id: 'TEST_ID',
            title: "[테스트] 펄스 오리지널 콘서트",
            poster: "https://via.placeholder.com/300x420?text=Test+Poster",
            genre: "콘서트",
            startDate: "2026.05.01",
            endDate: "2026.05.31",
            facility: "PULSE 그랜드 시어터",
            cast: "테스트 출연진",
            runtime: "120분",
            price: "전석 100,000원",
            state: "공연중"
        };
    }

    const priceMatch = data.price.replace(/,/g, '').match(/\d+/);
    data.defaultPrice = priceMatch ? parseInt(priceMatch[0], 10) : 100000;
    currentPerformanceData = data;

    renderDetailView(container, data, introImagesHtml);
}

// ==========================================
// [4] 화면 렌더링 및 이벤트 바인딩
// ==========================================
function renderDetailView(container, data, introImagesHtml) {
    const todayStr = new Date().toISOString().split('T')[0];

    container.innerHTML = `
        <div class="bg-white rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 md:p-10 mb-12 flex flex-col md:flex-row gap-10 animate-fade-in">
            <div class="w-full md:w-1/3 flex-shrink-0">
                <div class="rounded-2xl overflow-hidden shadow-lg sticky top-24">
                    <img src="${data.poster}" class="w-full h-auto object-cover aspect-[3/4]" onerror="this.src='https://via.placeholder.com/300x420?text=No+Image';">
                </div>
            </div>
            <div class="w-full md:w-2/3 flex flex-col">
                <div class="flex items-center gap-2 mb-3">
                    <span class="bg-purple-100 text-purple-700 text-xs font-bold px-2.5 py-1 rounded-md">${data.genre}</span>
                    <span class="bg-gray-100 text-gray-600 text-xs font-bold px-2.5 py-1 rounded-md">${data.state}</span>
                </div>
                <h1 class="text-3xl md:text-4xl font-black text-gray-900 mb-8 leading-tight">${data.title}</h1>
                <div class="space-y-4 mb-8 flex-1">
                    <div class="flex items-start"><div class="w-24 font-bold text-gray-400">공연기간</div><div class="flex-1 font-medium text-gray-800">${data.startDate} ~ ${data.endDate}</div></div>
                    <div class="flex items-start"><div class="w-24 font-bold text-gray-400">공연장소</div><div class="flex-1 font-medium text-gray-800">${data.facility}</div></div>
                    <div class="flex items-start"><div class="w-24 font-bold text-gray-400">관람시간</div><div class="flex-1 font-medium text-gray-800">${data.runtime}</div></div>
                    <div class="flex items-start"><div class="w-24 font-bold text-gray-400">출연진</div><div class="flex-1 font-medium text-gray-800 break-keep">${data.cast}</div></div>
                    <div class="flex items-start border-t border-gray-100 pt-4 mt-2">
                        <div class="w-24 font-bold text-purple-500">티켓가격</div>
                        <div class="flex-1 text-purple-600 font-bold whitespace-pre-wrap">${data.price}</div>
                    </div>
                </div>
                
                <div class="mt-auto bg-purple-50 rounded-2xl p-5 md:p-6 border border-purple-100">
                    <p class="text-sm font-bold text-purple-800 mb-4 flex items-center gap-2"><i data-lucide="calendar-check" class="w-5 h-5"></i> 관람 일시 선택</p>
                    <div class="flex flex-col sm:flex-row gap-3 mb-4">
                        <input type="date" id="bookDate" class="flex-1 bg-white border border-purple-200 rounded-xl px-4 py-3 font-bold text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-400" min="${todayStr}">
                        <select id="bookTime" class="flex-1 bg-white border border-purple-200 rounded-xl px-4 py-3 font-bold text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-400">
                            <option value="">시간 선택</option>
                            <option value="14:00">14:00 (낮 공연)</option>
                            <option value="19:00">19:00 (저녁 공연)</option>
                        </select>
                    </div>
                    <button id="bookTicketBtn" class="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-4 rounded-xl transition-all shadow-md shadow-purple-200 flex justify-center items-center gap-2">
                        <i data-lucide="armchair" class="w-5 h-5"></i> 좌석 선택 및 예매하기
                    </button>
                </div>
            </div>
        </div>
        ${introImagesHtml ? `<div class="bg-white rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 md:p-12 text-center"><h2 class="text-2xl font-black mb-8 border-b pb-4 inline-block px-8 text-gray-800">공연 상세 소개</h2><div class="flex flex-col items-center gap-4">${introImagesHtml}</div></div>` : ''}
    `;

    if (typeof lucide !== 'undefined') lucide.createIcons();
    document.getElementById('bookTicketBtn').addEventListener('click', handleBooking);
}

function moveToBookingPage() {
    const { id, title, facility, defaultPrice, poster } = currentPerformanceData;
    const date = document.getElementById('bookDate').value;
    const time = document.getElementById('bookTime').value;

    const queryParams = new URLSearchParams({
        id: id, title: title, date: date, time: time,
        place: facility, price: defaultPrice, poster: poster
    });

    location.href = 'booking.html?' + queryParams.toString();
}

// ==========================================
// [5] 모달 제어 및 대기열 검증 로직
// ==========================================
function showWaitingModal(count) {
    const modal = document.getElementById('waitingModal');
    const countSpan = document.getElementById('waitingCount');
    const progressBar = document.getElementById('progressBar');

    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
    if (countSpan) countSpan.innerText = count;

    if (progressBar) {
        const max = 500; 
        const progress = Math.min(100, Math.max(0, ((max - count) / max) * 100));
        progressBar.style.width = `${progress}%`;
    }
}

function closeWaitingModal() {
    const modal = document.getElementById('waitingModal');
    if (modal) {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
    }
}

function resetButton() {
    const btn = document.getElementById('bookTicketBtn');
    if (!btn) return;
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="armchair" class="w-5 h-5"></i> 좌석 선택 및 예매하기`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

async function handleBooking() {
    const userId = sessionStorage.getItem('u_id');
    if (!userId) {
        alert("예매는 로그인한 사용자만 이용할 수 있습니다.");
        location.href = 'login.html';
        return;
    }

    const date = document.getElementById('bookDate').value;
    const time = document.getElementById('bookTime').value;

    if (!date || !time) {
        alert("관람하실 날짜와 시간을 모두 선택해주세요.");
        return;
    }

    const btn = document.getElementById('bookTicketBtn');
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader-2" class="w-5 h-5 animate-spin"></i> 대기열 확인 중...`;
    if (typeof lucide !== 'undefined') lucide.createIcons();

    await sendPreCheckRequest(); 
}

async function sendPreCheckRequest() {
    const requestData = {
        user_id: sessionStorage.getItem('u_id'),
        perf_id: currentPerformanceData.id,
        select_date: document.getElementById('bookDate').value,
        select_time: document.getElementById('bookTime').value,
        // 💡 422 에러 차단: 백엔드가 캡차 토큰을 빈칸으로라도 받을 수 있게 처리
        turnstile_token: "" 
    };

    try {
        const response = await fetch(BACKEND_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        // [대기열에 걸렸을 때]
        if (result.status === "wait") {
            showWaitingModal(result.waiting_number);
            setTimeout(() => sendPreCheckRequest(), 3000);
            return;
        }

        // [내 순서가 왔을 때]
        if (result.status === "success" || response.status === 200) {
            closeWaitingModal(); 
            moveToBookingPage(); 
        } else {
            alert("❌ 진입 실패: " + (result.message || "알 수 없는 오류"));
            resetButton();
        }
    } catch (error) {
        console.error("서버 연결 에러:", error);
        alert("⚠️ 서버와 통신할 수 없습니다. 다시 시도해주세요.");
        resetButton();
    }
}