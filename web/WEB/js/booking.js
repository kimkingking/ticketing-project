let perfInfo = {};
let selectedSeat = null;
let turnstileToken = ""; // 전역 토큰 저장용

function safeNavigate(url) { window.location.href = url; }

// [추가] 캡차 콜백 함수
window.javascriptCallback = function(token) {
    console.log("캡차 인증 성공");
    turnstileToken = token;
    
    // 💡 인증 성공 시 모달 확실하게 닫기 (flex 제거 후 hidden 추가)
    const modal = document.getElementById('captchaModal');
    if(modal) {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
    }
};

document.addEventListener('DOMContentLoaded', async () => {
    updateHeaderUI();
    if (typeof lucide !== 'undefined') lucide.createIcons();

    let userId = sessionStorage.getItem('u_id');
    if (!userId) {
        userId = 'test_user';
        sessionStorage.setItem('u_id', userId);
        sessionStorage.setItem('ename', '테스터');
        updateHeaderUI(); 
    }

    const urlParams = new URLSearchParams(window.location.search);
    perfInfo = {
        perf_id: urlParams.get('id') || 'TEST_PERF_001',
        perf_title: urlParams.get('title') || '테스트 고정 공연',
        select_date: urlParams.get('date') || '2026-05-01',
        select_time: urlParams.get('time') || '19:00',
        place: urlParams.get('place') || 'PULSE 그랜드 시어터',
        price: parseInt(urlParams.get('price')) || 100000,
        poster: urlParams.get('poster') || 'https://via.placeholder.com/300x420?text=Test+Poster'
    };

    document.getElementById('infoPoster').src = perfInfo.poster;
    document.getElementById('infoTitle').textContent = perfInfo.perf_title;
    document.getElementById('infoDateTime').textContent = `${perfInfo.select_date} ${perfInfo.select_time}`;
    document.getElementById('infoPlace').textContent = perfInfo.place;

    const reservedSeats = await fetchReservedSeats();
    renderSeats(reservedSeats);
});

async function fetchReservedSeats() {
    try {
        const url = `/api/reservations/seats?perf_id=${perfInfo.perf_id}&date=${perfInfo.select_date}&time=${perfInfo.select_time}`;
        const response = await fetch(url);
        const data = await response.json();
        if (data.status === 'success') {
            return data.reserved_seats;
        }
    } catch (e) {
        console.error("예약된 좌석 정보 로딩 실패:", e);
    }
    return []; 
}

function renderSeats(reservedSeats) {
    const container = document.getElementById('seatContainer');
    container.innerHTML = '';
    
    for (let i = 1; i <= 20; i++) {
        const seatNum = `S${i}`;
        const btn = document.createElement('button');
        btn.textContent = seatNum;
        
        if (reservedSeats.includes(seatNum)) {
            // 이미 예약된 좌석: 회색 배경, 회색 글씨, 클릭 불가 마우스 커서 적용
            btn.className = `seat w-12 h-12 rounded-lg border-2 font-bold OCCUPIED bg-gray-300 text-gray-500 cursor-not-allowed`;
            btn.disabled = true; 
        } else {
            btn.className = `seat w-12 h-12 rounded-lg border-2 font-bold AVAILABLE hover:bg-purple-100 transition-colors`;
            btn.onclick = () => {
                selectedSeat = { seat_num: seatNum };
                
                // 다른 좌석 선택 해제 및 현재 좌석 선택 표시
                document.querySelectorAll('.seat.AVAILABLE').forEach(s => {
                    s.classList.remove('SELECTED', 'bg-purple-600', 'text-white');
                });
                btn.classList.add('SELECTED', 'bg-purple-600', 'text-white');
                
                document.getElementById('infoSeat').textContent = btn.textContent;
                document.getElementById('infoPrice').textContent = `${perfInfo.price.toLocaleString()}원`;
                
                const rb = document.getElementById('btnReserve');
                rb.disabled = false;
                rb.className = "w-full bg-purple-600 hover:bg-purple-700 text-white font-bold text-lg py-4 rounded-xl transition-all shadow-lg shadow-purple-200 transform hover:-translate-y-1";
                rb.textContent = "결제하기";
            };
        }
        container.appendChild(btn);
    }
}

async function processReservation() {
    if (!selectedSeat || !turnstileToken) {
        alert("인증 정보가 없거나 좌석이 선택되지 않았습니다.");
        return;
    }
    
    const reserveBtn = document.getElementById('btnReserve');
    reserveBtn.disabled = true;
    reserveBtn.textContent = "처리 중...";

    const payload = {
        user_id: sessionStorage.getItem('u_id'),
        seat_num: selectedSeat.seat_num, 
        perf_id: perfInfo.perf_id,
        perf_title: perfInfo.perf_title,
        select_date: perfInfo.select_date,
        select_time: perfInfo.select_time,
        place: perfInfo.place,
        price: perfInfo.price,
        turnstile_token: turnstileToken 
    };

    try {
        const response = await fetch(`/api/reservations/confirm`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            alert(result.message);
            location.href = 'mypage.html';
        } else if (result.status === "fail") {
            // 💡 [핵심 수정] 누군가 이미 채간 경우, 새로고침 없이 좌석만 업데이트
            alert(result.message); 
            
            // 좌석 최신화
            const updatedReservedSeats = await fetchReservedSeats();
            renderSeats(updatedReservedSeats);
            
            // 우측 정보 및 버튼 초기화 (새로운 좌석을 골라야 하므로)
            selectedSeat = null;
            document.getElementById('infoSeat').textContent = "좌석을 선택해주세요";
            document.getElementById('infoPrice').textContent = "0원";
            
            reserveBtn.className = "w-full bg-gray-300 text-gray-500 font-bold text-lg py-4 rounded-xl cursor-not-allowed transition-all";
            reserveBtn.textContent = "결제하기";
            // disabled는 renderSeats가 끝난 상태이므로 이미 선택된 자리가 없으니 true 유지
        } else {
            alert(result.message || "예매 실패");
            location.reload(); 
        }
    } catch (e) {
        console.error("통신 오류:", e);
        alert(`서버 통신에 실패했습니다.`);
        resetReserveButton(reserveBtn);
    }
}

function resetReserveButton(btn) {
    btn.disabled = false;
    btn.innerHTML = "결제하기";
    btn.classList.remove('opacity-75', 'cursor-not-allowed');
}

// 💡 스크립트 에러 방지를 위해 헤더 및 로그아웃 함수 복구
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