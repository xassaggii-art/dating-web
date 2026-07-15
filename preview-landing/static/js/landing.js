(function () {
  const THEME_STORAGE_KEY = "vd-landing-theme";
  const root = document.documentElement;
  const themeToggle = document.getElementById("theme-toggle");

  const applyTheme = (theme) => {
    const isBlack = theme === "black";
    root.classList.toggle("theme-black", isBlack);

    if (!themeToggle) return;

    themeToggle.setAttribute("aria-pressed", String(isBlack));
    themeToggle.setAttribute(
      "aria-label",
      isBlack ? "Переключить на синюю гамму" : "Переключить на чёрную гамму"
    );
  };

  if (themeToggle) {
    const savedTheme = (() => {
      try {
        return localStorage.getItem(THEME_STORAGE_KEY);
      } catch (error) {
        return null;
      }
    })();

    if (savedTheme === "black" || savedTheme === "blue") {
      applyTheme(savedTheme);
    } else if (savedTheme) {
      try {
        localStorage.setItem(THEME_STORAGE_KEY, "blue");
      } catch (error) {
        /* ignore storage errors */
      }
    }

    themeToggle.addEventListener("click", () => {
      const nextTheme = root.classList.contains("theme-black") ? "blue" : "black";
      applyTheme(nextTheme);

      try {
        localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
      } catch (error) {
        /* ignore storage errors */
      }
    });
  }

  const toggle = document.getElementById("menu-toggle");
  const nav = document.getElementById("nav-mobile");
  const curtain = document.getElementById("intro-curtain");

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
      closeMenu();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  if (curtain && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    requestAnimationFrame(() => {
      curtain.classList.add("is-done");
      window.setTimeout(() => curtain.remove(), 1100);
    });
  } else if (curtain) {
    curtain.remove();
  }

  const revealEls = document.querySelectorAll(".reveal-on-scroll");
  if (revealEls.length) {
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          });
        },
        { threshold: 0.12, rootMargin: "0px 0px -48px 0px" }
      );
      revealEls.forEach((el) => observer.observe(el));
    } else {
      revealEls.forEach((el) => el.classList.add("is-visible"));
    }
  }

  const heartScene = document.getElementById("heart-scene");
  const siteMain = document.getElementById("site-main");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const LAYOUT_SEED = 20260715;
  const WATERFALL_COLS = 4;
  const WATERFALL_ROW_STEP = 215;
  const SCROLL_LAG_RATIO = 0.44;
  const HEART_VISIBLE_RATIO = 0.75;

  if (heartScene && siteMain) {
    const root = document.documentElement;
    const hearts = [];
    let lagScrollY = window.scrollY;
    let layoutFrame = null;
    let scrollPulseTimer = null;
    let previousPulseScrollY = window.scrollY;

    const denseSelectors = [
      ".consultation-card",
      ".emotion-card",
      ".step-card",
      ".feature-card",
      ".pain-card",
      ".review-card",
      ".price-card",
      ".faq-item",
      ".consultation-mockup",
      ".store-btn",
      ".btn",
      "img",
      "h1",
      "h2",
      "h3",
    ].join(",");

    const sparseSelectors = [
      ".hero",
      ".section-head",
      ".section-download",
      ".agency-strip",
      ".cta-band",
      ".section-emotions",
      ".section-alt",
    ].join(",");

    const createRng = (seed) => {
      let state = seed % 2147483647;
      if (state <= 0) state += 2147483646;
      return () => {
        state = (state * 16807) % 2147483647;
        return (state - 1) / 2147483646;
      };
    };

    const getSheetHeight = () =>
      Math.max(
        document.documentElement.scrollHeight,
        document.body.scrollHeight,
        window.innerHeight
      ) + window.innerHeight * 0.55;

    const getHeartRadius = () => {
      const size = Math.min(window.innerWidth * 0.25, window.innerHeight * 0.21);
      return size * 0.4;
    };

    const syncSheetHeight = () => {
      root.style.setProperty("--heart-sheet-height", `${getSheetHeight()}px`);
    };

    const ensureHeartCount = (targetCount) => {
      while (hearts.length < targetCount) {
        const heart = document.createElement("div");
        heart.className = "heart-scene__heart";
        heart.textContent = "♥";
        heart.setAttribute("aria-hidden", "true");
        heartScene.appendChild(heart);
        hearts.push(heart);
      }

      for (let i = targetCount; i < hearts.length; i += 1) {
        hearts[i].style.display = "none";
      }

      for (let i = 0; i < targetCount; i += 1) {
        hearts[i].style.display = "";
      }
    };

    const layoutBalancedHearts = () => {
      syncSheetHeight();

      const sheetHeight = getSheetHeight();
      const sheetWidth = window.innerWidth;
      const minDistance = getHeartRadius() * 2.05;
      const rows = Math.max(4, Math.ceil((sheetHeight - 180) / WATERFALL_ROW_STEP));
      const fullCount = rows * WATERFALL_COLS;
      const targetCount = Math.max(6, Math.round(fullCount * HEART_VISIBLE_RATIO));
      const colX = [15, 36, 58, 80];
      const rng = createRng(LAYOUT_SEED + Math.round(sheetWidth / 48));
      const placed = [];

      ensureHeartCount(targetCount);

      const topPadding = 100;
      const slots = [];

      for (let row = 0; row < rows; row += 1) {
        for (let col = 0; col < WATERFALL_COLS; col += 1) {
          slots.push({ row, col });
        }
      }

      for (let i = slots.length - 1; i > 0; i -= 1) {
        const j = Math.floor(rng() * (i + 1));
        const temp = slots[i];
        slots[i] = slots[j];
        slots[j] = temp;
      }

      const selectedSlots = slots.slice(0, targetCount);

      for (let index = 0; index < targetCount; index += 1) {
        const { row, col } = selectedSlots[index];
        const rowProgress = rows === 1 ? 0.5 : row / (rows - 1);
        const usableHeight = sheetHeight - topPadding * 2;
        const anchorY = topPadding + rowProgress * usableHeight;
        const anchorX = colX[col];

        let x = anchorX;
        let y = anchorY;
        let accepted = false;

        for (let attempt = 0; attempt < 24; attempt += 1) {
          const jitterX = (rng() - 0.5) * 12;
          const jitterY = (rng() - 0.5) * (WATERFALL_ROW_STEP * 0.42);
          const cascadeShift = (col % 2) * 18;
          x = anchorX + jitterX;
          y = anchorY + jitterY + cascadeShift;

          const hit = placed.some((point) => {
            const dx = (x / 100) * sheetWidth - (point.x / 100) * sheetWidth;
            const dy = y - point.y;
            return Math.hypot(dx, dy) < minDistance;
          });

          if (!hit) {
            accepted = true;
            break;
          }
        }

        if (!accepted) {
          x = anchorX + (col % 2) * 4;
          y = anchorY + (row % 2) * 22;
        }

        placed.push({ x, y });

        const scale = 0.88 + (row % 3) * 0.03 + rng() * 0.06;
        const opacity = 0.36 + (col % 2) * 0.03 + rng() * 0.04;
        const heart = hearts[index];

        heart.dataset.baseX = x.toFixed(2);
        heart.dataset.baseY = String(y);
        heart.dataset.baseScale = scale.toFixed(3);
        heart.dataset.baseOpacity = opacity.toFixed(2);
        heart.dataset.wobble = (rng() * Math.PI * 2).toFixed(3);

        heart.style.setProperty("--heart-x", `${x}%`);
        heart.style.setProperty("--heart-y", `${y}px`);
        heart.style.setProperty("--heart-scale", scale.toFixed(3));
        heart.style.setProperty("--heart-opacity", opacity.toFixed(2));
        heart.style.setProperty("--heart-lift", "0px");
      }
    };

    const scheduleLayout = () => {
      if (layoutFrame) return;
      layoutFrame = requestAnimationFrame(() => {
        layoutBalancedHearts();
        layoutFrame = null;
      });
    };

    const revealHeart = () => {
      heartScene.classList.add("is-visible");
    };

    const pulseScrollMotion = () => {
      heartScene.classList.add("is-scrolling");

      if (scrollPulseTimer) window.clearTimeout(scrollPulseTimer);
      scrollPulseTimer = window.setTimeout(() => {
        heartScene.classList.remove("is-scrolling");
      }, 180);
    };

    const getEmptyBoost = () => {
      const x = window.innerWidth * 0.5;
      const y = window.innerHeight * 0.5;
      const stack = document.elementsFromPoint(x, y);
      if (!stack.length) return 1;

      for (const el of stack) {
        if (el === heartScene || el.closest("#heart-scene")) continue;
        if (el.closest(denseSelectors)) return 1;
        if (el.closest(sparseSelectors)) return 1.02;
        if (el.tagName === "SECTION" || el.tagName === "MAIN" || el.tagName === "BODY") return 1.015;
      }

      return 1.01;
    };

    const updateHeartMotion = () => {
      const scrollY = window.scrollY;
      const scrollDelta = scrollY - previousPulseScrollY;
      const motionStrength = Math.min(1, Math.abs(scrollDelta) / 9);
      const active = heartScene.classList.contains("is-visible");
      const emptyBoost = getEmptyBoost();
      const scrollLift = motionStrength * -10;

      lagScrollY += (scrollY - lagScrollY) * (reduceMotion ? 1 : 0.11);
      const lagOffset = lagScrollY * SCROLL_LAG_RATIO;

      if (motionStrength > 0.08) pulseScrollMotion();

      hearts.forEach((heart) => {
        if (heart.style.display === "none") return;

        const baseY = Number(heart.dataset.baseY || 0);
        const baseScale = Number(heart.dataset.baseScale || 1);
        const wobble = Number(heart.dataset.wobble || 0);
        const drift = Math.sin(scrollY * 0.008 + wobble) * 5;
        const y = baseY + drift;
        const scale = baseScale + motionStrength * 0.03;

        heart.style.setProperty("--heart-y", `${y}px`);
        heart.style.setProperty("--heart-scale", scale.toFixed(3));
        heart.style.setProperty("--heart-lift", `${scrollLift}px`);
        heart.style.setProperty("--heart-boost", emptyBoost.toFixed(3));
      });

      root.style.setProperty("--heart-lag-y", `${-lagOffset}px`);
      heartScene.classList.toggle("is-active", active);
      previousPulseScrollY = scrollY;
    };

    const animateHearts = () => {
      updateHeartMotion();
      requestAnimationFrame(animateHearts);
    };

    scheduleLayout();

    if (curtain) {
      window.setTimeout(revealHeart, 900);
    } else {
      revealHeart();
    }

    requestAnimationFrame(animateHearts);
    window.addEventListener("resize", () => {
      scheduleLayout();
    }, { passive: true });
    window.addEventListener("load", scheduleLayout);
  }
})();
