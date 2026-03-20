const signupForm = document.getElementById('signupForm');
const submitBtn = document.getElementById('submitBtn');

const fields = {
    userId: { el: document.getElementById('userId'), msg: document.getElementById('idMsg'), regex: /^[a-zA-Z0-9]{5,}$/, error: "5자 이상의 영문/숫자여야 합니다." },
    email: { el: document.getElementById('userEmail'), msg: document.getElementById('emailMsg'), regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, error: "유효한 이메일 형식이 아닙니다." },
    pw: { el: document.getElementById('password'), msg: document.getElementById('pwMsg'), regex: /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$/, error: "영문/숫자/특수문자 포함 8자 이상이어야 합니다." }
};

const confirmPw = document.getElementById('passwordConfirm');
const confirmMsg = document.getElementById('confirmMsg');

function validate() {
    let isAllValid = true;

    for (let key in fields) {
        const item = fields[key];
        if (item.regex.test(item.el.value)) {
            item.msg.textContent = "사용 가능합니다.";
            item.msg.className = "msg success";
            item.msg.style.color = "green";
        } else {
            item.msg.textContent = item.el.value ? item.error : "";
            item.msg.className = "msg error";
            item.msg.style.color = "red";
            isAllValid = false;
        }
    }

    if (fields.pw.el.value === confirmPw.value && confirmPw.value !== "") {
        confirmMsg.textContent = "비밀번호가 일치합니다.";
        confirmMsg.className = "msg success";
        confirmMsg.style.color = "green";
    } else {
        confirmMsg.textContent = confirmPw.value ? "비밀번호가 일치하지 않습니다." : "";
        confirmMsg.className = "msg error";
        confirmMsg.style.color = "red";
        isAllValid = false;
    }

    const nameVal = document.getElementById('userName').value;
    const addrVal = document.getElementById('userAddress').value;
    const phoneVal = document.getElementById('userPhone').value;
    if(!nameVal || !addrVal || !phoneVal) {
        isAllValid = false;
    }

    submitBtn.disabled = !isAllValid;
}

async function register() {
    const formData = new FormData();
    formData.append('user_id', document.getElementById('userId').value);
    formData.append('password', document.getElementById('password').value);
    formData.append('user_name', document.getElementById('userName').value);
    formData.append('phone', document.getElementById('userPhone').value);
    formData.append('addr', document.getElementById('userAddress').value);
    formData.append('email', document.getElementById('userEmail').value);

    try {
        // 💡 하드코딩 IP 제거! Nginx 설정에 따라 프록시 처리됨
        const res = await fetch('/api/member/register', { 
            method: 'POST', 
            body: formData 
        });
        
        const result = await res.json();
        console.log("Server Response:", result);
        
        if(result.status === 'success') {
            alert(result.message);
            location.href = './login.html'; 
        } else {
            alert(result.message);
        }
    } catch (error) {
        console.error('Fetch Error:', error);
        alert(`서버와 통신 중 문제가 발생했습니다.`);
    }
}

Object.values(fields).forEach(item => item.el.addEventListener('input', validate));
confirmPw.addEventListener('input', validate);
document.getElementById('userName').addEventListener('input', validate);
document.getElementById('userAddress').addEventListener('input', validate);
document.getElementById('userPhone').addEventListener('input', validate);

signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await register();
});