
// window.API_BASE_URL est injecté dans config.js au démarrage du conteneur
// (voir docker-entrypoint.sh) : l'URL de l'API n'est jamais figée dans le build.

const API_URL = `${window.API_BASE_URL}/tasks`;

const form = document.getElementById("task-form");
const idField = document.getElementById("task-id");
const titleField = document.getElementById("title");
const descField = document.getElementById("description");
const submitBtn = document.getElementById("submit-btn");
const cancelBtn = document.getElementById("cancel-btn");
const list = document.getElementById("task-list");
const statusEl = document.getElementById("status");


// ============================================================
// Gestion du statut
// ============================================================

function setStatus(message, kind) {
    statusEl.textContent = message;
    statusEl.className = "status" + (kind ? " " + kind : "");
}


// ============================================================
// GET /tasks
// ============================================================

async function loadTasks() {

    try {

        const res = await fetch(API_URL);

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();

        const tasks = Array.isArray(data.tasks)
            ? data.tasks
            : [];

        const pod = data.pod || "inconnu";

        renderTasks(tasks, pod);

        setStatus(
            `${tasks.length} tâche(s) — répondu par le pod ${pod}`,
            "ok"
        );

    } catch (err) {

        setStatus(
            `Impossible de contacter l'API (${err.message})`,
            "error"
        );
    }
}


// ============================================================
// Affichage des tâches
// ============================================================

function renderTasks(tasks, pod) {

    list.innerHTML = "";

    if (tasks.length === 0) {

        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td colspan="5">
                Aucune tâche pour le moment.
            </td>
        `;

        list.appendChild(tr);

        return;
    }


    for (const t of tasks) {

        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>
                ${t.id}
            </td>

            <td>
                ${escapeHtml(t.title)}
            </td>

            <td>
                ${escapeHtml(t.description || "")}
            </td>

            <td>
                ${escapeHtml(pod || "—")}
            </td>

            <td class="actions">

                <button
                    class="edit"
                    data-id="${t.id}"
                >
                    Modifier
                </button>

                <button
                    class="delete"
                    data-id="${t.id}"
                >
                    Supprimer
                </button>

            </td>
        `;

        list.appendChild(tr);
    }
}


// ============================================================
// Protection contre l'injection HTML
// ============================================================

function escapeHtml(str) {

    const div = document.createElement("div");

    div.textContent = String(str);

    return div.innerHTML;
}


// ============================================================
// POST /tasks
// PUT /tasks/<id>
// ============================================================

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    const id = idField.value;

    const payload = {
        title: titleField.value,
        description: descField.value
    };


    try {

        const res = await fetch(
            id ? `${API_URL}/${id}` : API_URL,
            {
                method: id ? "PUT" : "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(payload)
            }
        );


        if (!res.ok) {

            const err = await res
                .json()
                .catch(() => ({}));

            throw new Error(
                err.error || `HTTP ${res.status}`
            );
        }


        resetForm();

        await loadTasks();


    } catch (err) {

        setStatus(
            `Erreur : ${err.message}`,
            "error"
        );
    }
});


// ============================================================
// Boutons Modifier / Supprimer
// ============================================================

list.addEventListener("click", async (e) => {

    const id = e.target.dataset.id;

    if (!id) {
        return;
    }


    // --------------------------------------------------------
    // DELETE /tasks/<id>
    // --------------------------------------------------------

    if (e.target.classList.contains("delete")) {

        if (!confirm(`Supprimer la tâche #${id} ?`)) {
            return;
        }


        try {

            const res = await fetch(
                `${API_URL}/${id}`,
                {
                    method: "DELETE"
                }
            );


            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }


            await loadTasks();


        } catch (err) {

            setStatus(
                `Erreur : ${err.message}`,
                "error"
            );
        }
    }


    // --------------------------------------------------------
    // GET /tasks/<id>
    // --------------------------------------------------------

    if (e.target.classList.contains("edit")) {

        try {

            const res = await fetch(
                `${API_URL}/${id}`
            );


            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }


            const data = await res.json();


            idField.value = data.task.id;

            titleField.value = data.task.title;

            descField.value =
                data.task.description || "";


            submitBtn.textContent = "Enregistrer";

            cancelBtn.classList.remove("hidden");


            titleField.focus();


        } catch (err) {

            setStatus(
                `Erreur : ${err.message}`,
                "error"
            );
        }
    }

});


// ============================================================
// Annuler la modification
// ============================================================

cancelBtn.addEventListener(
    "click",
    resetForm
);


function resetForm() {

    idField.value = "";

    titleField.value = "";

    descField.value = "";

    submitBtn.textContent = "Ajouter";

    cancelBtn.classList.add("hidden");
}


// ============================================================
// Chargement initial
// ============================================================

loadTasks();


// ============================================================
// Actualisation automatique
// ============================================================

setInterval(
    loadTasks,
    15000
);

