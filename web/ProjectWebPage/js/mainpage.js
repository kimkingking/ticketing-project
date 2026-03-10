const API_KEY = "76bdb5ba111645e394169b887d8a5e33";
const parser = new DOMParser();

window.onload = async () => {
    initDates();
    await refreshData();
    
    // 로딩 화면 제거
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => loader.style.display = 'none', 700);
    }
};

function initDates() {
    const end = new Date();
    const start = new Date();
    start.setMonth(end.getMonth() - 1);
    document.getElementById('startDate').value = start.toISOString().split('T')[0];
    document.getElementById('endDate').value = end.toISOString().split('T')[0];
}

async function refreshData() {
    await Promise.all([fetchBoxOffice(), fetchPerformanceList()]);
    if (window.lucide) lucide.createIcons();
}

// 1. 박스오피스 TOP 10 (가로 스크롤)
async function fetchBoxOffice() {
    const container = document.getElementById('boxOfficeList');
    const stdate = document.getElementById('startDate').value.replace(/-/g, '');
    const eddate = document.getElementById('endDate').value.replace(/-/g, '');
    const cate = document.getElementById('genreSelect').value;

    let url = `https://corsproxy.io/?${encodeURIComponent(`http://www.kopis.or.kr/openApi/restful/boxoffice?service=${API_KEY}&stdate=${stdate}&eddate=${eddate}&catecode=${cate}`)}`;

    try {
        const res = await fetch(url);
        const xml = parser.parseFromString(await res.text(), "text/xml");
        const items = xml.getElementsByTagName("boxof");
        container.innerHTML = '';

        for (let i = 0; i < Math.min(items.length, 10); i++) {
            const id = items[i].getElementsByTagName("mt20id")[0].textContent;
            const title = items[i].getElementsByTagName("prfnm")[0].textContent;
            const poster = items[i].getElementsByTagName("poster")[0].textContent;
            const rank = items[i].getElementsByTagName("rnum")[0].textContent;

            container.innerHTML += `
                <div onclick="openDetail('${id}')" class="boxoffice-card">
                    <div style="position: relative;">
                        <img src="${poster}" alt="${title}">
                        <div style="position: absolute; top: 10px; left: 10px; background: #06b6d4; color: #000; font-weight: 900; padding: 2px 8px; border-radius: 4px; font-size: 11px;">
                            ${rank}위
                        </div>
                    </div>
                    <div class="truncate-custom" style="margin-top: 10px; font-weight: bold; font-size: 14px; color: #fff;">${title}</div>
                </div>
            `;
        }
    } catch (e) { console.error("BoxOffice Error:", e); }
}

// 2. 공연 목록 (그리드 리스트)
async function fetchPerformanceList() {
    const container = document.getElementById('performanceList');
    const stdate = document.getElementById('startDate').value.replace(/-/g, '');
    const eddate = document.getElementById('endDate').value.replace(/-/g, '');
    const cate = document.getElementById('genreSelect').value;

    let url = `https://corsproxy.io/?${encodeURIComponent(`http://www.kopis.or.kr/openApi/restful/pblprfr?service=${API_KEY}&stdate=${stdate}&eddate=${eddate}&shcate=${cate}&cpage=1&rows=12`)}`;

    try {
        const res = await fetch(url);
        const xml = parser.parseFromString(await res.text(), "text/xml");
        const items = xml.getElementsByTagName("db");
        container.innerHTML = '';

        for (let i = 0; i < items.length; i++) {
            const id = items[i].getElementsByTagName("mt20id")[0].textContent;
            const title = items[i].getElementsByTagName("prfnm")[0].textContent;
            const poster = items[i].getElementsByTagName("poster")[0].textContent;
            const venue = items[i].getElementsByTagName("fcltynm")[0].textContent;
            const state = items[i].getElementsByTagName("prfstate")[0].textContent;

            container.innerHTML += `
                <div onclick="openDetail('${id}')" class="perf-card">
                    <img src="${poster}" alt="${title}">
                    <div style="flex: 1; min-width: 0;">
                        <span style="font-size: 10px; color: #22d3ee; border: 1px solid rgba(34,211,238,0.3); padding: 1px 6px; border-radius: 10px; margin-bottom: 8px; display: inline-block;">${state}</span>
                        <div class="truncate-custom" style="font-weight: bold; color: #fff; font-size: 15px; margin-bottom: 8px;">${title}</div>
                        <div class="truncate-custom" style="font-size: 12px; color: #64748b;">📍 ${venue}</div>
                    </div>
                </div>
            `;
        }
    } catch (e) { console.error("List Error:", e); }
}

// 3. 상세 팝업 및 닫기
async function openDetail(id) {
    const modal = document.getElementById('modal-container');
    const content = document.getElementById('modal-content');
    modal.classList.replace('hidden', 'flex');
    content.innerHTML = `<div style="padding: 50px; color: #06b6d4; font-weight: bold; text-align: center;">데이터 로딩 중...</div>`;

    try {
        const url = `https://corsproxy.io/?${encodeURIComponent(`http://www.kopis.or.kr/openApi/restful/pblprfr/${id}?service=${API_KEY}`)}`;
        const res = await fetch(url);
        const xml = parser.parseFromString(await res.text(), "text/xml");
        const db = xml.getElementsByTagName("db")[0];

        const prfnm = db.getElementsByTagName("prfnm")[0].textContent;
        const poster = db.getElementsByTagName("poster")[0].textContent;
        const fcltynm = db.getElementsByTagName("fcltynm")[0].textContent;
        const prfpd = `${db.getElementsByTagName("prfpdfrom")[0].textContent} ~ ${db.getElementsByTagName("prfpdto")[0].textContent}`;
        const pcse = db.getElementsByTagName("pcseguidance")[0].textContent;

        content.innerHTML = `
            <div style="display: flex; flex-direction: row; width: 100%; background: #0f172a; border-radius: 20px; overflow: hidden; position: relative;">
                <button onclick="closeModal()" style="position: absolute; top: 15px; right: 15px; background: rgba(0,0,0,0.5); color: #fff; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer;">X</button>
                <img src="${poster}" style="width: 40%; object-fit: cover;">
                <div style="width: 60%; padding: 40px; color: #fff;">
                    <h2 style="font-size: 24px; font-weight: 900; margin-bottom: 20px;">${prfnm}</h2>
                    <div style="font-size: 14px; color: #94a3b8; line-height: 2;">
                        <p><b>기간:</b> ${prfpd}</p>
                        <p><b>장소:</b> ${fcltynm}</p>
                        <p><b>가격:</b> ${pcse}</p>
                    </div>
                    <button style="margin-top: 30px; width: 100%; padding: 15px; background: #06b6d4; border: none; border-radius: 10px; font-weight: bold; cursor: pointer;">예매하기</button>
                </div>
            </div>
        `;
    } catch (e) { content.innerHTML = `<div style="padding: 50px;">정보를 불러올 수 없습니다.</div>`; }
}

function closeModal() {
    document.getElementById('modal-container').classList.replace('flex', 'hidden');
}
