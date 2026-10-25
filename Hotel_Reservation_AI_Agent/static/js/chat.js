(() => {
  const toggle = document.getElementById("chat-toggle");
  const panel = document.getElementById("chat-panel");
  const close = document.getElementById("chat-close");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("chat-messages");
  if (!toggle || !panel || !form) return;

  const addBubble = (text, who) => {
    const node = document.createElement("div");
    node.className = `bubble ${who}`;
    node.textContent = text;
    messages.appendChild(node);
    messages.scrollTop = messages.scrollHeight;
  };
  toggle.addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) input.focus();
  });
  close.addEventListener("click", () => panel.classList.add("hidden"));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    addBubble(message, "user");
    input.value = "";
    const waiting = document.createElement("div");
    waiting.className = "bubble bot";
    waiting.textContent = "Thinking...";
    messages.appendChild(waiting);
    messages.scrollTop = messages.scrollHeight;
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message})
      });
      const data = await response.json();
      waiting.textContent = data.reply || "Sorry, I couldn't answer that.";
    } catch (_error) {
      waiting.textContent = "The assistant is temporarily unavailable. Please try again.";
    }
    messages.scrollTop = messages.scrollHeight;
  });
})();