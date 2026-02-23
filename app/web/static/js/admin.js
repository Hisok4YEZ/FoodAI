const API_BASE = window.location.origin;
const TOKEN_KEY = "foodai_admin_token";

const tokenInput = document.getElementById("adminToken");
const saveTokenBtn = document.getElementById("saveTokenBtn");
const refreshBtn = document.getElementById("refreshBtn");
const retrainBtn = document.getElementById("retrainBtn");
const refreshRetrainBtn = document.getElementById("refreshRetrainBtn");
const retrainStatus = document.getElementById("retrainStatus");
const grid = document.getElementById("candidatesGrid");
const filterButtons = Array.from(document.querySelectorAll(".filter"));

let currentStatus = "";

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

async function api(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    "X-Admin-Token": token,
    ...(options.headers || {}),
  };
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

function recipeToText(recipe) {
  if (!recipe) return "(Aucune recette fournie)";
  const ingredients = Array.isArray(recipe.ingredients)
    ? recipe.ingredients.join("\n")
    : "";
  const steps = Array.isArray(recipe.steps) ? recipe.steps.join("\n") : "";
  return `Recette: ${recipe.name || "?"}\nPortions: ${recipe.servings || "?"}\n\nIngredients:\n${ingredients}\n\nEtapes:\n${steps}`;
}

function renderCards(items) {
  if (!items.length) {
    grid.innerHTML = `<div class="empty">Aucun candidat.</div>`;
    return;
  }

  grid.innerHTML = items
    .map((item) => {
      const image = item.image_url
        ? `<img src="${item.image_url}" alt="${item.dish_name}" />`
        : `<span>Aucune image</span>`;
      const tags = `${item.is_new_dish ? '<span class="tag new">Nouveau plat</span>' : '<span class="tag">Deja connu</span>'}<span class="tag">${item.status || "pending"}</span>${item.added_to_training ? '<span class="tag">training set</span>' : ''}`;
      const created = item.created_at ? new Date(item.created_at).toLocaleString("fr-FR") : "-";
      const recipeText = recipeToText(item.recipe_payload);

      return `
      <article class="card">
        <div class="preview">${image}</div>
        <div class="content">
          <div class="title">${item.dish_name || "Sans nom"}</div>
          <div class="meta">${created} • keyword: ${item.source_keyword || "-"} • servings: ${item.servings || "-"}</div>
          <div>${tags}</div>
          <p class="meta">${item.notes || ""}</p>
          <div class="recipe">${recipeText}</div>
          <div class="actions">
            <button class="ok" onclick="updateCandidate('${item.id}','approved',null)">Approve</button>
            <button class="danger" onclick="updateCandidate('${item.id}','rejected',null)">Reject</button>
            <button class="train" onclick="updateCandidate('${item.id}',null,true)">Mark train</button>
          </div>
        </div>
      </article>`;
    })
    .join("");
}

async function loadCandidates() {
  try {
    grid.innerHTML = `<div class="empty">Chargement...</div>`;
    const qs = currentStatus ? `?status=${encodeURIComponent(currentStatus)}` : "";
    const items = await api(`/api/admin/candidates${qs}`);
    renderCards(items);
  } catch (err) {
    grid.innerHTML = `<div class="empty">Erreur: ${err.message}</div>`;
  }
}

async function updateCandidate(id, status, addedToTraining) {
  try {
    const payload = {};
    if (status !== null) payload.status = status;
    if (addedToTraining !== null) payload.added_to_training = addedToTraining;
    await api(`/api/admin/candidates/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    await loadCandidates();
  } catch (err) {
    alert(`Erreur update: ${err.message}`);
  }
}

window.updateCandidate = updateCandidate;

async function loadRetrainStatus() {
  try {
    const status = await api("/api/admin/retrain/status");
    retrainStatus.textContent = JSON.stringify(status, null, 2);
  } catch (err) {
    retrainStatus.textContent = `Erreur statut retrain: ${err.message}`;
  }
}

async function triggerIncrementalRetrain() {
  try {
    retrainStatus.textContent = "Lancement du retrain en cours...";
    const result = await api("/api/admin/retrain/incremental", {
      method: "POST",
      body: JSON.stringify({
        limit_candidates: 50,
        epochs: 2,
        replay_per_class: 20,
      }),
    });
    retrainStatus.textContent = JSON.stringify(result, null, 2);
    await loadCandidates();
    await loadRetrainStatus();
  } catch (err) {
    retrainStatus.textContent = `Erreur lancement retrain: ${err.message}`;
  }
}

saveTokenBtn.addEventListener("click", () => {
  setToken(tokenInput.value.trim());
  loadCandidates();
});

refreshBtn.addEventListener("click", loadCandidates);
retrainBtn.addEventListener("click", triggerIncrementalRetrain);
refreshRetrainBtn.addEventListener("click", loadRetrainStatus);

filterButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    filterButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentStatus = btn.dataset.status || "";
    loadCandidates();
  });
});

(function init() {
  tokenInput.value = getToken();
  if (getToken()) {
    loadCandidates();
    loadRetrainStatus();
  } else {
    grid.innerHTML = `<div class="empty">Renseigne d'abord l'admin token.</div>`;
    retrainStatus.textContent = "Renseigne d'abord l'admin token.";
  }
})();
