let container = null;

function ensureContainer() {
  if (!container) {
    container = document.getElementById("toast-container");
  }
  return container;
}

export function showToast(message, { type = "info", duration = 4000 } = {}) {
  const root = ensureContainer();
  if (!root) return;

  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.setAttribute("role", "status");
  el.textContent = message;
  root.appendChild(el);

  requestAnimationFrame(() => el.classList.add("visible"));

  setTimeout(() => {
    el.classList.remove("visible");
    setTimeout(() => el.remove(), 300);
  }, duration);
}
