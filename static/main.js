document.addEventListener("DOMContentLoaded", () => {
  // Animated counters on dashboard metrics
  const counters = document.querySelectorAll("[data-count-target]");

  counters.forEach((el) => {
    const target = parseInt(el.getAttribute("data-count-target") || "0", 10);
    if (!Number.isFinite(target)) return;

    const duration = 900;
    const start = performance.now();

    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out
      const value = Math.floor(target * eased);
      el.textContent = value.toString();
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target.toString();
      }
    };

    // Start from zero visually
    el.textContent = "0";
    requestAnimationFrame(step);
  });

  // Enable Bootstrap tooltips if available
  if (window.bootstrap) {
    const tooltipTriggerList = [].slice.call(
      document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.forEach((tooltipTriggerEl) => {
      new window.bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

});

