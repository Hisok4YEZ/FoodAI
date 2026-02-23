const SUPABASE_URL = window.__APP_CONFIG__?.SUPABASE_URL || "";
const SUPABASE_ANON_KEY = window.__APP_CONFIG__?.SUPABASE_ANON_KEY || "";
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const API_URL = window.location.origin;

const $ = (id) => document.getElementById(id);
const setModal = (id, show) => $(id)?.classList.toggle("show", show);

let currentUser = null;
let currentProfile = null;
let currentResponse = null;
let currentHistory = [];
let currentFavorites = [];
let selectedDietaryRestrictions = [];
let recipeBase = null;
let recipeBaseServings = 2;

async function parseError(response, fallback = "Une erreur est survenue.") {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) return data.detail[0]?.msg || fallback;
    return fallback;
  } catch {
    const text = await response.text();
    return text?.slice(0, 200) || fallback;
  }
}

async function getAccessToken() {
  const {
    data: { session },
  } = await sb.auth.getSession();
  return session?.access_token || null;
}

async function request(path, { method = "GET", body, headers = {}, auth = true } = {}) {
  const h = { ...headers };
  if (auth) {
    const token = await getAccessToken();
    if (token) h.Authorization = `Bearer ${token}`;
  }
  if (body !== undefined && !(body instanceof FormData) && !h["Content-Type"]) {
    h["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: h,
    body:
      body instanceof FormData
        ? body
        : body !== undefined
          ? JSON.stringify(body)
          : undefined,
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "La requete a echoue."));
  }
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : response.text();
}

function showStatus(message, type = "info") {
  const statusBar = $("statusBar");
  const statusText = $("statusText");
  statusText.textContent = message;
  statusBar.className = `status-bar ${type}`;
  statusBar.classList.remove("hidden");
  if (type === "success") {
    setTimeout(() => statusBar.classList.add("hidden"), 4000);
  }
}

function toggleUserDropdown() {
  $("userDropdown").classList.toggle("show");
}

function closePreferences() {
  setModal("preferencesModal", false);
}

function closeHistory() {
  setModal("historyModal", false);
}

function closeFavorites() {
  setModal("favoritesModal", false);
}

function closeConsentModal() {
  setModal("consentModal", false);
}

function closeAllPanels() {
  closePreferences();
  closeHistory();
  closeFavorites();
  closeConsentModal();
  $("userDropdown").classList.remove("show");
}

async function signInWithGoogle() {
  const { error } = await sb.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: window.location.origin },
  });
  if (error) showStatus(`Je n'ai pas pu lancer Google: ${error.message}`, "error");
}

async function signOut() {
  const { error } = await sb.auth.signOut();
  if (error) showStatus(`Je n'ai pas pu te deconnecter: ${error.message}`, "error");
}

async function handleOAuthCallback() {
  const search = new URLSearchParams(window.location.search);
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const code = search.get("code");
  const accessToken = hash.get("access_token");
  const refreshToken = hash.get("refresh_token");
  if (code) {
    await sb.auth.exchangeCodeForSession(code);
  } else if (accessToken && refreshToken) {
    await sb.auth.setSession({ access_token: accessToken, refresh_token: refreshToken });
  }
}

function updateAuthUI(session) {
  const isLoggedIn = Boolean(session);
  currentUser = isLoggedIn ? session.user : null;
  currentProfile = isLoggedIn ? currentProfile : null;

  $("authOverlay").classList.toggle("hidden", isLoggedIn);
  $("mainApp").style.display = isLoggedIn ? "block" : "none";
  $("userMenu").style.display = isLoggedIn ? "block" : "none";

  if (!isLoggedIn) {
    closeAllPanels();
    return;
  }

  const initials = (
    (currentUser.user_metadata?.first_name || "")[0] ||
    (currentUser.email || "u")[0]
  ).toUpperCase();
  $("userAvatar").textContent = initials;
  $("userName").textContent =
    currentUser.user_metadata?.full_name ||
    currentUser.email?.split("@")[0] ||
    "Utilisateur";

  if (window.location.search || window.location.hash) {
    history.replaceState({}, document.title, window.location.pathname);
  }
}

async function checkAuth() {
  const {
    data: { session },
  } = await sb.auth.getSession();
  updateAuthUI(session);
}

function updateDietaryTagUI() {
  document.querySelectorAll(".dietary-tag").forEach((el) => {
    el.classList.toggle("active", selectedDietaryRestrictions.includes(el.dataset.value));
  });
}

async function fetchUserProfile() {
  const profile = await request("/api/user/profile");
  currentProfile = profile;
  return profile;
}

async function maybeOpenConsentModal() {
  if (!currentUser) return;
  try {
    const profile = currentProfile || (await fetchUserProfile());
    if (!profile.consent_prompt_shown) setModal("consentModal", true);
  } catch (error) {
    console.error("Consentement introuvable:", error);
  }
}

async function openPreferences() {
  $("userDropdown").classList.remove("show");
  setModal("preferencesModal", true);
  await loadPreferences();
}

async function loadPreferences() {
  $("prefEmail").value = currentUser?.email || "";
  try {
    const profile = await fetchUserProfile();
    $("prefFirstName").value = profile.first_name || "";
    $("prefLastName").value = profile.last_name || "";
    $("prefImageConsent").checked = Boolean(profile.image_storage_consent);
    selectedDietaryRestrictions = profile.dietary_restrictions || [];
    updateDietaryTagUI();
  } catch (error) {
    console.error("Chargement preferences:", error);
  }
}

async function savePreferences() {
  const payload = {
    first_name: $("prefFirstName").value || null,
    last_name: $("prefLastName").value || null,
    dietary_restrictions: selectedDietaryRestrictions,
    image_storage_consent: Boolean($("prefImageConsent").checked),
    consent_prompt_shown: true,
  };
  try {
    await request("/api/user/profile", { method: "PATCH", body: payload });
    currentProfile = { ...(currentProfile || {}), ...payload };
    closePreferences();
    checkAuth();
    showStatus("C'est enregistre, tes preferences sont a jour.", "success");
  } catch (error) {
    showStatus(`Impossible d'enregistrer: ${error.message}`, "error");
  }
}

async function submitImageConsent(allowStorage) {
  try {
    const payload = {
      image_storage_consent: Boolean(allowStorage),
      consent_prompt_shown: true,
    };
    await request("/api/user/profile", { method: "PATCH", body: payload });
    currentProfile = { ...(currentProfile || {}), ...payload };
    $("prefImageConsent").checked = Boolean(allowStorage);
    closeConsentModal();
    showStatus(
      allowStorage
        ? "Parfait, je garderai tes images pour ameliorer le modele."
        : "Ok, je ne garde plus tes images.",
      "success",
    );
  } catch (error) {
    showStatus(`Je n'ai pas pu enregistrer ton choix: ${error.message}`, "error");
  }
}

function historyToHtml(item, idx, actionName, deleteFn) {
  const pct = (item.confidence * 100).toFixed(1);
  const when = new Date(item.created_at).toLocaleString("fr-FR");
  return `
    <div class="history-item">
      <div class="history-title">
        <strong>${item.predicted_dish}</strong>
        <span>${pct}%</span>
      </div>
      <div class="history-meta">${when} • ${item.servings} portions</div>
      <div class="history-actions">
        <button class="btn-history" onclick="${actionName}(${idx})">Voir</button>
        <button class="btn-history delete" onclick="${deleteFn}('${item.id}')">Supprimer</button>
      </div>
    </div>
  `;
}

async function openHistory() {
  $("userDropdown").classList.remove("show");
  setModal("historyModal", true);
  await loadHistory();
}

async function loadHistory() {
  const list = $("historyList");
  list.innerHTML = '<div class="history-meta">Chargement...</div>';
  try {
    currentHistory = await request("/api/user/history");
    list.innerHTML =
      currentHistory.length === 0
        ? '<div class="history-meta">Aucun scan enregistre pour le moment.</div>'
        : currentHistory.map((item, idx) => historyToHtml(item, idx, "useHistoryItem", "deleteHistoryItem")).join("");
  } catch (error) {
    list.innerHTML = `<div class="history-meta">Oups: ${error.message}</div>`;
  }
}

function useHistoryItem(index) {
  const item = currentHistory[index];
  if (!item) return;
  currentResponse = {
    predictions: item.top_predictions,
    recipe: null,
    warning: `Scan du ${new Date(item.created_at).toLocaleString("fr-FR")} • Il faut rescanner l'image pour retrouver la recette detaillee.`,
  };
  recipeBase = null;
  recipeBaseServings = parseInt($("servings").value, 10) || 2;
  displayResults(currentResponse);
  closeHistory();
  showStatus(`On a recharge ce scan: ${item.predicted_dish}`, "success");
}

async function deleteHistoryItem(scanId) {
  try {
    await request(`/api/user/history/${scanId}`, { method: "DELETE" });
    await loadHistory();
    showStatus("Scan supprime.", "success");
  } catch (error) {
    showStatus(`Impossible de supprimer: ${error.message}`, "error");
  }
}

async function openFavorites() {
  $("userDropdown").classList.remove("show");
  setModal("favoritesModal", true);
  await loadFavorites();
}

async function loadFavorites() {
  const list = $("favoritesList");
  list.innerHTML = '<div class="history-meta">Chargement...</div>';
  try {
    currentFavorites = await request("/api/user/favorites");
    list.innerHTML =
      currentFavorites.length === 0
        ? '<div class="history-meta">Aucun favori pour le moment.</div>'
        : currentFavorites
            .map((item, idx) => historyToHtml(item, idx, "useFavoriteItem", "deleteFavoriteItem"))
            .join("");
  } catch (error) {
    list.innerHTML = `<div class="history-meta">Oups: ${error.message}</div>`;
  }
}

function useFavoriteItem(index) {
  const item = currentFavorites[index];
  if (!item) return;

  currentResponse = {
    predictions: item.top_predictions?.length
      ? item.top_predictions
      : [{ label: item.predicted_dish, confidence: item.confidence }],
    recipe: item.recipe_payload || null,
    warning: null,
  };
  $("servings").value = item.servings || 2;

  recipeBase = currentResponse.recipe ? JSON.parse(JSON.stringify(currentResponse.recipe)) : null;
  recipeBaseServings = (recipeBase && parseInt(recipeBase.servings, 10)) || parseInt(item.servings, 10) || 2;

  displayResults(currentResponse);
  closeFavorites();
  showStatus(`Favori charge: ${item.predicted_dish}`, "success");
}

async function deleteFavoriteItem(favoriteId) {
  try {
    await request(`/api/user/favorites/${favoriteId}`, { method: "DELETE" });
    await loadFavorites();
    showStatus("Favori supprime.", "success");
  } catch (error) {
    showStatus(`Impossible de supprimer le favori: ${error.message}`, "error");
  }
}

async function saveCurrentAsFavorite() {
  if (!currentResponse?.predictions?.length) {
    showStatus("Fais d'abord un scan avant d'ajouter en favori.", "error");
    return;
  }
  const best = currentResponse.predictions[0];
  const payload = {
    predicted_dish: best.label,
    confidence: best.confidence,
    top_predictions: currentResponse.predictions,
    servings: parseInt($("servings").value, 10) || 2,
    recipe_payload: currentResponse.recipe || null,
  };
  try {
    await request("/api/user/favorites", { method: "POST", body: payload });
    showStatus(`Ajoute aux favoris: ${best.label}`, "success");
  } catch (error) {
    showStatus(`Impossible d'ajouter en favori: ${error.message}`, "error");
  }
}

async function checkBackendHealth() {
  try {
    const data = await request("/health", { auth: false });
    if (data.status === "healthy") {
      showStatus(`Le serveur est pret (${data.num_dishes} plats disponibles).`, "success");
    } else {
      showStatus("Le serveur repond, mais tout n'est pas encore charge.", "error");
    }
  } catch {
    showStatus("Je n'arrive pas a joindre le backend.", "error");
  }
}

async function handleImageUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    $("imagePreview").innerHTML = `<img src="${e.target.result}" alt="Food sample">`;
  };
  reader.readAsDataURL(file);

  await predictImage(file);
}

function displayResults(data) {
  $("topkResults").innerHTML = (data.predictions || [])
    .map((pred, idx) => {
      const percentage = (pred.confidence * 100).toFixed(1);
      return `
        <div class="prediction-item" style="animation-delay: ${idx * 0.1}s">
          <div>
            <div class="prediction-label">${pred.label}</div>
            <div class="confidence-bar">
              <div class="confidence-fill" style="width: ${percentage}%"></div>
            </div>
          </div>
          <div class="prediction-confidence">${percentage}%</div>
        </div>
      `;
    })
    .join("");
  refreshRecipeDisplay();
}

function refreshRecipeDisplay() {
  if (!currentResponse) return;
  const output = $("recipeOutput");
  const minConfidence = parseFloat($("confidence").value);
  const bestPrediction = currentResponse.predictions[0];

  if (currentResponse.warning || bestPrediction.confidence < minConfidence) {
    output.className = "recipe-card";
    output.textContent =
      currentResponse.warning ||
      `Confiance trop basse (${(bestPrediction.confidence * 100).toFixed(1)}% < ${(minConfidence * 100).toFixed(0)}%).\n\nEssaie avec:\n• plat bien centre\n• bonne lumiere\n• fond simple\n• photo nette\n\nJe n'affiche pas la recette pour eviter les erreurs.`;
    return;
  }

  if (!currentResponse.recipe) {
    output.className = "recipe-card";
    output.textContent = "Le plat est reconnu, mais je n'ai pas trouve la recette dans la base.";
    return;
  }

  const requestedServings = Math.max(1, parseInt($("servings").value, 10) || 2);
  const sourceRecipe = recipeBase || currentResponse.recipe;
  const baseServings = Math.max(1, parseInt(recipeBaseServings || sourceRecipe.servings, 10) || 2);
  const ratio = requestedServings / baseServings;

  const formatQuantity = (qty, unit) => {
    if (qty === null || Number.isNaN(qty)) return "";
    let value = qty;
    let u = (unit || "").toLowerCase();
    if (u === "g" && value >= 1000) {
      value /= 1000;
      u = "kg";
    } else if (u === "ml" && value >= 1000) {
      value /= 1000;
      u = "l";
    }
    const rounded =
      Math.abs(value - Math.round(value)) < 1e-9
        ? `${Math.round(value)}`
        : `${value.toFixed(2).replace(/\.?0+$/, "")}`;
    const labels = {
      g: "g",
      kg: "kg",
      ml: "ml",
      l: "l",
      piece: rounded === "1" ? "piece" : "pieces",
      tbsp: "tbsp",
      tsp: "tsp",
    };
    return labels[u] ? `${rounded} ${labels[u]}` : rounded;
  };

  const recipe = {
    ...sourceRecipe,
    servings: requestedServings,
    ingredients: (sourceRecipe.ingredients || []).map((ing) => {
      const hasQty = typeof ing.qty === "number";
      const scaledQty = hasQty ? ing.qty * ratio : null;
      return {
        ...ing,
        qty: scaledQty,
        formatted: hasQty ? formatQuantity(scaledQty, ing.unit) : ing.formatted || "",
      };
    }),
  };

  let recipeText = `╔════════════════════════════════════════╗\n`;
  recipeText += `║  ${recipe.name.toUpperCase()}\n`;
  recipeText += `║  Servings: ${recipe.servings}\n`;
  recipeText += `╚════════════════════════════════════════╝\n\n`;
  recipeText += "📦 INGREDIENTS:\n";
  recipeText += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
  recipe.ingredients.forEach((ing) => {
    recipeText += `  • ${ing.formatted} ${ing.display}\n`;
  });
  recipeText += "\n🔬 PROCEDURE:\n";
  recipeText += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
  recipe.steps.forEach((step, index) => {
    recipeText += `  ${index + 1}. ${step}\n`;
  });

  output.className = "recipe-card";
  output.textContent = recipeText;
}

async function predictImage(file) {
  $("loadingOverlay").classList.add("active");
  $("btnUpload").disabled = true;

  try {
    const formData = new FormData();
    formData.append("file", file);

    const servings = parseInt($("servings").value, 10);
    const minConfidence = parseFloat($("confidence").value);
    const data = await request(
      `/api/predict?servings=${servings}&min_confidence=${minConfidence}`,
      { method: "POST", body: formData, headers: {}, auth: true },
    );

    currentResponse = data;
    recipeBase = data.recipe ? JSON.parse(JSON.stringify(data.recipe)) : null;
    recipeBaseServings = (recipeBase && parseInt(recipeBase.servings, 10)) || servings || 2;

    displayResults(data);
    showStatus("Top, analyse terminee.", "success");
    document.querySelector(".predictions-card")?.classList.add("success-flash");
    setTimeout(() => document.querySelector(".predictions-card")?.classList.remove("success-flash"), 600);
  } catch (error) {
    console.error("Prediction error:", error);
    showStatus(`Je n'ai pas pu analyser l'image: ${error.message}`, "error");
    $("recipeOutput").className = "recipe-card";
    $("recipeOutput").textContent = `Analyse impossible:\n${error.message}\n\nVerifie que le backend tourne bien.`;
  } finally {
    $("loadingOverlay").classList.remove("active");
    $("btnUpload").disabled = false;
  }
}

function onGlobalClick(event) {
  if (!event.target.closest(".user-menu")) $("userDropdown").classList.remove("show");
  if (event.target.classList.contains("dietary-tag")) {
    const value = event.target.dataset.value;
    selectedDietaryRestrictions = selectedDietaryRestrictions.includes(value)
      ? selectedDietaryRestrictions.filter((item) => item !== value)
      : [...selectedDietaryRestrictions, value];
    updateDietaryTagUI();
  }
  if (event.target.id === "preferencesModal") closePreferences();
  if (event.target.id === "historyModal") closeHistory();
  if (event.target.id === "favoritesModal") closeFavorites();
}

function onKeyDown(event) {
  if (event.key === "Escape") closeAllPanels();
}

window.addEventListener("load", () => {
  document.addEventListener("click", onGlobalClick);
  document.addEventListener("keydown", onKeyDown);

  handleOAuthCallback()
    .then(checkAuth)
    .then(async () => {
      if (!currentUser) return;
      try {
        await fetchUserProfile();
        await maybeOpenConsentModal();
      } catch {
        // Pas bloquant pour l'UI.
      }
      await checkBackendHealth();
    });

  sb.auth.onAuthStateChange(async (_event, session) => {
    updateAuthUI(session);
    if (!session) return;
    try {
      await fetchUserProfile();
      await maybeOpenConsentModal();
    } catch {
      // Pas bloquant pour l'UI.
    }
    await checkBackendHealth();
  });
});
