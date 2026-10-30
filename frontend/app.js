// Chat-Oberfläche von JARVIS.
const messagesEl = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const usageEl = document.getElementById("usage");

// --- Hilfsfunktionen ---

// Kleiner API-Helfer: bei fehlendem Login zurück zur Login-Seite.
async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 401) {
    window.location.href = "/login";
    throw new Error("Nicht eingeloggt");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Unbekannter Fehler");
  return data;
}

// Wandelt einfachen Markdown-Text sicher in HTML um.
// Wichtig: Erst ALLES escapen, dann nur unsere eigenen Tags einfügen (Schutz vor Code-Injection).
function renderMarkdown(text) {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

  // Codeblöcke zuerst herausnehmen, damit darin nichts weiter formatiert wird.
  const blocks = [];
  let html = escaped.replace(/```[\w-]*\n?([\s\S]*?)```/g, (_, code) => {
    blocks.push(`<pre><code>${code.trim()}</code></pre>`);
    return `\u0000${blocks.length - 1}\u0000`;
  });

  html = html
    .replace(/`([^`\n]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])_([^_\n]+)_(?=[\s).,!?]|$)/g, "$1<em>$2</em>")
    .replace(/^- (.*)$/gm, "• $1")
    .replace(/\n/g, "<br>");

  return html.replace(/\u0000(\d+)\u0000/g, (_, i) => blocks[Number(i)]);
}

function addMessage(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `msg ${role}`;
  bubble.innerHTML = renderMarkdown(text);
  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

function showEmptyState() {
  messagesEl.innerHTML = "";
  const hint = document.createElement("div");
  hint.className = "empty";
  hint.textContent = "Zu Diensten. Womit kann ich helfen?";
  messagesEl.appendChild(hint);
}

async function refreshUsage() {
  try {
    const data = await api("/api/usage");
    usageEl.textContent = `${data.month_cost_usd.toFixed(2)} $`;
  } catch { /* nicht kritisch */ }
}

// Textfeld wächst mit dem Inhalt mit
function autoResize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
}

// --- Ablauf ---

async function loadConversation() {
  const data = await api("/api/conversation");
  if (data.messages.length === 0) {
    showEmptyState();
    return;
  }
  messagesEl.innerHTML = "";
  data.messages.forEach((m) => addMessage(m.role, m.content));
}

async function sendMessage(text) {
  messagesEl.querySelector(".empty")?.remove();
  addMessage("user", text);
  const thinking = addMessage("assistant thinking", "…");
  sendBtn.disabled = true;

  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: text }),
    });
    thinking.remove();
    addMessage("assistant", data.reply);
    refreshUsage();
  } catch (err) {
    thinking.remove();
    addMessage("error", err.message);
    input.value = text; // Nachricht nicht verlieren – erneut senden möglich
    autoResize();
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || sendBtn.disabled) return;
  input.value = "";
  autoResize();
  sendMessage(text);
});

// Enter = senden, Shift+Enter = neue Zeile (nur am Computer sinnvoll)
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !("ontouchstart" in window)) {
    event.preventDefault();
    form.requestSubmit();
  }
});
input.addEventListener("input", autoResize);

document.getElementById("new-chat").addEventListener("click", async () => {
  await api("/api/conversation/new", { method: "POST" });
  showEmptyState();
});

document.getElementById("logout").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  window.location.href = "/login";
});

loadConversation();
refreshUsage();
