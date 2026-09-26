/**
 * ============================================================================
 * CRM - Client-side Interactive Script (script.js)
 * ============================================================================
 * Handles:
 * 1. Mobile sidebar toggle
 * 2. Universal modal opening/closing (Add, Edit, Delete Confirm)
 * 3. Dynamic Edit Modal data population from HTML data-* attributes
 * 4. Dynamic Delete Confirmation modal with target name
 * 5. Instant client-side table search & quick filtering
 * 6. Alert dismissals
 * 7. Chart.js rendering on Reports page (with graceful pure-SVG fallback)
 * ============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  initSidebar();
  initModals();
  initAlerts();
  initDynamicModals();
  initClientTableSearch();
});

// ---------------------------------------------------------------------------
// 1. MOBILE SIDEBAR TOGGLE
// ---------------------------------------------------------------------------
function initSidebar() {
  const toggleBtn = document.getElementById("mobileSidebarToggle");
  const sidebar = document.getElementById("appSidebar");

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });

    // Close when clicking outside on mobile
    document.addEventListener("click", (e) => {
      if (
        window.innerWidth <= 768 &&
        sidebar.classList.contains("open") &&
        !sidebar.contains(e.target) &&
        !toggleBtn.contains(e.target)
      ) {
        sidebar.classList.remove("open");
      }
    });
  }
}

// ---------------------------------------------------------------------------
// 2. MODAL CONTROLS (Open, Close, Backdrop Click, Esc Key)
// ---------------------------------------------------------------------------
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("active");
    document.body.style.overflow = "hidden"; // Prevent scrolling
    // Autofocus first input inside modal
    const firstInput = modal.querySelector("input:not([type=hidden]), select, textarea");
    if (firstInput) firstInput.focus();
  }
}

function closeModal(modalOrId) {
  const modal = typeof modalOrId === "string" ? document.getElementById(modalOrId) : modalOrId;
  if (modal) {
    modal.classList.remove("active");
    document.body.style.overflow = "";
  }
}

function initModals() {
  // Click on backdrop to close
  document.querySelectorAll(".modal-overlay").forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        closeModal(overlay);
      }
    });
  });

  // Buttons with data-modal-close
  document.querySelectorAll("[data-modal-close]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = btn.closest(".modal-overlay");
      if (modal) closeModal(modal);
    });
  });

  // Buttons with data-modal-open
  document.querySelectorAll("[data-modal-open]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const modalId = btn.getAttribute("data-modal-open");
      openModal(modalId);
    });
  });

  // Escape key closes open modal
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const activeModal = document.querySelector(".modal-overlay.active");
      if (activeModal) closeModal(activeModal);
    }
  });
}

// ---------------------------------------------------------------------------
// 3. DYNAMIC EDIT & DELETE MODALS
// ---------------------------------------------------------------------------
function initDynamicModals() {
  // A. Edit Customer Modal Population
  document.querySelectorAll(".btn-edit-customer").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const name = btn.getAttribute("data-name");
      const email = btn.getAttribute("data-email");
      const phone = btn.getAttribute("data-phone");
      const company = btn.getAttribute("data-company");
      const address = btn.getAttribute("data-address");
      const status = btn.getAttribute("data-status");
      const notes = btn.getAttribute("data-notes");

      const form = document.getElementById("editCustomerForm");
      if (form) {
        form.action = `/customers/edit/${id}`;
        document.getElementById("edit_customer_name").value = name || "";
        document.getElementById("edit_customer_email").value = email || "";
        document.getElementById("edit_customer_phone").value = phone || "";
        document.getElementById("edit_customer_company").value = company || "";
        document.getElementById("edit_customer_address").value = address || "";
        document.getElementById("edit_customer_status").value = status || "Active";
        document.getElementById("edit_customer_notes").value = notes || "";
        openModal("editCustomerModal");
      }
    });
  });

  // B. Edit Follow-up Modal Population
  document.querySelectorAll(".btn-edit-followup").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const reason = btn.getAttribute("data-reason");
      const date = btn.getAttribute("data-date");
      const priority = btn.getAttribute("data-priority");
      const status = btn.getAttribute("data-status");

      const form = document.getElementById("editFollowupForm");
      if (form) {
        form.action = `/followups/edit/${id}`;
        document.getElementById("edit_followup_reason").value = reason || "";
        document.getElementById("edit_followup_date").value = date || "";
        document.getElementById("edit_followup_priority").value = priority || "Medium";
        document.getElementById("edit_followup_status").value = status || "Pending";
        openModal("editFollowupModal");
      }
    });
  });

  // C. Universal Delete Confirmation Modal
  document.querySelectorAll(".btn-confirm-delete").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const actionUrl = btn.getAttribute("data-action");
      const title = btn.getAttribute("data-title") || "this record";

      const deleteForm = document.getElementById("universalDeleteForm");
      const deleteText = document.getElementById("deleteConfirmItemText");

      if (deleteForm) {
        deleteForm.action = actionUrl;
        if (deleteText) {
          deleteText.textContent = `Are you sure you want to delete ${title}? This action cannot be undone.`;
        }
        openModal("deleteConfirmModal");
      }
    });
  });
}

// ---------------------------------------------------------------------------
// 4. INSTANT CLIENT-SIDE SEARCH
// ---------------------------------------------------------------------------
function initClientTableSearch() {
  const searchInput = document.getElementById("clientTableSearch");
  const targetTable = document.querySelector(".data-table tbody");

  if (searchInput && targetTable) {
    searchInput.addEventListener("input", () => {
      const query = searchInput.value.toLowerCase().trim();
      const rows = targetTable.querySelectorAll("tr");

      let visibleCount = 0;
      rows.forEach((row) => {
        // Skip empty state row if present
        if (row.classList.contains("no-records-row")) return;

        const text = row.textContent.toLowerCase();
        if (text.includes(query)) {
          row.style.display = "";
          visibleCount++;
        } else {
          row.style.display = "none";
        }
      });
    });
  }
}

// ---------------------------------------------------------------------------
// 5. ALERT AUTO-DISMISS
// ---------------------------------------------------------------------------
function initAlerts() {
  document.querySelectorAll(".alert").forEach((alert) => {
    // Auto fade after 5 seconds
    setTimeout(() => {
      alert.style.transition = "opacity 0.4s ease";
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 400);
    }, 5000);

    // Manual close button
    const closeBtn = alert.querySelector(".alert-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        alert.remove();
      });
    }
  });
}

// ---------------------------------------------------------------------------
// 6. REPORTS CHARTS INITIALIZER (Chart.js + SVG Fallback)
// ---------------------------------------------------------------------------
function renderReportsCharts(reportsData) {
  if (!reportsData) return;

  const isChartJsAvailable = typeof Chart !== "undefined";

  if (isChartJsAvailable) {
    // A. Customer Status Doughnut Chart
    const statusCtx = document.getElementById("customerStatusChart");
    if (statusCtx) {
      new Chart(statusCtx, {
        type: "doughnut",
        data: {
          labels: Object.keys(reportsData.customer_status),
          datasets: [
            {
              data: Object.values(reportsData.customer_status),
              backgroundColor: ["#10b981", "#94a3b8", "#f59e0b"],
              hoverOffset: 4,
              borderWidth: 2,
              borderColor: "#ffffff",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
              labels: { boxWidth: 12, font: { size: 12 } },
            },
          },
        },
      });
    }

    // B. Interaction Types Bar Chart
    const interCtx = document.getElementById("interactionTypesChart");
    if (interCtx) {
      new Chart(interCtx, {
        type: "bar",
        data: {
          labels: Object.keys(reportsData.interaction_types),
          datasets: [
            {
              label: "Interactions",
              data: Object.values(reportsData.interaction_types),
              backgroundColor: "#4f46e5",
              borderRadius: 6,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1, precision: 0 },
              grid: { color: "#f1f5f9" },
            },
            x: {
              grid: { display: false },
            },
          },
        },
      });
    }

    // C. Follow-up Priority & Status Chart
    const fuCtx = document.getElementById("followupsPriorityChart");
    if (fuCtx) {
      new Chart(fuCtx, {
        type: "pie",
        data: {
          labels: ["High Priority", "Medium Priority", "Low Priority"],
          datasets: [
            {
              data: [
                reportsData.followup_priority["High"] || 0,
                reportsData.followup_priority["Medium"] || 0,
                reportsData.followup_priority["Low"] || 0,
              ],
              backgroundColor: ["#ef4444", "#f59e0b", "#10b981"],
              borderWidth: 2,
              borderColor: "#ffffff",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
              labels: { boxWidth: 12, font: { size: 12 } },
            },
          },
        },
      });
    }
  } else {
    // Graceful offline pure CSS/DOM bar visualization fallback
    console.log("Chart.js CDN not reachable; activating built-in pure HTML chart fallback.");
    renderSvgFallback(reportsData);
  }
}

function renderSvgFallback(data) {
  const container = document.getElementById("interactionTypesChart");
  if (container) {
    const parent = container.parentElement;
    parent.innerHTML = `
      <div class="svg-bar-chart">
        ${Object.entries(data.interaction_types)
          .map(([type, count]) => {
            const max = Math.max(...Object.values(data.interaction_types), 1);
            const heightPercent = Math.max((count / max) * 100, 8);
            return `
            <div class="svg-bar-item">
              <span class="svg-bar-val">${count}</span>
              <div class="svg-bar-pillar" style="height: ${heightPercent}%;"></div>
              <span class="svg-bar-label">${type}</span>
            </div>
          `;
          })
          .join("")}
      </div>
    `;
  }
}
