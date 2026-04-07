const LOCAL_COUNTER_ENDPOINT = "/api/visit";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootSite);
} else {
  bootSite();
}

function bootSite() {
  revealSections();
  initializeVisitorCounter().catch(() => {
    setVisitCount("Unavailable");
  });
  setCurrentYear();
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

function formatInteger(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "Unavailable";
  }
  return new Intl.NumberFormat("en-US").format(Math.round(number));
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
