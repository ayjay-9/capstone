function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        for (let cookie of document.cookie.split(";")) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function ExperimentName({ experimentId, initialName }) {
    const [name, setName] = React.useState(initialName);
    const [draft, setDraft] = React.useState(initialName);
    const [editing, setEditing] = React.useState(false);
    const [saving, setSaving] = React.useState(false);
    const [error, setError] = React.useState(null);

    const startEditing = () => {
        setDraft(name);
        setError(null);
        setEditing(true);
    };

    const cancelEditing = () => {
        setEditing(false);
        setError(null);
    };

    const saveName = () => {
        const trimmed = draft.trim();
        if (!trimmed) {
            setError("Name cannot be empty.");
            return;
        }
        setSaving(true);
        setError(null);
        fetch(`/experiment/${experimentId}/rename/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ name: trimmed }),
        })
            .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) {
                    throw new Error(data.error || "Could not rename experiment.");
                }
                setName(data.name);
                setEditing(false);
            })
            .catch((err) => setError(err.message))
            .finally(() => setSaving(false));
    };

    if (!editing) {
        return (
            <span>
                <strong>{name}</strong>{" "}
                <button type="button" className="rename-link" onClick={startEditing}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil" viewBox="0 0 16 16">
                        <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325"/>
                    </svg>
                </button>
            </span>
        );
    }

    return (
        <span className="rename-editor">
            <input
                type="text"
                value={draft}
                maxLength={100}
                disabled={saving}
                onChange={(event) => setDraft(event.target.value)}
                autoFocus
            />
            <button type="button" onClick={saveName} disabled={saving}>
                Save
            </button>
            <button type="button" onClick={cancelEditing} disabled={saving}>
                Cancel
            </button>
            {error && <span className="rename-error">{error}</span>}
        </span>
    );
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".experiment-name-root").forEach((el) => {
        const { experimentId, experimentName } = el.dataset;
        ReactDOM.createRoot(el).render(
            <ExperimentName experimentId={experimentId} initialName={experimentName} />
        );
    });
});
