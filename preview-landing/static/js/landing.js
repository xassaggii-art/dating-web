(function () {
  const toggle = document.getElementById("menu-toggle");
  const nav = document.getElementById("nav-mobile");

  function closeMenu() {
    if (!toggle || !nav) return;
    nav.hidden = true;
    nav.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
  }

  function openMenu() {
    if (!toggle || !nav) return;
    nav.hidden = false;
    nav.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
  }

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = toggle.getAttribute("aria-expanded") === "true";
      if (open) closeMenu();
      else openMenu();
    });

    nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", closeMenu);
    });

    window.addEventListener("scroll", closeMenu, { passive: true });
    window.addEventListener("resize", () => {
      if (window.innerWidth >= 720) closeMenu();
    });
  }

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const id = anchor.getAttribute("href");
      if (!id || id === "#") return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
})();
