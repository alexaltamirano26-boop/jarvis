// Login-Seite: schickt das Passwort an den Server und leitet bei Erfolg zum Chat weiter.
const form = document.getElementById("login-form");
const errorBox = document.getElementById("error");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  const password = document.getElementById("password").value;

  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });

  if (res.ok) {
    window.location.href = "/";
  } else {
    const data = await res.json().catch(() => ({}));
    errorBox.textContent = data.detail || "Anmeldung fehlgeschlagen.";
    errorBox.hidden = false;
  }
});
