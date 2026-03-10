/* --- [공통] 메뉴 및 로그인 상태 제어 --- */
function updateMenu() {
    const userId = localStorage.getItem('userId');
    const userName = localStorage.getItem('userName');
    const navMenu = document.getElementById('nav-menu');

    if (!navMenu) return;

    if (userId) {
        // 로그인 된 상태
        navMenu.innerHTML = `
            <div>
                <a href="index.html">홈(게시판)</a>
            </div>
            <div class="user-info">
                <span>👤 ${userName}님 접속 중</span> | 
                <a href="#" onclick="logout()" style="margin-left:10px; font-size:0.8em;">로그아웃</a>
            </div>
        `;
    } else {
        // 로그인 안 된 상태
        navMenu.innerHTML = `
            <div>
                <a href="index.html">홈(게시판)</a>
                <a href="login.html">로그인</a>
                <a href="register.html">회원가입</a>
            </div>
        `;
    }
}

function logout() {
    localStorage.clear();
    alert("로그아웃 되었습니다.");
    location.href = "index.html";
}

/* --- [회원] 가입 및 로그인 --- */
async function register() {
    const formData = new FormData();
    formData.append('u_id', document.getElementById('reg_id').value);
    formData.append('u_pass', document.getElementById('reg_pass').value);
    formData.append('u_name', document.getElementById('reg_name').value);
	formData.append('u_nick', document.getElementById('reg_nick').value);
	formData.append('u_age', document.getElementById('reg_age').value);
	formData.append('u_email', document.getElementById('reg_email').value);

    const res = await fetch('/api/member/register', { method: 'POST', body: formData });
    const result = await res.json();
    alert(result.message);
    if(result.status === 'success') location.href = 'login.html';
}

async function login() {
    const formData = new FormData();
    formData.append('u_id', document.getElementById('login_id').value);
    formData.append('u_pass', document.getElementById('login_pass').value);

    const res = await fetch('/api/member/login', { method: 'POST', body: formData });
    const result = await res.json();
    
    if(result.status === 'success') {
        localStorage.setItem('userId', document.getElementById('login_id').value);
        localStorage.setItem('userName', result.nickname || result.user || '사용자');
        localStorage.setItem('userEmail', result.email || '');
        alert(result.message);
        location.href = 'index.html';
    } else {
        alert(result.message);
    }
}

/* --- [게시판] 목록, 작성, 상세보기 --- */
async function loadBoard() {
    const res = await fetch('/api/board/list');
    const data = await res.json();
    const tbody = document.querySelector('#board-table tbody');
    if(!tbody) return;
    tbody.innerHTML = '';
    data.forEach(post => {
        tbody.innerHTML += `
            <tr>
                <td>${post.strNumber}</td>
                <td><a href="view.html?no=${post.strNumber}" style="text-decoration:none; color:#2c3e50;">${post.strSubject}</a></td>
                <td>${post.strName}</td>
                <td>${post.writeDate ? post.writeDate.split('T')[0] : '-'}</td>
            </tr>`;
    });
}

async function writePost() {
    const userId = localStorage.getItem('userId');
    if(!userId) {
        alert("로그인이 필요합니다.");
        return;
    }

    const formData = new FormData();
    formData.append('name', localStorage.getItem('userName'));
    formData.append('pw', document.getElementById('write_pass').value);
    formData.append('subject', document.getElementById('write_title').value);
    formData.append('content', document.getElementById('write_content').value);

    const res = await fetch('/api/board/write', { method: 'POST', body: formData });
    const result = await res.json();
    if(result.status === 'success') {
        alert('글이 등록되었습니다.');
        location.href = 'index.html';
    }
}

async function loadView() {
    const urlParams = new URLSearchParams(window.location.search);
    const postNo = urlParams.get('no');
    const res = await fetch('/api/board/list');
    const data = await res.json();
    const post = data.find(p => p.strNumber == postNo);

    if(post) {
        document.getElementById('v_title').innerText = post.strSubject;
        document.getElementById('v_name').innerText = post.strName;
        document.getElementById('v_date').innerText = post.writeDate.replace('T', ' ');
        document.getElementById('v_content').innerText = post.strContent;
    }
}
/* --- [수정] 상세보기에서 수정 버튼 연동 --- */
async function loadView() {
    const no = new URLSearchParams(window.location.search).get('no');
    const res = await fetch('/api/board/list');
    const data = await res.json();
    const post = data.find(p => p.strNumber == no);
    if(post) {
	console.log("add buttons")
        document.getElementById('v_title').innerText = post.strSubject;
        document.getElementById('v_name').innerText = post.strName;
        document.getElementById('v_date').innerText = post.writeDate.replace('T', ' ');
        document.getElementById('v_content').innerText = post.strContent;
        document.getElementById('view-buttons').innerHTML = `
            <button onclick="location.href='index.html'" class="btn-cancel">목록</button>
            <button onclick="location.href='edit.html?no=${no}'" style="background:#e67e22;">수정</button>
            <button onclick="deletePost(${no})" style="background:#e74c3c;">삭제</button>`;
    }
}

/* --- [신규] 수정 페이지 데이터 로드 --- */
async function loadEditData() {
    const urlParams = new URLSearchParams(window.location.search);
    const no = urlParams.get('no');
    const res = await fetch('/api/board/list');
    const data = await res.json();
    const post = data.find(p => p.strNumber == no);

    if(post) {
        document.getElementById('edit_no').value = post.strNumber;
        document.getElementById('edit_title').value = post.strSubject;
        document.getElementById('edit_content').value = post.strContent;
    }
}

/* --- [신규] 수정 데이터 전송 --- */
async function updatePost() {
    const formData = new FormData();
    formData.append('no', document.getElementById('edit_no').value);
    formData.append('pw', document.getElementById('edit_pass').value);
    formData.append('subject', document.getElementById('edit_title').value);
    formData.append('content', document.getElementById('edit_content').value);

    const res = await fetch('/api/board/update', { method: 'POST', body: formData });
    const result = await res.json();
    alert(result.message);
    if(result.status === 'success') location.href = `view.html?no=${document.getElementById('edit_no').value}`;
}

async function deletePost(no) {
    const pw = prompt("비밀번호를 입력하세요.");
    if(!pw) return;
    const formData = new FormData();
    formData.append('no', no);
    formData.append('pw', pw);
    const res = await fetch('/api/board/delete', { method: 'POST', body: formData });
    const result = await res.json();
    alert(result.message);
    if(result.status === 'success') location.href = 'index.html';
}
