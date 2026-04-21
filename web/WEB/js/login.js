if (sessionStorage.getItem('ename')) {
    alert("이미 로그인 상태입니다. 메인페이지로 이동합니다.");
    location.href = "./index.html";
}

async function handleLogin() {
    const idInput = document.getElementById('employeeId').value;
    const pwInput = document.getElementById('password').value;
    const message = document.getElementById('pw-message');
    
    const formData = new FormData();
    formData.append('u_id', idInput);
    formData.append('u_pass', pwInput);

    try {
        message.textContent = "서버와 통신 중...";
        message.style.color = "#3498db";

        // 💡 깔끔한 상대 경로 적용
        const res = await fetch(`/api/member/login`, { 
            method: 'POST', 
            body: formData,
            credentials: 'include'
        });

        const result = await res.json();
        console.log("디버깅 - 서버 응답:", result);

        if (result.status === "success") {
            sessionStorage.setItem('ename', result.nickname);
            sessionStorage.setItem('u_id', idInput);
            
            alert(result.message);
            location.href = './index.html';
        } else {
            message.textContent = result.message || "로그인 실패";
            message.style.color = "#ff4d4d";
            alert("로그인 실패: " + result.message);
        }
    } catch (error) {
        console.error("통신 오류:", error);
        message.textContent = `서버 연결 실패`;
        message.style.color = "#ff4d4d";
        alert(`서버에 연결할 수 없습니다. 네트워크 상태를 확인해주세요.`);
    }
}

const idRegex = /^[a-zA-Z0-9]{5,}$/;

function executeLoginValidation() {
    const idInput = document.getElementById('employeeId');
    const pwInput = document.getElementById('password');
    const message = document.getElementById('pw-message');
    
    // 아이디 검사 유지
    if (!idRegex.test(idInput.value)) {
        message.textContent = "아이디는 5자 이상의 영문/숫자여야 합니다.";
        message.style.color = "#ff4d4d";
        idInput.focus();
        return; 
    }

    // 비밀번호는 '빈칸'인지만 검사하도록 변경!
    if (pwInput.value.trim() === "") {
        message.textContent = "비밀번호를 입력해주세요.";
        message.style.color = "#ff4d4d";
        pwInput.focus();
        return; 
    }

    handleLogin(); // 문제 없으면 서버로 전송
}
document.getElementById('loginBtn').addEventListener('click', executeLoginValidation);

document.getElementById('employeeId').addEventListener('keyup', function(event) {
    if (event.key === 'Enter') executeLoginValidation();
});

document.getElementById('password').addEventListener('keyup', function(event) {
    if (event.key === 'Enter') executeLoginValidation();
});