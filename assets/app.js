const LOCAL_COUNTER_ENDPOINT = "/api/visit";
const X_WIDGETS_SRC = "https://platform.x.com/widgets.js";
let xWidgetsPromise = null;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootSite);
} else {
  bootSite();
}

function bootSite() {
  revealSections();
  cleanupLegacyServiceWorkers().catch(() => {
    // Ignore legacy service worker cleanup failures.
  });
  initializeVisitorCounter().catch(() => {
    setVisitCount("Unavailable");
  });
  setCurrentYear();
  initializeLeadershipFeed().catch(() => {
    // Keep the page usable if X widgets fail to load.
  });
}

function revealSections() {
  const targets = document.querySelectorAll("[data-reveal]");
  if (!targets.length) {
    return;
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) {
    targets.forEach((node) => node.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    {
      threshold: 0.12,
      rootMargin: "0px 0px -48px 0px",
    }
  );

  targets.forEach((node) => observer.observe(node));
}

async function initializeVisitorCounter() {
  const localCounter = await fetchLocalCounter();
  if (localCounter !== null) {
    setVisitCount(formatInteger(localCounter));
    return;
  }

  const namespace = "shadowfetch-news";
  const counterName = "site-visits";
  const sessionKey = "shadowfetch_site_visit_counted";
  const hasCounted = readSessionValue(sessionKey) === "1";
  const endpoint = hasCounted
    ? `https://api.counterapi.dev/v1/${namespace}/${counterName}/`
    : `https://api.counterapi.dev/v1/${namespace}/${counterName}/up`;

  let response = await fetch(endpoint, { cache: "no-store" });
  if (!response.ok && hasCounted) {
    response = await fetch(`https://api.counterapi.dev/v1/${namespace}/${counterName}/up`, { cache: "no-store" });
  }
  if (!response.ok) {
    throw new Error("Counter request failed");
  }

  const payload = await response.json();
  writeSessionValue(sessionKey, "1");
  setVisitCount(formatInteger(payload.count ?? payload.value));
}

async function fetchLocalCounter() {
  const sessionKey = "shadowfetch_site_visit_counted";
  const hasCounted = readSessionValue(sessionKey) === "1";
  const method = hasCounted ? "GET" : "POST";

  try {
    const response = await fetch(LOCAL_COUNTER_ENDPOINT, {
      method,
      cache: "no-store",
      headers: {
        "content-type": "application/json",
      },
    });

    if (!response.ok) {
      return null;
    }

    const payload = await response.json();
    if (!payload || typeof payload.count !== "number") {
      return null;
    }

    writeSessionValue(sessionKey, "1");
    return payload.count;
  } catch {
    return null;
  }
}

function setVisitCount(value) {
  document.querySelectorAll("[data-visit-count]").forEach((node) => {
    node.textContent = value;
  });
}

function setCurrentYear() {
  const year = String(new Date().getFullYear());
  document.querySelectorAll("[data-current-year]").forEach((node) => {
    node.textContent = year;
  });
}

async function initializeLeadershipFeed() {
  const rotator = document.querySelector("[data-x-rotator]");
  if (!rotator) {
    return;
  }

  const panels = Array.from(rotator.querySelectorAll("[data-x-panel]"));
  const toggles = Array.from(rotator.querySelectorAll("[data-x-toggle]"));
  if (!panels.length || !toggles.length) {
    return;
  }

  await loadXWidgets().catch(() => null);

  let activeIndex = Math.max(
    0,
    panels.findIndex((panel) => panel.classList.contains("is-active"))
  );
  let intervalId = null;

  const setActive = (index) => {
    activeIndex = index;
    panels.forEach((panel, panelIndex) => {
      panel.classList.toggle("is-active", panelIndex === index);
    });
    toggles.forEach((toggle, toggleIndex) => {
      const isActive = toggleIndex === index;
      toggle.classList.toggle("is-active", isActive);
      toggle.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
    renderActiveTimeline(panels[index]);
  };

  const restartRotation = () => {
    if (intervalId) {
      window.clearInterval(intervalId);
    }
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || panels.length < 2) {
      return;
    }
    const interval = Number(rotator.dataset.xInterval || 12000);
    intervalId = window.setInterval(() => {
      setActive((activeIndex + 1) % panels.length);
    }, interval);
  };

  toggles.forEach((toggle, index) => {
    toggle.addEventListener("click", () => {
      setActive(index);
      restartRotation();
    });
  });

  setActive(activeIndex);
  restartRotation();
}

function loadXWidgets() {
  if (window.twttr?.widgets) {
    return Promise.resolve(window.twttr);
  }
  if (xWidgetsPromise) {
    return xWidgetsPromise;
  }

  xWidgetsPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${X_WIDGETS_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve(window.twttr), { once: true });
      existing.addEventListener("error", reject, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = X_WIDGETS_SRC;
    script.async = true;
    script.charset = "utf-8";
    script.onload = () => {
      if (window.twttr?.ready) {
        window.twttr.ready(() => resolve(window.twttr));
        return;
      }
      resolve(window.twttr);
    };
    script.onerror = reject;
    document.head.appendChild(script);
  });

  return xWidgetsPromise;
}

function renderActiveTimeline(panel) {
  if (!panel || panel.dataset.xRendered === "true") {
    return;
  }

  const target = panel.querySelector("[data-x-embed]");
  if (!target) {
    return;
  }

  if (target.querySelector("iframe")) {
    panel.dataset.xRendered = "true";
    return;
  }

  if (window.twttr?.widgets?.load) {
    window.twttr.widgets.load(target);
    panel.dataset.xRendered = "true";
  }
}

function formatInteger(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "Unavailable";
  }
  return new Intl.NumberFormat("en-US").format(Math.round(number));
}

async function cleanupLegacyServiceWorkers() {
  if (!("serviceWorker" in navigator)) {
    return;
  }

  const registrations = await navigator.serviceWorker.getRegistrations();
  if (!registrations.length) {
    return;
  }

  const hadController = Boolean(navigator.serviceWorker.controller);
  await Promise.all(registrations.map((registration) => registration.unregister().catch(() => false)));

  if ("caches" in window) {
    const keys = await window.caches.keys();
    await Promise.all(
      keys
        .filter((key) => key.startsWith("shadowfetch-"))
        .map((key) => window.caches.delete(key))
    );
  }

  const reloadKey = "shadowfetch_service_worker_cleared";
  if (hadController && readSessionValue(reloadKey) !== "1") {
    writeSessionValue(reloadKey, "1");
    window.location.reload();
  }
}

function readSessionValue(key) {
  try {
    return window.sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeSessionValue(key, value) {
  try {
    window.sessionStorage.setItem(key, value);
  } catch {
    // Ignore storage failures.
  }
}
