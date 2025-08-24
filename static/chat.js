async function sendMessage() {
    const input = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
  
    const message = input.value.trim();
    if (!message) return;
  
    chatBox.innerHTML += `<div class="user-msg">${message}</div>`;
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;
  
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });
      const data = await res.json();
      const reply = data.reply || data.error || "No response.";
      chatBox.innerHTML += `<div class="bot-msg">${reply}</div>`;
      chatBox.scrollTop = chatBox.scrollHeight;
    } catch (err) {
      chatBox.innerHTML += `<div class="bot-msg text-danger">Error: could not connect</div>`;
    }
  }
  
  // Active Link Highlight
document.querySelectorAll('.nav-link').forEach(link => {
  if(link.href === window.location.href) {
    link.classList.add('active');
  }
});

// Dark Mode Toggle
document.getElementById('toggle-dark').addEventListener('click', () => {
  document.body.classList.toggle('dark-mode');
  const darkModeEnabled = document.body.classList.contains('dark-mode');
  localStorage.setItem('darkMode', darkModeEnabled);
});

// Remember user's dark mode preference
window.addEventListener('DOMContentLoaded', () => {
  if(localStorage.getItem('darkMode') === 'true'){
    document.body.classList.add('dark-mode');
  }
});
