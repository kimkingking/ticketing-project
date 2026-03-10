// 공공데이터 서버에 접속하기 위한 비밀번호
const API_KEY = "76bdb5ba111645e394169b887d8a5e33";

// 날짜 형식을 서버가 이해하기 쉽게 (예: 2026-03-09 -> 20260309) 바꿔주는 도구
function formatDate(dateString) {
    return dateString.replace(/-/g, '');
}

// 사용자가 페이지에서 입력한 데이터를 저장하는 변수 
function getInputDateFormat(date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
}


// 페이지가 처음 열리자마자 자동으로 실행되는 명령어들입니다.
window.onload = function() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(endDate.getMonth() - 1); 

    document.getElementById('startDate').value = getInputDateFormat(startDate);
    document.getElementById('endDate').value = getInputDateFormat(endDate);

    fetchPerformanceList();
    fetchBoxOffice();
};

// [기능 1] 공연 목록과 가격 정보를 가져오는 함수입니다.
async function fetchPerformanceList() {
    // 사용자가 선택한 장르와 날짜를 읽어옵니다.
    const stdate = document.getElementById('startDate').value; // 시작 날짜
    const eddate = document.getElementById('endDate').value; // 종료 날짜
    const genreCode = document.getElementById('genreSelect').value; // 장르코드
    const listContainer = document.getElementById('performanceList'); //  공연 목록 

    if (!stdate || !eddate) return; // 날짜가 없으면 아무것도 안 함

    listContainer.innerHTML = '목록과 가격 정보를 함께 불러오는 중입니다...';

    // 공공기관(KOPIS) 서버에 "정보 좀 주세요~"라고 요청할 주소를 만듭니다.
    let pblprfrUrl = `http://www.kopis.or.kr/openApi/restful/pblprfr?service=${API_KEY}&stdate=${formatDate(stdate)}&eddate=${formatDate(eddate)}&cpage=1&rows=10`;
    
    if (genreCode) {
        pblprfrUrl += `&shcate=${genreCode}`;
    }

    const targetUrl = encodeURIComponent(pblprfrUrl);
    const url = `https://corsproxy.io/?${targetUrl}`;

    //
    try {
        const response = await fetch(url);
        const textData = await response.text();
        
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(textData, "text/xml");
        const dbs = xmlDoc.getElementsByTagName("db");
        
        if (dbs.length === 0) {
            listContainer.innerHTML = '선택하신 조건에 해당하는 공연이 없습니다.';
            return;
        }

        const detailPromises = [];

        for (let i = 0; i < dbs.length; i++) {
            const id = dbs[i].getElementsByTagName("mt20id")[0]?.textContent;
            const title = dbs[i].getElementsByTagName("prfnm")[0]?.textContent || '제목 없음';
            const poster = dbs[i].getElementsByTagName("poster")[0]?.textContent || '';
            const genre = dbs[i].getElementsByTagName("genrenm")[0]?.textContent || '';
            const fcltynm = dbs[i].getElementsByTagName("fcltynm")[0]?.textContent || '';
            const prfstate = dbs[i].getElementsByTagName("prfstate")[0]?.textContent || '';

            const fetchDetail = async () => {
                let price = '가격 정보 없음';
                if (id) {
                    const detailUrl = encodeURIComponent(`http://www.kopis.or.kr/openApi/restful/pblprfr/${id}?service=${API_KEY}`);
                    const detailProxiedUrl = `https://corsproxy.io/?${detailUrl}`;
                    try {
                        const detailRes = await fetch(detailProxiedUrl);
                        const detailText = await detailRes.text();
                        const detailDoc = parser.parseFromString(detailText, "text/xml");
                        price = detailDoc.getElementsByTagName("pcseguidance")[0]?.textContent || '가격 정보 없음';
                    } catch (e) {
                        console.error(`가격 오류 (${id}):`, e);
                    }
                }
                // ⭐ 링크 생성을 위해 반환값에 id 추가
                return { id, title, poster, genre, fcltynm, prfstate, price };
            };
            detailPromises.push(fetchDetail());
        }

        const performances = await Promise.all(detailPromises);

        listContainer.innerHTML = '';
        performances.forEach(perf => {
            // ⭐ a 태그(상세보기 버튼) 추가 (KOPIS 공식 홈페이지 상세 화면으로 연결)
            listContainer.innerHTML += `
                <div class="card">
                    <img src="${perf.poster}" alt="포스터" onerror="this.src='https://via.placeholder.com/100x140?text=No+Image'">
                    <div class="card-content">
                        <h3>${perf.title}</h3>
                        <p><strong>장르:</strong> ${perf.genre}</p>
                        <p><strong>장소:</strong> ${perf.fcltynm}</p>
                        <p><strong>상태:</strong> ${perf.prfstate}</p>
                        <p><strong>티켓가격:</strong> <span class="price-text">${perf.price}</span></p>
                       <a href="detail.html?id=${perf.id}" target="_blank" class="detail-btn">🔍 상세보기</a>
                    </div>
                </div>
            `;
        });
    } catch (error) {
        console.error(error);
        listContainer.innerHTML = '데이터를 불러오는 중 오류가 발생했습니다.';
    }
}

// [기능 2] 인기 순위(박스오피스)를 가져오는 함수입니다.
async function fetchBoxOffice() {
    // 공연 목록과 비슷하게 인기 순위 데이터를 서버에서 가져와 화면에 보여줍니다
    const stdate = document.getElementById('startDate').value;
    const eddate = document.getElementById('endDate').value;
    const genreCode = document.getElementById('genreSelect').value;
    const boxContainer = document.getElementById('boxOfficeList');

    if (!stdate || !eddate) return;

    boxContainer.innerHTML = '예매 상황과 가격 정보를 불러오는 중입니다...';

    let boxOfficeUrl = `http://www.kopis.or.kr/openApi/restful/boxoffice?service=${API_KEY}&stdate=${formatDate(stdate)}&eddate=${formatDate(eddate)}`;
    
    if (genreCode) {
        boxOfficeUrl += `&catecode=${genreCode}`;
    }

    const targetUrl = encodeURIComponent(boxOfficeUrl);
    const url = `https://corsproxy.io/?${targetUrl}`;

    try {
        const response = await fetch(url);
        const textData = await response.text();
       
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(textData, "text/xml");
        const boxofs = xmlDoc.getElementsByTagName("boxof");

        if (boxofs.length === 0) {
            boxContainer.innerHTML = '선택하신 조건의 예매 상황 데이터가 없습니다.';
            return;
        }
        console.log(boxofs);
        const detailPromises = [];
        const maxCount = Math.min(boxofs.length, 10);

        for (let i = 0; i < maxCount; i++) {
            const id = boxofs[i].getElementsByTagName("mt20id")[0]?.textContent;
            const rank = boxofs[i].getElementsByTagName("rnum")[0]?.textContent || '';
            const title = boxofs[i].getElementsByTagName("prfnm")[0]?.textContent || '';
            const poster = boxofs[i].getElementsByTagName("poster")[0]?.textContent || '';
            const area = boxofs[i].getElementsByTagName("area")[0]?.textContent || '';
            const seatcnt = boxofs[i].getElementsByTagName("seatcnt")[0]?.textContent || '';

            const fetchDetail = async () => {
                let price = '가격 정보 없음';
                if (id) {
                    const detailUrl = encodeURIComponent(`http://www.kopis.or.kr/openApi/restful/pblprfr/${id}?service=${API_KEY}`);
                    const detailProxiedUrl = `https://corsproxy.io/?${detailUrl}`;
                    try {
                        const detailRes = await fetch(detailProxiedUrl);
                        const detailText = await detailRes.text();
                        const detailDoc = parser.parseFromString(detailText, "text/xml");
                        price = detailDoc.getElementsByTagName("pcseguidance")[0]?.textContent || '가격 정보 없음';
                    } catch (e) {
                        console.error(`가격 오류 (${id}):`, e);
                    }
                }
                // ⭐ 링크 생성을 위해 반환값에 id 추가
                return { id, rank, title, poster, area, seatcnt, price };
            };
            
            detailPromises.push(fetchDetail());
        }

        const boxOfficeItems = await Promise.all(detailPromises);

        boxContainer.innerHTML = '';
        boxOfficeItems.forEach(item => {
            // ⭐ a 태그(상세보기 버튼) 추가 (KOPIS 공식 홈페이지 상세 화면으로 연결)
            boxContainer.innerHTML += `
                <div class="card">
                    <img src="${item.poster}" alt="포스터" onerror="this.src='https://via.placeholder.com/100x140?text=No+Image'">
                        <div class="card-content">
                        <h3><span class="rank-badge">${item.rank}위</span> ${item.title}</h3>
                        <p><strong>지역:</strong> ${item.area}</p>
                        <p><strong>좌석 수:</strong> ${item.seatcnt}석</p>
                        <p><strong>티켓가격:</strong> <span class="price-text">${item.price}</span></p>
                        <a href="detail.html?id=${item.id}" target="_blank" class="detail-btn">🔍 상세보기</a>
                    </div>
                </div>
            `;
        });
    } catch (error) {
        console.error(error);
        boxContainer.innerHTML = '데이터를 불러오는 중 오류가 발생했습니다.';
    }
}