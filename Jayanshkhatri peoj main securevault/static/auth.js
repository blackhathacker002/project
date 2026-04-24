const loginTab = document.getElementById("loginTab");
const signupTab = document.getElementById("signupTab");

const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");

loginTab.onclick = () => {
    loginTab.classList.add("active");
    signupTab.classList.remove("active");

    loginForm.style.display = "block";
    signupForm.style.display = "none";
};

signupTab.onclick = () => {
    signupTab.classList.add("active");
    loginTab.classList.remove("active");

    signupForm.style.display = "block";
    loginForm.style.display = "none";
}; 