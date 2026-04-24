let lastScroll = 0;
const navbar = document.getElementById("navbar");

window.addEventListener("scroll", () => {
    let current = window.scrollY;

    if (current > lastScroll) {
        navbar.classList.add("hide");
    } else {
        navbar.classList.remove("hide");
    }

    lastScroll = current;
}); 