document.addEventListener("DOMContentLoaded", () => {
  // Mobile navigation toggle
  const navToggle = document.getElementById("navToggle");
  const navMenu = document.getElementById("navMenu");
  if (navToggle && navMenu) {
    navToggle.addEventListener("click", () => {
      navMenu.classList.toggle("open");
    });
  }

  // Dismissible flash alerts
  document.querySelectorAll(".flash-close").forEach((btn) => {
    btn.addEventListener("click", () => {
      const alert = btn.closest(".flash");
      if (alert) alert.remove();
    });
  });

  // Dynamic tracklist editor on album create/edit form
  const trackList = document.getElementById("trackEditorList");
  const addTrackBtn = document.getElementById("addTrackBtn");

  function renumberTracks() {
    if (!trackList) return;
    trackList.querySelectorAll(".track-editor-row").forEach((row, index) => {
      const idxEl = row.querySelector(".track-editor-index");
      if (idxEl) idxEl.textContent = String(index + 1).padStart(2, "0");
    });
  }

  function createTrackRow(title = "", duration = "", featuring = "") {
    const row = document.createElement("div");
    row.className = "track-editor-row";
    row.innerHTML = `
      <span class="track-editor-index">01</span>
      <input type="text" name="track_title[]" class="form-control" placeholder="Назва треку" value="${title.replace(/"/g, "&quot;")}">
      <input type="text" name="track_duration[]" class="form-control mono" placeholder="3:20" value="${duration.replace(/"/g, "&quot;")}">
      <input type="text" name="track_featuring[]" class="form-control" placeholder="feat. (необов'язково)" value="${featuring.replace(/"/g, "&quot;")}">
      <button type="button" class="btn-icon-remove" title="Видалити трек" aria-label="Видалити трек">&times;</button>
    `;
    return row;
  }

  if (trackList && addTrackBtn) {
    addTrackBtn.addEventListener("click", () => {
      const row = createTrackRow();
      trackList.appendChild(row);
      renumberTracks();
      const input = row.querySelector('input[name="track_title[]"]');
      if (input) input.focus();
    });

    trackList.addEventListener("click", (event) => {
      const removeBtn = event.target.closest(".btn-icon-remove");
      if (!removeBtn) return;
      const rows = trackList.querySelectorAll(".track-editor-row");
      if (rows.length <= 1) {
        rows[0].querySelectorAll("input").forEach((inp) => (inp.value = ""));
        return;
      }
      removeBtn.closest(".track-editor-row").remove();
      renumberTracks();
    });

    renumberTracks();
  }

  // Delete album confirmation
  document.querySelectorAll("[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const message = form.getAttribute("data-confirm");
      if (message && !window.confirm(message)) {
        event.preventDefault();
      }
    });
  });
});

