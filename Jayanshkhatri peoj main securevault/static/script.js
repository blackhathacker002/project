// static/script.js

document.addEventListener('DOMContentLoaded', () => {
    console.log("SecureVault System Initialized...");

    // Add a subtle glow follow effect to glass cards
    const cards = document.querySelectorAll('.glass-card');
    
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });

    // Auto-focus the first input on any page
    const firstInput = document.querySelector('input');
    if (firstInput) firstInput.focus();
}); 
// ===== SCROLL REVEAL SYSTEM =====
const reveals = document.querySelectorAll(".reveal");

const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add("show");
        }
    });
}, {
    threshold: 0.15
});

reveals.forEach(el => observer.observe(el)); 