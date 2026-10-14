/**
 * Restaurant Billing System — Client-Side Scripts
 * TQM Quality Goal: Q11 - Improve Maintainability
 * Student: Swati Melkani (CSE - B, 2026-27)
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Auto-dismiss flash alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 5000);
  });

  // 2. Add confirmation prompt to destructive forms
  const confirmForms = document.querySelectorAll("form[data-confirm]");
  confirmForms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      const message = form.getAttribute("data-confirm") || "Are you sure you want to proceed?";
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // 3. Print Invoice button handler
  const printBtn = document.getElementById("printInvoiceBtn");
  if (printBtn) {
    printBtn.addEventListener("click", () => {
      window.print();
    });
  }
});
