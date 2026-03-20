const siteConfig = {
  social: {
    x: {
      label: "X / Twitter",
      url: "https://x.com/MrBobCorbin"
    },
    bluesky: {
      label: "Bluesky",
      url: "https://bsky.app/profile/mrbobcorbin.bsky.social"
    },
    kalshi: {
      label: "Kalshi",
      url: "https://kalshi.com/sign-up/?referral=6ca54e6d-a516-4918-bc0a-829b18f99f70"
    }
  }
};

const SEARCH_INDEX_URL = "/assets/data/search-index.json";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootSite);
} else {
  bootSite();
}

function bootSite() {
  applySocialLinks();
  initializeVisitorCounter().catch(() => {
    setVisitCount("Unavailable");
  });
  initializeFilterToolbars();
  initializeSearchPage().catch(() => {
    const empty = document.getElementById("search-empty");
    if (empty) {
      empty.hidden = false;
      empty.textContent = "Search is temporarily unavailable.";
    }
  });
}

function applySocialLinks() {
  document.querySelectorAll("[data-social-link]").forEach((node) => {
    const key = node.dataset.socialLink;
    const config = siteConfig.social[key];
    if (!config) {
      return;
    }

    const safe = safeUrl(config.url);
    node.href = safe === "#" ? node.getAttribute("href") || "#" : safe;
    if (safe === "#") {
      node.removeAttribute("target");
      node.removeAttribute("rel");
    }

    if (!node.textContent.trim()) {
      node.textContent = config.label;
    }
  });
}

async function initializeVisitorCounter() {
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

function setVisitCount(value) {
  document.querySelectorAll("[data-visit-count]").forEach((node) => {
    node.textContent = value;
  });
}

function initializeFilterToolbars() {
  document.querySelectorAll("[data-filter-toolbar]").forEach((toolbar) => {
    const gridId = toolbar.dataset.targetGrid;
    const summaryId = toolbar.dataset.summaryId;
    const grid = gridId ? document.getElementById(gridId) : null;
    const summary = summaryId ? document.getElementById(summaryId) : null;

    if (!grid || !summary) {
      return;
    }

    toolbar.querySelectorAll("[data-filter-key]").forEach((button) => {
      button.addEventListener("click", () => {
        applyToolbarFilter(toolbar, grid, summary, button.dataset.filterKey || "all");
      });
    });

    applyToolbarFilter(toolbar, grid, summary, "all");
  });
}

function applyToolbarFilter(toolbar, grid, summary, filterKey) {
  const cards = [...grid.querySelectorAll("[data-section-key]")];
  let visibleCount = 0;

  cards.forEach((card) => {
    const matches = filterKey === "all" || card.dataset.sectionKey === filterKey;
    card.hidden = !matches;
    if (matches) {
      visibleCount += 1;
    }
  });

  toolbar.querySelectorAll("[data-filter-key]").forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.filterKey === filterKey ? "true" : "false");
  });

  const label = currentFilterLabel(toolbar, filterKey);
  if (filterKey === "all") {
    summary.textContent = `Showing ${visibleCount} story${visibleCount === 1 ? "" : "ies"} across every section in this view.`;
  } else {
    summary.textContent = `Showing ${visibleCount} ${label.toLowerCase()} story${visibleCount === 1 ? "" : "ies"} in this view.`;
  }
}

function currentFilterLabel(toolbar, filterKey) {
  if (filterKey === "all") {
    return "All Stories";
  }

  const button = [...toolbar.querySelectorAll("[data-filter-key]")].find((candidate) => candidate.dataset.filterKey === filterKey);
  return button ? button.dataset.filterLabel || button.textContent.trim() : "Filtered";
}

async function initializeSearchPage() {
  const results = document.getElementById("search-results");
  const empty = document.getElementById("search-empty");
  if (!results || !empty) {
    return;
  }

  const response = await fetch(SEARCH_INDEX_URL, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Could not load search index");
  }

  const searchIndex = await response.json();
  const query = new URLSearchParams(window.location.search).get("q") || "";
  const forms = [...document.querySelectorAll("[data-search-form]")];
  const inputs = [...document.querySelectorAll("[data-search-input]")];
  const titleNode = document.querySelector("[data-search-title]");
  const summaryNode = document.querySelector("[data-search-summary]");

  inputs.forEach((input) => {
    input.value = query;
  });

  forms.forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const value = String(formData.get("q") || "").trim();
      updateSearchQuery(value);
      inputs.forEach((input) => {
        input.value = value;
      });
      renderSearchResults(searchIndex, value, results, empty, titleNode, summaryNode);
    });
  });

  inputs.forEach((input) => {
    input.addEventListener("input", () => {
      const value = input.value.trim();
      inputs.forEach((node) => {
        if (node !== input) {
          node.value = value;
        }
      });
      updateSearchQuery(value);
      renderSearchResults(searchIndex, value, results, empty, titleNode, summaryNode);
    });
  });

  renderSearchResults(searchIndex, query, results, empty, titleNode, summaryNode);
}

function renderSearchResults(searchIndex, query, resultsNode, emptyNode, titleNode, summaryNode) {
  const normalizedQuery = query.trim();
  if (!normalizedQuery) {
    resultsNode.innerHTML = "";
    emptyNode.hidden = false;
    emptyNode.textContent = "Enter a search above to explore the site.";
    if (titleNode) {
      titleNode.textContent = "Search the newsroom";
    }
    if (summaryNode) {
      summaryNode.textContent = "Type a topic, person, company, place, or source to pull up matching pages.";
    }
    return;
  }

  const ranked = rankSearchResults(searchIndex, normalizedQuery).slice(0, 36);
  if (!ranked.length) {
    resultsNode.innerHTML = "";
    emptyNode.hidden = false;
    emptyNode.textContent = `No results found for "${normalizedQuery}".`;
    if (titleNode) {
      titleNode.textContent = `Search: ${normalizedQuery}`;
    }
    if (summaryNode) {
      summaryNode.textContent = "Try a broader keyword, source name, or topic title.";
    }
    return;
  }

  emptyNode.hidden = true;
  resultsNode.innerHTML = ranked.map((item) => searchResultMarkup(item)).join("");

  if (titleNode) {
    titleNode.textContent = `Search: ${normalizedQuery}`;
  }
  if (summaryNode) {
    summaryNode.textContent = `Showing ${ranked.length} result${ranked.length === 1 ? "" : "s"} across briefs, topics, sources, and coverage pages.`;
  }
}

function rankSearchResults(searchIndex, query) {
  const normalized = normalizeText(query);
  const tokens = normalized.split(/\s+/).filter(Boolean);

  return searchIndex
    .map((item) => {
      const haystack = normalizeText([
        item.title,
        item.summary,
        item.type,
        item.section,
        item.source,
        item.keywords
      ].join(" "));

      let score = 0;
      if (normalizeText(item.title).includes(normalized)) {
        score += 12;
      }
      if (haystack.includes(normalized)) {
        score += 6;
      }

      tokens.forEach((token) => {
        if (normalizeText(item.title).includes(token)) {
          score += 4;
        }
        if (haystack.includes(token)) {
          score += 1;
        }
      });

      if (item.type === "Topic" && tokens.some((token) => normalizeText(item.title).includes(token))) {
        score += 2;
      }

      return { ...item, score };
    })
    .filter((item) => item.score > 0)
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }
      return new Date(right.timestamp || 0) - new Date(left.timestamp || 0);
    });
}

function searchResultMarkup(item) {
  return `
    <article class="search-card">
      <div class="story-meta">
        <span class="story-tag">${escapeHtml(item.type || "Result")}</span>
        <span class="story-source">${escapeHtml(item.section || "")}</span>
        <span class="story-time">${escapeHtml(item.source || "")}</span>
      </div>
      <h3><a class="story-headline-link" href="${safeUrlOrPath(item.path)}">${escapeHtml(item.title || "Untitled")}</a></h3>
      <p>${escapeHtml(item.summary || "")}</p>
      <div class="story-actions">
        <a class="story-link" href="${safeUrlOrPath(item.path)}">Open page</a>
      </div>
    </article>
  `;
}

function updateSearchQuery(value) {
  const url = new URL(window.location.href);
  if (value) {
    url.searchParams.set("q", value);
  } else {
    url.searchParams.delete("q");
  }
  window.history.replaceState({}, "", url.toString());
}

function normalizeText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function formatInteger(value) {
  return new Intl.NumberFormat("en-US").format(Number(value) || 0);
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
    // Ignore storage failures and keep the page working.
  }
}

function safeUrl(url) {
  try {
    const parsed = new URL(url);
    return /^https?:$/i.test(parsed.protocol) ? parsed.toString() : "#";
  } catch {
    return "#";
  }
}

function safeUrlOrPath(value) {
  if (String(value).startsWith("/")) {
    return value;
  }
  return safeUrl(value);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
