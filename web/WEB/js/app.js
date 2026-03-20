const API_KEY = "76bdb5ba111645e394169b887d8a5e33";
// ✨ 현재 프로토콜 동적 할당
const CURRENT_PROTOCOL = window.location.protocol;
const KOPIS_BASE_URL = `${CURRENT_PROTOCOL}//www.kopis.or.kr`;

const genreData = [
    { code: '', name: '전체', icon: '🌈', bg: 'bg-gray-100', text: 'text-gray-800' },
    { code: 'AAAA', name: '연극', icon: '🎭', bg: 'bg-orange-100', text: 'text-orange-800' },
    { code: 'GGGA', name: '뮤지컬', icon: '💃', bg: 'bg-pink-100', text: 'text-pink-800' },
    { code: 'CCCA', name: '클래식', icon: '🎻', bg: 'bg-blue-100', text: 'text-blue-800' },
    { code: 'CCCC', name: '국악', icon: '🪘', bg: 'bg-green-100', text: 'text-green-800' },
    { code: 'CCCD', name: '대중음악', icon: '🎸', bg: 'bg-indigo-100', text: 'text-indigo-800' },
    { code: 'BBBC', name: '무용', icon: '🩰', bg: 'bg-rose-100', text: 'text-rose-800' },
    { code: 'EEEA', name: '서커스/복합', icon: '🎪', bg: 'bg-yellow-100', text: 'text-yellow-800' }
];

let currentGenreCode = '';

const formatDate = (dateString) => dateString ? dateString.replace(/-/g, '') : "";
const getInputDateFormat = (date) => {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
};

const getText = (element, tagName, defaultValue = '') => {
    const node = element.getElementsByTagName(tagName)[0];
    return node ? node.textContent : defaultValue;
};

async function fetchXML(url) {
    const proxies = [
        `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`,
        `https://api.codetabs.com/v1/proxy?quest=${encodeURIComponent(url)}`,
        `https://corsproxy.io/?${encodeURIComponent(url)}`
    ];

    let lastError = null;

    for (let i = 0; i < proxies.length; i++) {
        const proxyUrl = proxies[i];
        try {
            const response = await fetch(proxyUrl);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const textData = await response.text();
            const xmlDoc = new DOMParser().parseFromString(textData, "text/xml");
            
            if (xmlDoc.getElementsByTagName("parsererror").length > 0) throw new Error("XML 파싱 실패");
            return xmlDoc;
        } catch (error) {
            console.warn(`[프록시 시도 ${i + 1}/${proxies.length} 실패] ${proxyUrl} - 사유: ${error.message}`);
            lastError = error;
        }
    }
    console.error("모든 프록시 서버 및 API 연동 실패. 테스트 데이터를 렌더링합니다.", lastError);
    throw new Error("KOPIS API 서버 응답 지연");
}

function scrollBoxOffice(direction) {
    const container = document.getElementById('boxOfficeList');
    const scrollAmount = 320; 
    container.scrollBy({ left: direction === 'left' ? -scrollAmount : scrollAmount, behavior: 'smooth' });
}

function showLoader(text) {
    document.getElementById('loaderText').innerText = text;
    const loader = document.getElementById('loader');
    loader.classList.remove('hidden');
    loader.style.opacity = '1';
}

function hideLoader() {
    const loader = document.getElementById('loader');
    loader.style.opacity = '0';
    setTimeout(() => loader.classList.add('hidden'), 500);
}

window.onload = function() {
    lucide.createIcons();
    const today = new Date();
    const lastMonth = new Date();
    lastMonth.setMonth(today.getMonth() - 1); 

    document.getElementById('startDate').value = getInputDateFormat(lastMonth);
    document.getElementById('endDate').value = getInputDateFormat(today);

    renderGenreCards();
    fetchAllData();
};

function renderGenreCards() {
    const container = document.getElementById('genreCardsContainer');
    container.innerHTML = genreData.map(genre => {
        const isActive = genre.code === currentGenreCode;
        const activeClasses = isActive 
            ? `ring-4 ring-purple-400 ring-offset-2 scale-105 shadow-md` 
            : `hover:-translate-y-1 shadow-sm hover:shadow-md border border-transparent`;
        
        return `
            <div onclick="changeGenre('${genre.code}')" 
                 class="cursor-pointer transition-all duration-300 rounded-2xl p-4 flex flex-col items-center justify-center gap-2 ${genre.bg} ${genre.text} ${activeClasses}">
                <span class="text-3xl drop-shadow-sm">${genre.icon}</span>
                <span class="font-bold text-sm">${genre.name}</span>
            </div>
        `;
    }).join('');
}

function changeGenre(code) {
    currentGenreCode = code;
    renderGenreCards();
    const genreName = genreData.find(g => g.code === code)?.name || '전체';
    document.getElementById('boxOfficeTitleGenre').innerText = genreName;
    document.getElementById('listTitleGenre').innerText = genreName;
    fetchAllData();
}

async function fetchAllData() {
    const stdate = document.getElementById('startDate').value;
    const eddate = document.getElementById('endDate').value;

    if (new Date(stdate) > new Date(eddate)) {
        alert("시작일이 종료일보다 늦을 수 없습니다.");
        return;
    }

    showLoader("데이터를 가져오고 있습니다...");
    document.getElementById('boxOfficeList').innerHTML = '';
    document.getElementById('performanceList').innerHTML = '';
    
    await Promise.allSettled([fetchBoxOffice(stdate, eddate), fetchPerformanceList(stdate, eddate)]);
    
    hideLoader();
    lucide.createIcons();
}

async function fetchBoxOffice(stdate, eddate) {
    const boxContainer = document.getElementById('boxOfficeList');
    // ✨ 동적 KOPIS URL 적용
    let url = `${KOPIS_BASE_URL}/openApi/restful/boxoffice?service=${API_KEY}&stdate=${formatDate(stdate)}&eddate=${formatDate(eddate)}`;
    if (currentGenreCode) url += `&catecode=${currentGenreCode}`;

    try {
        const xmlDoc = await fetchXML(url);
        const boxofs = xmlDoc.getElementsByTagName("boxof");

        if (boxofs.length === 0) {
            boxContainer.innerHTML = '<div class="text-gray-500 w-full text-center py-10 font-medium bg-white/50 rounded-2xl">해당 기간의 예매 데이터가 없습니다.</div>';
            return;
        }

        const maxCount = Math.min(boxofs.length, 10);
        const itemsHtml = Array.from(boxofs).slice(0, maxCount).map((item, index) => {
            const id = getText(item, "mt20id");
            const rank = getText(item, "rnum", index + 1);
            const title = getText(item, "prfnm", "제목 없음");
            const poster = getText(item, "poster");
            const area = getText(item, "area", "지역 미상");
            const rankColor = rank <= 3 ? 'bg-rose-500' : 'bg-gray-800';

            return `
                <div class="w-[260px] md:w-[300px] flex-shrink-0 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden snap-start hover-scale relative group">
                    <div class="absolute top-0 left-0 ${rankColor} text-white font-black text-xl w-12 h-12 flex items-center justify-center rounded-br-2xl z-10 shadow-md">${rank}</div>
                    <div class="h-48 overflow-hidden bg-gray-100 relative">
                        <img src="${poster}" alt="${title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" onerror="this.src='https://via.placeholder.com/300x200?text=No+Image'">
                        <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[2px]">
                            <a href="detail.html?id=${id}" target="_blank" class="bg-white text-gray-900 font-bold py-2 px-5 rounded-full shadow-lg flex items-center gap-2 text-sm">상세보기</a>
                        </div>
                    </div>
                    <div class="p-4">
                        <h3 class="font-bold text-gray-900 truncate-1-lines mb-2" title="${title}">${title}</h3>
                        <p class="text-xs text-gray-500 flex items-center gap-1 mb-3"><i data-lucide="map-pin" class="w-3 h-3"></i> ${area}</p>
                    </div>
                </div>`;
        }).join('');

        boxContainer.innerHTML = itemsHtml;

    } catch (error) {
        boxContainer.innerHTML = '<div class="text-red-500 py-10 w-full text-center">박스오피스 데이터를 불러오지 못했습니다.</div>';
    }
}

async function fetchPerformanceList(stdate, eddate) {
    const listContainer = document.getElementById('performanceList');
    // ✨ 동적 KOPIS URL 적용
    let url = `${KOPIS_BASE_URL}/openApi/restful/pblprfr?service=${API_KEY}&stdate=${formatDate(stdate)}&eddate=${formatDate(eddate)}&cpage=1&rows=15`;
    if (currentGenreCode) url += `&shcate=${currentGenreCode}`;

    try {
        const xmlDoc = await fetchXML(url);
        const dbs = xmlDoc.getElementsByTagName("db");
        
        if (dbs.length === 0) {
            listContainer.innerHTML = '<div class="text-gray-500 col-span-full py-20 text-center bg-gray-50 rounded-2xl">검색 결과가 없습니다.</div>';
            return;
        }

        const itemsHtml = Array.from(dbs).map(db => {
            const id = getText(db, "mt20id");
            const title = getText(db, "prfnm", "제목 없음");
            const poster = getText(db, "poster");
            const genre = getText(db, "genrenm", "장르 미상");
            const fcltynm = getText(db, "fcltynm", "장소 미상");
            const prfstate = getText(db, "prfstate", "상태 미상");

            let stateColor = 'bg-gray-100 text-gray-600';
            if(prfstate.includes('공연중')) stateColor = 'bg-pink-100 text-pink-700';
            else if(prfstate.includes('예정')) stateColor = 'bg-blue-100 text-blue-700';

            return `
                <div class="flex flex-col bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover-scale group">
                    <div class="relative w-full aspect-[3/4] bg-gray-50 overflow-hidden">
                        <img src="${poster}" alt="${title}" loading="lazy" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" onerror="this.src='https://via.placeholder.com/300x400?text=No+Image'">
                        <div class="absolute top-2 left-2 ${stateColor} text-[10px] font-bold px-2 py-1 rounded shadow-sm">${prfstate}</div>
                    </div>
                    <div class="p-4 flex flex-col flex-1">
                        <span class="text-[10px] font-bold text-purple-500 mb-1">${genre}</span>
                        <h3 class="font-bold text-gray-900 text-sm truncate-2-lines mb-3 leading-snug" title="${title}">${title}</h3>
                        <div class="mt-auto space-y-1">
                            <p class="text-[11px] text-gray-500 truncate-1-lines" title="${fcltynm}"><i data-lucide="map-pin" class="w-3 h-3 inline mr-1"></i>${fcltynm}</p>
                        </div>
                        <a href="detail.html?id=${id}" target="_blank" class="mt-4 w-full bg-gray-50 hover:bg-purple-600 hover:text-white text-gray-600 text-xs font-bold py-2 rounded-lg text-center transition-colors">상세보기</a>
                    </div>
                </div>`;
        }).join('');

        listContainer.innerHTML = itemsHtml;

    } catch (error) {
        listContainer.innerHTML = '<div class="text-red-500 col-span-full py-10 text-center">공연 목록 데이터를 불러오지 못했습니다.</div>';
    }
}