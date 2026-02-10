const SUPABASE_URL = window.__APP_CONFIG__?.SUPABASE_URL || "";
const SUPABASE_ANON_KEY = window.__APP_CONFIG__?.SUPABASE_ANON_KEY || "";
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

      const API_URL = window.location.origin;
      let currentUser = null;
      let currentResponse = null;
      let selectedDietaryRestrictions = [];
      let currentHistory = [];
      let currentFavorites = [];
      let currentProfile = null;

      async function signInWithGoogle() {
        const { error } = await sb.auth.signInWithOAuth({
          provider: "google",
          options: { redirectTo: window.location.origin },
        });
        if (error) {
          showStatus(`❌ Auth Google: ${error.message}`, "error");
        }
      }

      async function signOut() {
        const { error } = await sb.auth.signOut();
        if (error) {
          showStatus(`❌ Deconnexion: ${error.message}`, "error");
        }
      }

      async function handleOAuthCallback() {
        const search = new URLSearchParams(window.location.search);
        const code = search.get("code");
        const hash = new URLSearchParams(
          window.location.hash.startsWith("#")
            ? window.location.hash.slice(1)
            : window.location.hash,
        );
        const accessToken = hash.get("access_token");
        const refreshToken = hash.get("refresh_token");

        if (code) {
          await sb.auth.exchangeCodeForSession(code);
        } else if (accessToken && refreshToken) {
          await sb.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          });
        }
      }

      function updateAuthUI(session) {
        const overlay = document.getElementById("authOverlay");
        const app = document.getElementById("mainApp");
        const userMenu = document.getElementById("userMenu");
        if (session) {
          currentUser = session.user;
          overlay.classList.add("hidden");
          app.style.display = "block";
          userMenu.style.display = "block";
          const initials = (
            (currentUser.user_metadata?.first_name || "")[0] ||
            (currentUser.email || "u")[0]
          ).toUpperCase();
          document.getElementById("userAvatar").textContent = initials;
          document.getElementById("userName").textContent =
            currentUser.user_metadata?.full_name ||
            currentUser.email?.split("@")[0] ||
            "Utilisateur";
          if (window.location.search || window.location.hash) {
            history.replaceState({}, document.title, window.location.pathname);
          }
          return;
        }
        currentUser = null;
        currentProfile = null;
        overlay.classList.remove("hidden");
        app.style.display = "none";
        userMenu.style.display = "none";
        closePreferences();
        closeHistory();
        closeFavorites();
        closeConsentModal();
      }

      async function checkAuth() {
        const {
          data: { session },
        } = await sb.auth.getSession();
        updateAuthUI(session);
      }

      async function getAccessToken() {
        const {
          data: { session },
        } = await sb.auth.getSession();
        return session?.access_token || null;
      }

      async function buildAuthHeaders(extra = {}) {
        const token = await getAccessToken();
        return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
      }

      function toggleUserDropdown() {
        document.getElementById("userDropdown").classList.toggle("show");
      }

      async function openPreferences() {
        document.getElementById("userDropdown").classList.remove("show");
        document.getElementById("preferencesModal").classList.add("show");
        await loadPreferences();
      }

      function closePreferences() {
        document.getElementById("preferencesModal").classList.remove("show");
      }

      async function openHistory() {
        document.getElementById("userDropdown").classList.remove("show");
        document.getElementById("historyModal").classList.add("show");
        await loadHistory();
      }

      function closeHistory() {
        document.getElementById("historyModal").classList.remove("show");
      }

      async function openFavorites() {
        document.getElementById("userDropdown").classList.remove("show");
        document.getElementById("favoritesModal").classList.add("show");
        await loadFavorites();
      }

      function closeFavorites() {
        document.getElementById("favoritesModal").classList.remove("show");
      }

      function closeConsentModal() {
        document.getElementById("consentModal").classList.remove("show");
      }

      function updateDietaryTagUI() {
        document.querySelectorAll(".dietary-tag").forEach((el) => {
          el.classList.toggle(
            "active",
            selectedDietaryRestrictions.includes(el.dataset.value),
          );
        });
      }

      async function fetchUserProfile() {
        const response = await fetch(`${API_URL}/api/user/profile`, {
          headers: await buildAuthHeaders(),
        });
        if (!response.ok) {
          throw new Error("Impossible de charger le profil");
        }
        const profile = await response.json();
        currentProfile = profile;
        return profile;
      }

      async function maybeOpenConsentModal() {
        if (!currentUser) return;
        try {
          const profile = currentProfile || (await fetchUserProfile());
          if (!profile.consent_prompt_shown) {
            document.getElementById("consentModal").classList.add("show");
          }
        } catch (error) {
          console.error("Erreur chargement consentement:", error);
        }
      }

      async function loadPreferences() {
        const firstName = document.getElementById("prefFirstName");
        const lastName = document.getElementById("prefLastName");
        const email = document.getElementById("prefEmail");
        const imageConsent = document.getElementById("prefImageConsent");
        email.value = currentUser?.email || "";

        try {
          const profile = await fetchUserProfile();
          firstName.value = profile.first_name || "";
          lastName.value = profile.last_name || "";
          selectedDietaryRestrictions = profile.dietary_restrictions || [];
          imageConsent.checked = Boolean(profile.image_storage_consent);
          updateDietaryTagUI();
        } catch (error) {
          console.error("Erreur chargement preferences:", error);
        }
      }

      async function savePreferences() {
        const payload = {
          first_name: document.getElementById("prefFirstName").value || null,
          last_name: document.getElementById("prefLastName").value || null,
          dietary_restrictions: selectedDietaryRestrictions,
          image_storage_consent: Boolean(
            document.getElementById("prefImageConsent").checked,
          ),
          consent_prompt_shown: true,
        };
        try {
          const response = await fetch(`${API_URL}/api/user/profile`, {
            method: "PATCH",
            headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify(payload),
          });
          if (!response.ok) {
            const text = await response.text();
            throw new Error(text || "Erreur sauvegarde");
          }
          showStatus("✅ Preferences enregistrees", "success");
          closePreferences();
          currentProfile = { ...(currentProfile || {}), ...payload };
          checkAuth();
        } catch (error) {
          showStatus(`❌ ${error.message}`, "error");
        }
      }

      async function submitImageConsent(allowStorage) {
        try {
          const response = await fetch(`${API_URL}/api/user/profile`, {
            method: "PATCH",
            headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({
              image_storage_consent: Boolean(allowStorage),
              consent_prompt_shown: true,
            }),
          });
          if (!response.ok) {
            const text = await response.text();
            throw new Error(text || "Erreur sauvegarde consentement");
          }
          currentProfile = {
            ...(currentProfile || {}),
            image_storage_consent: Boolean(allowStorage),
            consent_prompt_shown: true,
          };
          const checkbox = document.getElementById("prefImageConsent");
          if (checkbox) checkbox.checked = Boolean(allowStorage);
          closeConsentModal();
          showStatus(
            allowStorage
              ? "✅ Stockage des images active"
              : "✅ Stockage des images desactive",
            "success",
          );
        } catch (error) {
          showStatus(`❌ ${error.message}`, "error");
        }
      }

      async function loadHistory() {
        const list = document.getElementById("historyList");
        list.innerHTML = '<div class="history-meta">Chargement...</div>';
        try {
          const response = await fetch(`${API_URL}/api/user/history`, {
            headers: await buildAuthHeaders(),
          });
          if (!response.ok) {
            throw new Error("Impossible de charger l'historique");
          }
          currentHistory = await response.json();
          if (currentHistory.length === 0) {
            list.innerHTML =
              '<div class="history-meta">Aucun scan enregistre pour le moment.</div>';
            return;
          }

          list.innerHTML = currentHistory
            .map((item, idx) => {
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
                    <button class="btn-history" onclick="useHistoryItem(${idx})">Voir</button>
                    <button class="btn-history delete" onclick="deleteHistoryItem('${item.id}')">Supprimer</button>
                  </div>
                </div>
              `;
            })
            .join("");
        } catch (error) {
          list.innerHTML = `<div class="history-meta">Erreur: ${error.message}</div>`;
        }
      }

      function useHistoryItem(index) {
        const item = currentHistory[index];
        if (!item) return;

        currentResponse = {
          predictions: item.top_predictions,
          recipe: null,
          warning: `Scan du ${new Date(item.created_at).toLocaleString("fr-FR")} • Recette detaillee indisponible sans re-scan image.`,
        };
        displayResults(currentResponse);
        closeHistory();
        showStatus(
          `📜 Historique charge: ${item.predicted_dish} (${(item.confidence * 100).toFixed(1)}%)`,
          "success",
        );
      }

      async function deleteHistoryItem(scanId) {
        try {
          const response = await fetch(`${API_URL}/api/user/history/${scanId}`, {
            method: "DELETE",
            headers: await buildAuthHeaders(),
          });
          if (!response.ok) {
            throw new Error("Suppression impossible");
          }
          showStatus("🗑️ Scan supprime", "success");
          await loadHistory();
        } catch (error) {
          showStatus(`❌ ${error.message}`, "error");
        }
      }

      async function loadFavorites() {
        const list = document.getElementById("favoritesList");
        list.innerHTML = '<div class="history-meta">Chargement...</div>';
        try {
          const response = await fetch(`${API_URL}/api/user/favorites`, {
            headers: await buildAuthHeaders(),
          });
          if (!response.ok) {
            throw new Error("Impossible de charger les favoris");
          }
          currentFavorites = await response.json();
          if (currentFavorites.length === 0) {
            list.innerHTML =
              '<div class="history-meta">Aucun favori pour le moment.</div>';
            return;
          }

          list.innerHTML = currentFavorites
            .map((item, idx) => {
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
                    <button class="btn-history" onclick="useFavoriteItem(${idx})">Voir</button>
                    <button class="btn-history delete" onclick="deleteFavoriteItem('${item.id}')">Supprimer</button>
                  </div>
                </div>
              `;
            })
            .join("");
        } catch (error) {
          list.innerHTML = `<div class="history-meta">Erreur: ${error.message}</div>`;
        }
      }

      function useFavoriteItem(index) {
        const item = currentFavorites[index];
        if (!item) return;

        currentResponse = {
          predictions: item.top_predictions || [],
          recipe: item.recipe_payload || null,
          warning: null,
        };
        if (!currentResponse.predictions.length) {
          currentResponse.predictions = [
            { label: item.predicted_dish, confidence: item.confidence },
          ];
        }
        document.getElementById("servings").value = item.servings || 2;
        displayResults(currentResponse);
        closeFavorites();
        showStatus(`⭐ Favori charge: ${item.predicted_dish}`, "success");
      }

      async function deleteFavoriteItem(favoriteId) {
        try {
          const response = await fetch(
            `${API_URL}/api/user/favorites/${favoriteId}`,
            {
              method: "DELETE",
              headers: await buildAuthHeaders(),
            },
          );
          if (!response.ok) {
            throw new Error("Suppression du favori impossible");
          }
          showStatus("🗑️ Favori supprime", "success");
          await loadFavorites();
        } catch (error) {
          showStatus(`❌ ${error.message}`, "error");
        }
      }

      async function saveCurrentAsFavorite() {
        if (!currentResponse || !currentResponse.predictions?.length) {
          showStatus("⚠️ Aucun resultat a ajouter en favori", "error");
          return;
        }

        const best = currentResponse.predictions[0];
        const payload = {
          predicted_dish: best.label,
          confidence: best.confidence,
          top_predictions: currentResponse.predictions,
          servings: parseInt(document.getElementById("servings").value) || 2,
          recipe_payload: currentResponse.recipe || null,
        };

        try {
          const response = await fetch(`${API_URL}/api/user/favorites`, {
            method: "POST",
            headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify(payload),
          });
          if (!response.ok) {
            const text = await response.text();
            throw new Error(text || "Impossible d'ajouter aux favoris");
          }
          showStatus(`⭐ Favori ajoute: ${best.label}`, "success");
        } catch (error) {
          showStatus(`❌ ${error.message}`, "error");
        }
      }

      async function checkBackendHealth() {
        try {
          const response = await fetch(`${API_URL}/health`);
          const data = await response.json();
          if (data.status === "healthy") {
            showStatus(
              `✅ System online • ${data.num_dishes} dishes in database`,
              "success",
            );
          } else {
            showStatus(
              "⚠️ System partially online • Model not loaded",
              "error",
            );
          }
        } catch (error) {
          showStatus("❌ Connection failed • Backend offline", "error");
        }
      }

      function showStatus(message, type = "info") {
        const statusBar = document.getElementById("statusBar");
        const statusText = document.getElementById("statusText");
        statusText.textContent = message;
        statusBar.className = `status-bar ${type}`;
        statusBar.classList.remove("hidden");

        if (type === "success") {
          setTimeout(() => {
            statusBar.classList.add("hidden");
          }, 4000);
        }
      }

      async function handleImageUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function (e) {
          const preview = document.getElementById("imagePreview");
          preview.innerHTML = `<img src="${e.target.result}" alt="Food sample">`;
        };
        reader.readAsDataURL(file);

        await predictImage(file);
      }

      async function predictImage(file) {
        const loadingOverlay = document.getElementById("loadingOverlay");
        const btnUpload = document.getElementById("btnUpload");

        try {
          loadingOverlay.classList.add("active");
          btnUpload.disabled = true;

          const formData = new FormData();
          formData.append("file", file);
          const servings = parseInt(document.getElementById("servings").value);
          const minConfidence = parseFloat(
            document.getElementById("confidence").value,
          );

          const response = await fetch(
            `${API_URL}/api/predict?servings=${servings}&min_confidence=${minConfidence}`,
            {
              method: "POST",
              headers: await buildAuthHeaders(),
              body: formData,
            },
          );

          if (!response.ok) {
            let errorMsg = "Analysis failed";
            try {
              const error = await response.json();
              errorMsg = error.detail || errorMsg;
            } catch {
              const text = await response.text();
              errorMsg = text.substring(0, 200);
            }
            throw new Error(errorMsg);
          }

          const data = await response.json();
          currentResponse = data;

          displayResults(data);
          showStatus("✅ Analysis complete", "success");

          // Success animation
          document
            .querySelector(".predictions-card")
            .classList.add("success-flash");
          setTimeout(() => {
            document
              .querySelector(".predictions-card")
              .classList.remove("success-flash");
          }, 600);
        } catch (error) {
          console.error("Error:", error);
          showStatus(`❌ Error: ${error.message}`, "error");

          const output = document.getElementById("recipeOutput");
          output.className = "recipe-card";
          output.textContent = `⚠️ Analysis error:\n${error.message}\n\nPlease check that the backend is running.`;
        } finally {
          loadingOverlay.classList.remove("active");
          btnUpload.disabled = false;
        }
      }

      function displayResults(data) {
        const topkResults = document.getElementById("topkResults");

        let html = "";
        data.predictions.forEach((pred, idx) => {
          const percentage = (pred.confidence * 100).toFixed(1);
          html += `
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
        });

        topkResults.innerHTML = html;
        refreshRecipeDisplay();
      }

      function refreshRecipeDisplay() {
        if (!currentResponse) return;

        const output = document.getElementById("recipeOutput");
        const minConfidence = parseFloat(
          document.getElementById("confidence").value,
        );
        const bestPrediction = currentResponse.predictions[0];

        if (
          currentResponse.warning ||
          bestPrediction.confidence < minConfidence
        ) {
          output.className = "recipe-card";
          output.textContent =
            currentResponse.warning ||
            `⚠️ Low confidence (${(bestPrediction.confidence * 100).toFixed(1)}% < ${(minConfidence * 100).toFixed(0)}%)\n\nSuggestions:\n• Center the dish in frame\n• Use good lighting\n• Simple background\n• Avoid zooming too much\n\nNo recipe data displayed.`;
          return;
        }

        if (!currentResponse.recipe) {
          output.className = "recipe-card";
          output.textContent =
            "⚠️ Dish predicted but not found in database.\nCheck that class ID matches recipes.json.";
          return;
        }

        const recipe = currentResponse.recipe;
        const requestedServings = Math.max(
          1,
          parseInt(document.getElementById("servings").value) || recipe.servings || 1,
        );
        const baseServings = Number(recipe.servings) > 0 ? Number(recipe.servings) : 1;
        const scaleFactor = requestedServings / baseServings;

        function formatScaledQuantity(value, unit) {
          const numericValue = Number(value);
          if (!Number.isFinite(numericValue)) return "";
          const scaled = numericValue * scaleFactor;
          const rounded =
            scaled >= 10
              ? scaled.toFixed(1)
              : scaled >= 1
                ? scaled.toFixed(2)
                : scaled.toFixed(3);
          const clean = Number(rounded).toString();
          return unit ? `${clean} ${unit}` : clean;
        }

        let recipeText = `╔════════════════════════════════════════╗\n`;
        recipeText += `║  ${recipe.name.toUpperCase()}\n`;
        recipeText += `║  Servings: ${requestedServings}\n`;
        recipeText += `╚════════════════════════════════════════╝\n\n`;

        recipeText += "📦 INGREDIENTS:\n";
        recipeText += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
        recipe.ingredients.forEach((ing) => {
          const formattedQty = formatScaledQuantity(ing.qty, ing.unit);
          const qtyText = formattedQty || ing.formatted || "";
          recipeText += `  • ${qtyText} ${ing.display}\n`;
        });

        recipeText += "\n🔬 PROCEDURE:\n";
        recipeText += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
        recipe.steps.forEach((step, index) => {
          recipeText += `  ${index + 1}. ${step}\n`;
        });

        output.className = "recipe-card";
        output.textContent = recipeText;
      }

      window.addEventListener("load", () => {
        document.addEventListener("click", (event) => {
          if (!event.target.closest(".user-menu")) {
            document.getElementById("userDropdown").classList.remove("show");
          }
          if (event.target.classList.contains("dietary-tag")) {
            const value = event.target.dataset.value;
            if (selectedDietaryRestrictions.includes(value)) {
              selectedDietaryRestrictions = selectedDietaryRestrictions.filter(
                (item) => item !== value,
              );
            } else {
              selectedDietaryRestrictions.push(value);
            }
            updateDietaryTagUI();
          }
          if (event.target.id === "preferencesModal") {
            closePreferences();
          }
          if (event.target.id === "historyModal") {
            closeHistory();
          }
          if (event.target.id === "favoritesModal") {
            closeFavorites();
          }
        });

        document.addEventListener("keydown", (event) => {
          if (event.key === "Escape") {
            closePreferences();
            closeHistory();
            closeFavorites();
            document.getElementById("userDropdown").classList.remove("show");
          }
        });

        handleOAuthCallback().finally(() => {
          checkAuth().finally(() => {
            if (currentUser) {
              fetchUserProfile()
                .then(() => maybeOpenConsentModal())
                .catch(() => {});
              checkBackendHealth();
            }
          });
        });

        sb.auth.onAuthStateChange((_event, session) => {
          updateAuthUI(session);
          if (session) {
            fetchUserProfile()
              .then(() => maybeOpenConsentModal())
              .catch(() => {});
            checkBackendHealth();
          }
        });
      });
