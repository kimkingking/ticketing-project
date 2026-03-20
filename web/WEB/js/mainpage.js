const API_KEY = "76bdb5ba111645e394169b887d8a5e33"; 

let currentBoxOfficeGenre = ''; 
let currentListGenre = ''; 

const categories = [
    { id: '', name: '전체', icon: '🎫', color: 'bg-gray-100' },
    { id: 'GGGA', name: '뮤지컬', icon: '💃', color: 'text-pink-800' },
    { id: 'AAAA', name: '연극', icon: '🎭', color: 'bg-orange-100' },
    { id: 'CCCC', name: '국악', icon: '🪘', color: 'bg-green-100' },
    { id: 'BBBC', name: '무용', icon: '🩰', color: 'bg-purple-100' },
    { id: 'CCCA', name: '클래식', icon: '🎻', color: 'bg-blue-100' },
];

const endDate = new Date();
const startDate = new Date();
startDate.setDate(endDate.getDate() - 30); 

let stdateStr = startDate.toISOString().split('T')[0].replace(/-/g, '');
let eddateStr = endDate.toISOString().split('T')[0].replace(/-/g, '');

// ==========================================
// [0] 코어 유틸리티
// ==========================================
const getText = (element, tagName, defaultValue = '') => {
    const node = element?.getElementsByTagName(tagName)[0];
    return node && node.textContent.trim() ? node.textContent.trim() : defaultValue;
};

// 💡 궁극의 데이터 패칭 함수: 인그레스가 죽든, 포트로 접속하든 무조건 찾아옵니다.
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
    
    // 💡 1순위: 방금 완벽하게 고친 내부 K8s 통로
    // 💡 2순위, 3순위: CORS 에러가 절대 나지 않는 raw 데이터 프록시
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
            
            // Nginx 에러 페이지 필터링
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
// [1] 초기화
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
    updateHeaderUI();
    renderCategories();
    renderTabs();
    if (typeof lucide !== 'undefined') lucide.createIcons();
    
    await refreshData();
    window.addEventListener('resize', updateScrollButtons);
});

// ==========================================
// [2] UI 및 렌더링
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
                <button onclick="handleLogout()" class="flex items-center gap-1.5 text-gray-400 hover:text-red-500 transition-colors text-xs font-semibold">
                    <i data-lucide="log-out" class="w-4 h-4"></i> 로그아웃
                </button>
            </div>
        `;
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
        location.reload(); 
    }
}

function renderCategories() {
    const container = document.getElementById('categoryMenu');
    if (!container) return;
    container.innerHTML = categories.map(cat => `
        <div class="flex flex-col items-center gap-3 cursor-pointer group" onclick="changeListCategory('${cat.id}')">
            <div class="w-16 h-16 rounded-full ${cat.color} flex items-center justify-center text-3xl shadow-sm group-hover:shadow-md transition-all group-hover:-translate-y-1">
                ${cat.icon}
            </div>
            <span class="text-sm font-medium text-gray-700 group-hover:text-purple-600 transition-colors">${cat.name}</span>
        </div>
    `).join('');
}

function renderTabs() {
    const container = document.getElementById('tabMenu');
    if (!container) return;
    container.innerHTML = categories.map(cat => {
        const isActive = cat.id === currentBoxOfficeGenre;
        const activeClass = isActive ? 'bg-gray-900 text-white font-bold shadow-md' : 'bg-gray-100 text-gray-600 hover:bg-gray-200';
        return `<button onclick="changeBoxOfficeCategory('${cat.id}')" class="px-5 py-2 rounded-full text-sm whitespace-nowrap transition-all ${activeClass}">${cat.name}</button>`;
    }).join('');
}

// ==========================================
// [3] 데이터 패칭 로직
// ==========================================
async function refreshData() {
    await Promise.allSettled([fetchBoxOffice(), fetchPerformanceList()]);
}

async function changeBoxOfficeCategory(genreId) {
    currentBoxOfficeGenre = genreId;
    renderTabs(); 
    const boxOffice = document.getElementById('boxOfficeList');
    if (boxOffice) boxOffice.innerHTML = '<div class="text-gray-400 py-10 w-full text-center animate-pulse">데이터를 불러오는 중입니다...</div>';
    await fetchBoxOffice();
}

async function changeListCategory(genreId) {
    currentListGenre = genreId;
    const listTitle = document.getElementById('listTitle');
    const genreName = categories.find(c => c.id === genreId)?.name || '전체';
    if (listTitle) listTitle.innerHTML = `<span class="text-purple-600">${genreName}</span> 추천 공연`;
    
    const perfList = document.getElementById('performanceList');
    if (perfList) perfList.innerHTML = '<div class="text-gray-400 py-10 w-full col-span-full text-center animate-pulse">추천 공연을 불러오는 중입니다...</div>';
    await fetchPerformanceList();
}

async function fetchBoxOffice() {
    const container = document.getElementById('boxOfficeList');
    if (!container) return;

    let endpoint = `/openApi/restful/boxoffice?service=${API_KEY}&stdate=${stdateStr}&eddate=${eddateStr}`;
    if (currentBoxOfficeGenre) endpoint += `&catecode=${currentBoxOfficeGenre}`;

    try {
        const cacheKey = `data_boxoffice_${currentBoxOfficeGenre}`;
        const xmlDoc = await fetchXMLWithCache(endpoint, cacheKey, 10);
        const items = xmlDoc.getElementsByTagName("boxof");

        if(items.length === 0) {
            container.innerHTML = '<div class="text-gray-400 py-10 text-center w-full">해당 장르의 랭킹 데이터가 없습니다.</div>';
            return;
        }

        container.innerHTML = Array.from(items).slice(0, 10).map((item, index) => {
            const id = getText(item, "mt20id");
            const title = getText(item, "prfnm", "제목 없음");
            const poster = getText(item, "poster");
            const rank = getText(item, "rnum", index + 1);
            const period = getText(item, "prfpd");

            return `
                <div onclick="location.href='detail.html?id=${id}'" class="w-[240px] md:w-[280px] flex-shrink-0 cursor-pointer group snap-start">
                    <div class="relative rounded-2xl overflow-hidden mb-4 shadow-sm">
                        <img src="${poster}" alt="${title}" loading="lazy" class="w-full aspect-[3/4] object-cover hover-scale transition-transform duration-500 group-hover:scale-110" onerror="this.onerror=null; this.src='https://via.placeholder.com/300x420?text=No+Image';">
                        <div class="absolute top-0 left-0 bg-black/80 text-white font-black text-xl w-12 h-12 flex items-center justify-center rounded-br-2xl backdrop-blur-sm">${rank}</div>
                    </div>
                    <h3 class="font-bold text-gray-900 text-lg truncate mb-1 group-hover:text-purple-600 transition-colors" title="${title}">${title}</h3>
                    <p class="text-sm text-gray-500 truncate" title="${period}">${period}</p>
                </div>
            `;
        }).join('');

        setTimeout(() => typeof updateScrollButtons === 'function' && updateScrollButtons(), 50);

    } catch (e) { 
        container.innerHTML = '<div class="text-red-400 py-10 text-center w-full">데이터를 불러오는데 실패했습니다.</div>';
    }
}

async function fetchPerformanceList() {
    const container = document.getElementById('performanceList');
    if (!container) return;

    let endpoint = `/openApi/restful/pblprfr?service=${API_KEY}&stdate=${stdateStr}&eddate=${eddateStr}&cpage=1&rows=10`;
    if (currentListGenre) endpoint += `&shcate=${currentListGenre}`;

    try {
        const cacheKey = `data_perflist_${currentListGenre}`;
        const xmlDoc = await fetchXMLWithCache(endpoint, cacheKey, 10);
        const items = xmlDoc.getElementsByTagName("db");

        if(items.length === 0) {
            container.innerHTML = '<div class="text-gray-400 py-10 col-span-full text-center">진행중인 공연이 없습니다.</div>';
            return;
        }

        container.innerHTML = Array.from(items).map(item => {
            const id = getText(item, "mt20id");
            const title = getText(item, "prfnm", "제목 없음");
            const poster = getText(item, "poster");
            const venue = getText(item, "fcltynm", "장소 미상");
            const state = getText(item, "prfstate", "상태 미상");

            let badgeColor = 'bg-gray-100 text-gray-600';
            if(state.includes('공연중')) badgeColor = 'bg-purple-100 text-purple-700';
            else if(state.includes('예정')) badgeColor = 'bg-blue-100 text-blue-700';

            return `
                <div onclick="location.href='detail.html?id=${id}'" class="cursor-pointer group flex flex-col">
                    <div class="relative rounded-xl overflow-hidden mb-3 shadow-sm border border-gray-100">
                        <img src="${poster}" alt="${title}" loading="lazy" class="w-full aspect-[3/4] object-cover transition-transform duration-500 group-hover:scale-105" onerror="this.onerror=null; this.src='https://via.placeholder.com/300x420?text=No+Image';">
                        <div class="absolute bottom-2 left-2 ${badgeColor} text-[10px] font-bold px-2 py-1 rounded shadow-sm backdrop-blur-sm bg-opacity-90">${state}</div>
                    </div>
                    <h3 class="font-bold text-gray-900 text-sm h-10 line-clamp-2 leading-snug mb-1 group-hover:text-purple-600 transition-colors" title="${title}">${title}</h3>
                    <p class="text-[11px] text-gray-400 truncate mt-auto" title="${venue}">
                        <i data-lucide="map-pin" class="inline w-3 h-3 mr-0.5"></i>${venue}
                    </p>
                </div>
            `;
        }).join('');
        
        if (typeof lucide !== 'undefined') lucide.createIcons();

    } catch (e) { 
        container.innerHTML = '<div class="text-red-400 py-10 col-span-full text-center">데이터를 불러오는데 실패했습니다.</div>';
    }
}

function scrollBoxOffice(direction) {
    const container = document.getElementById('boxOfficeList');
    if (!container) return;
    const scrollAmount = container.clientWidth * 0.8; 
    container.scrollBy({ left: direction === 'left' ? -scrollAmount : scrollAmount, behavior: 'smooth' });
}

function updateScrollButtons() {
    const container = document.getElementById('boxOfficeList');
    const leftBtn = document.getElementById('btn-scroll-left');
    const rightBtn = document.getElementById('btn-scroll-right');
    
    if (!container || !leftBtn || !rightBtn) return;
    if (container.scrollLeft <= 10) leftBtn.classList.add('scroll-btn-disabled');
    else leftBtn.classList.remove('scroll-btn-disabled');
    
    if (Math.ceil(container.scrollLeft + container.clientWidth) >= container.scrollWidth - 10) rightBtn.classList.add('scroll-btn-disabled');
    else rightBtn.classList.remove('scroll-btn-disabled');
}