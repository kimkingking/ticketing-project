window.onload = function() {
    createSeats();
};

const MAX_ROWS = 26; // 이미지처럼 26줄
const MAX_COLS = 20;
let selectedSeats = [];

function createSeats() {
    const grid = document.getElementById('seatGrid');
    
    for (let r = 1; r <= MAX_ROWS; r++) {
        // 행 번호 추가
        const rowLabel = document.createElement('div');
        rowLabel.className = 'row-label';
        rowLabel.innerText = r;
        grid.appendChild(rowLabel);

        for (let c = 1; c <= MAX_COLS; c++) {
            const seat = document.createElement('div');
            seat.className = 'seat';
            
            // 랜덤으로 이미 팔린 좌석(occupied) 설정 (시뮬레이션)
            if (Math.random() < 0.1) {
                seat.classList.add('occupied');
            }

            seat.onclick = () => toggleSeat(seat, r, c);
            grid.appendChild(seat);
        }
    }
}

function toggleSeat(el, row, col) {
    if (el.classList.contains('occupied')) return;

    const seatId = `${row}행-${col}번`;

    if (el.classList.contains('selected')) {
        el.classList.remove('selected');
        selectedSeats = selectedSeats.filter(s => s !== seatId);
    } else {
        if (selectedSeats.length >= 2) {
            alert("최대 2석까지만 선택 가능합니다.");
            return;
        }
        el.classList.add('selected');
        selectedSeats.push(seatId);
    }

    updateSummary();
}

function updateSummary() {
    const listEl = document.getElementById('selectedSeatList');
    if (selectedSeats.length === 0) {
        listEl.innerText = "좌석을 선택해 주세요.";
    } else {
        listEl.innerHTML = selectedSeats.join('<br>');
    }
}

function finishSelection() {
    if (selectedSeats.length === 0) {
        alert("좌석을 선택하지 않으셨습니다.");
    } else {
        alert(`🎉 [${selectedSeats.join(', ')}] 예매가 완료되었습니다!`);
        location.href = "index.html"; // 메인으로 돌아가기
    }
}