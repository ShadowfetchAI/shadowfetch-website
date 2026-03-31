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
const LOCAL_COUNTER_ENDPOINT = "/api/visit";
const LOCAL_META_ENDPOINT = "/api/meta";
const LOCAL_LATEST_ENDPOINT = "/api/latest";
const LOCAL_WEATHER_ENDPOINT = "/api/weather";
const LOCAL_SPORTS_ENDPOINT = "/api/sports";
const LOCAL_MARKETS_ENDPOINT = "/api/markets";
const BIBLE_SUMMARY_ENDPOINT = "/assets/data/bible-edition.json";
const BIBLE_DAY_ENDPOINT = "/api/day";
const BIBLE_PROGRESS_ENDPOINT = "/api/progress";
const BIBLE_PROFILE_KEY = "shadowfetch_bible_profile";
const BIBLE_PROGRESS_KEY = "shadowfetch_bible_progress";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootSite);
} else {
  bootSite();
}

function bootSite() {
  if (document.body?.dataset.edition === "bible") {
    bootBibleEdition();
    return;
  }
  applySocialLinks();
  initializeVisitorCounter().catch(() => {
    setVisitCount("Unavailable");
  });
  initializeLiveEdition().catch(() => {
    // Keep the static build visible if live hydration is unavailable.
  });
  initializeUtilitySurfaces().catch(() => {
    // Utility panels should fail quietly and keep the static page readable.
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

function bootBibleEdition() {
  applyBibleTheme();
  wireBibleThemeToggle();
  wireBibleSignupForms();
  wireBibleMarkRead();
  initializeVisitorCounter().catch(() => {
    setVisitCount("Unavailable");
  });
  registerBiblePwa();
  hydrateBibleEdition().catch(() => {
    // Keep the build readable if personalization fails.
  });
}

function applyBibleTheme() {
  const saved = localStorage.getItem("shadowfetch_bible_theme") || "dark";
  document.body.dataset.theme = saved;
}

function wireBibleThemeToggle() {
  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    const updateLabel = () => {
      const current = document.body.dataset.theme || "dark";
      button.textContent = current === "dark" ? "Light Mode" : "Dark Mode";
    };
    updateLabel();
    button.addEventListener("click", () => {
      const next = (document.body.dataset.theme || "dark") === "dark" ? "light" : "dark";
      document.body.dataset.theme = next;
      localStorage.setItem("shadowfetch_bible_theme", next);
      updateLabel();
    });
  });
}

function wireBibleSignupForms() {
  document.querySelectorAll("[data-signup-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const status = form.querySelector("[data-signup-status]");
      const formData = new FormData(form);
      const body = Object.fromEntries(formData.entries());
      body.subscribed = formData.get("subscribed") === "1";
      if (status) {
        status.textContent = "Saving your reading setup...";
      }
      try {
        const response = await fetch("/api/signup", {
          method: "POST",
          headers: {
            "content-type": "application/json"
          },
          body: JSON.stringify(body)
        });
        const payload = await response.json();
        if (!response.ok || !payload?.ok) {
          throw new Error(payload?.error || "Could not save your signup.");
        }
        saveBibleProfile({
          email: payload.email,
          canon: payload.canon,
          start_date: payload.startDate,
          subscribed: payload.subscribed,
        });
        if (status) {
          status.textContent = payload.message || "You are set.";
        }
        if (payload.redirect) {
          window.location.href = payload.redirect;
        }
      } catch (error) {
        if (status) {
          status.textContent = error.message || "Could not save your reading setup yet.";
        }
      }
    });
  });
}

function wireBibleMarkRead() {
  document.body.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-mark-read]");
    if (!button) {
      return;
    }

    const profile = readBibleProfile();
    const readingDay = Number.parseInt(button.dataset.readingDay || "1", 10) || 1;
    const readingDate = new Date().toISOString().slice(0, 10);
    button.disabled = true;
    button.textContent = "Saving...";

    const progressSet = readLocalProgress(profile);
    progressSet.add(readingDay);
    writeLocalProgress(profile, progressSet);

    try {
      const response = await fetch(BIBLE_PROGRESS_ENDPOINT, {
        method: "POST",
        headers: {
          "content-type": "application/json"
        },
        body: JSON.stringify({
          email: profile.email || "",
          reading_day: readingDay,
          reading_date: readingDate
        })
      });
      const payload = await response.json();
      if (!response.ok || !payload?.ok) {
        throw new Error(payload?.error || "Could not mark this reading yet.");
      }
      button.textContent = "Marked as Read";
      hydrateBibleEdition().catch(() => {});
    } catch (error) {
      button.disabled = false;
      button.textContent = "Try again";
    }
  });
}

function registerBiblePwa() {
  if (!("serviceWorker" in navigator)) {
    return;
  }
  navigator.serviceWorker.register("/service-worker.js").catch(() => {
    // Keep the site readable even if the PWA layer is unavailable.
  });
}

async function hydrateBibleEdition() {
  const page = document.body?.dataset.page || "home";
  const summary = await fetchBibleSummary();
  const profile = readBibleProfile(summary);
  syncBibleForms(profile);

  if (page === "home" || page === "bible") {
    const reading = await fetchBibleReading(profile);
    renderBibleReadingPage(page, reading);
    updateBibleProgressUi(summary, profile);
  }

  if (page === "calendar") {
    renderBibleCalendar(summary, profile);
  }

  if (page === "archive") {
    renderBibleArchive(summary, profile);
  }
}

async function fetchBibleSummary() {
  const response = await fetch(BIBLE_SUMMARY_ENDPOINT, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Could not load bible summary.");
  }
  return response.json();
}

function readBibleProfile(summary = null) {
  const fromStorage = safeJsonParse(localStorage.getItem(BIBLE_PROFILE_KEY)) || {};
  const params = new URLSearchParams(window.location.search);
  const fallback = summary?.default_profile || {};
  const profile = {
    canon: params.get("canon") || fromStorage.canon || fallback.canon || "protestant",
    start_date: params.get("start_date") || fromStorage.start_date || fallback.start_date || new Date().toISOString().slice(0, 10),
    email: params.get("email") || fromStorage.email || "",
    subscribed: typeof fromStorage.subscribed === "boolean" ? fromStorage.subscribed : true
  };
  saveBibleProfile(profile);
  return profile;
}

function saveBibleProfile(profile) {
  const safeProfile = {
    canon: profile?.canon === "catholic" ? "catholic" : "protestant",
    start_date: String(profile?.start_date || new Date().toISOString().slice(0, 10)),
    email: String(profile?.email || ""),
    subscribed: profile?.subscribed !== false
  };
  localStorage.setItem(BIBLE_PROFILE_KEY, JSON.stringify(safeProfile));
}

async function fetchBibleReading(profile) {
  const query = new URLSearchParams({
    canon: profile.canon,
    start_date: profile.start_date
  });
  const dayParam = new URLSearchParams(window.location.search).get("day");
  if (dayParam) {
    query.set("day", dayParam);
  }
  const response = await fetch(`${BIBLE_DAY_ENDPOINT}?${query.toString()}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Could not load bible reading.");
  }
  const payload = await response.json();
  if (!payload?.ok) {
    throw new Error(payload?.error || "Could not load bible reading.");
  }
  return payload.reading;
}

function renderBibleReadingPage(page, reading) {
  const rootId = page === "home" ? "home-reading-root" : "bible-reading-root";
  const root = document.getElementById(rootId);
  if (root) {
    root.innerHTML = page === "home"
      ? renderBibleHomePreviewHtml(reading)
      : renderBibleReadingHtml(reading, { showQuote: page === "bible" });
  }
  const quoteRoot = document.getElementById("home-quote-root");
  if (page === "home" && quoteRoot && reading?.quote) {
    quoteRoot.innerHTML = renderBibleQuoteHtml(reading.quote);
  }
  const ribbonDay = document.getElementById("home-ribbon-day");
  if (page === "home" && ribbonDay) {
    ribbonDay.textContent = `Day ${reading.day_number} of 365`;
  }
}

function renderBibleHomePreviewHtml(reading) {
  const firstChapter = Array.isArray(reading?.chapters) ? reading.chapters[0] : null;
  const firstVerse = Array.isArray(firstChapter?.verses) ? firstChapter.verses[0] : null;
  const previewText = firstVerse?.text
    ? `${firstVerse.text.slice(0, 220)}${firstVerse.text.length > 220 ? "…" : ""}`
    : "A calm daily reading, one complete day at a time.";

  return `
    <div class="reading-lead-body reading-preview">
      <p class="paper-kicker">Today's Reading</p>
      <h1 class="paper-headline bible-headline">Day ${reading.day_number}</h1>
      <p class="paper-summary">${escapeHtml(reading.references)}</p>
      <div class="reading-meta reading-meta-strong">
        <span>${reading.estimated_minutes} minute read</span>
        <span>${reading.word_count} words</span>
        <span>${escapeHtml(reading.translation)}</span>
      </div>
      <p class="reading-preview-copy">One clean email a day with the exact chapters for your place in the plan. No paywall. No clutter.</p>
      <div class="panel mini-panel reading-preview-excerpt">
        <p class="panel-label">First verse</p>
        <p>${escapeHtml(previewText)}</p>
      </div>
      <div class="hero-actions devotional-actions reading-preview-actions">
        <a class="button button-primary" href="/signup/">Start free</a>
        <a class="button button-secondary" href="/bible/">Preview today's reading</a>
      </div>
      <p class="tomorrow-teaser">Tomorrow's teaser: <a href="/calendar/">${escapeHtml(reading.tomorrow_teaser)}</a></p>
    </div>
  `;
}

function renderBibleReadingHtml(reading, options = {}) {
  const chapters = Array.isArray(reading?.chapters) ? reading.chapters : [];
  const chapterMarkup = chapters.map((chapter) => renderBibleChapterHtml(chapter)).join("");
  const quoteMarkup = options.showQuote && reading?.quote ? renderBibleQuoteHtml(reading.quote) : "";
  return `
    <div class="reading-lead-body">
      <p class="paper-kicker">Today's Reading</p>
      <h1 class="paper-headline bible-headline">Day ${reading.day_number}</h1>
      <p class="paper-summary">${escapeHtml(reading.references)}</p>
      <div class="reading-meta reading-meta-strong">
        <span>${reading.estimated_minutes} minute read</span>
        <span>${reading.word_count} words</span>
        <span>${escapeHtml(reading.translation)}</span>
      </div>
      <div class="support-banner">
        <p>These daily chapters are free thanks to people like you. Donate what you want to help keep the emails going for everyone.</p>
        <a class="button button-secondary" href="https://www.buymeacoffee.com/shadowfetch" target="_blank" rel="noreferrer noopener">Buy Me a Coffee</a>
      </div>
      <div class="reading-stack">${chapterMarkup}</div>
      <div class="hero-actions devotional-actions">
        <button class="button button-primary" type="button" data-mark-read data-reading-day="${reading.day_number}">Mark as Read</button>
        <a class="button button-secondary" href="/calendar/">Open calendar</a>
      </div>
      <p class="tomorrow-teaser">Tomorrow's teaser: <a href="/calendar/">${escapeHtml(reading.tomorrow_teaser)}</a></p>
      ${quoteMarkup}
    </div>
  `;
}

function renderBibleChapterHtml(chapter) {
  const verses = Array.isArray(chapter?.verses) ? chapter.verses : [];
  const verseMarkup = verses
    .map(
      (verse) => `
        <p class="verse-row"><span class="verse-number">${verse.verse}</span><span>${escapeHtml(verse.text)}</span></p>
      `
    )
    .join("");
  return `
    <article class="panel chapter-reading">
      <p class="panel-label">Chapter</p>
      <h3>${escapeHtml(chapter.chapter_title)}</h3>
      <div class="reading-meta">
        <span>${chapter.verse_count} verses</span>
        <span>${chapter.word_count} words</span>
      </div>
      <div class="verse-stack">${verseMarkup}</div>
    </article>
  `;
}

function renderBibleQuoteHtml(quote) {
  return `
    <article class="panel quote-panel">
      <p class="panel-label">Verse of the day</p>
      <blockquote class="quote-block">
        <p>${escapeHtml(quote.text)}</p>
        <footer>${escapeHtml(quote.verse)}</footer>
      </blockquote>
      <p>${escapeHtml(quote.reflection)}</p>
    </article>
  `;
}

function renderBibleCalendar(summary, profile) {
  const root = document.getElementById("calendar-root");
  if (!root) {
    return;
  }
  const plan = summary?.plans?.[profile.canon] || summary?.plans?.protestant;
  const days = Array.isArray(plan?.days) ? plan.days : [];
  const progress = readLocalProgress(profile);
  const months = buildCalendarMonths(profile.start_date, days, progress);
  root.innerHTML = months
    .map(
      (month) => `
        <article class="panel calendar-month-card">
          <p class="panel-label">${escapeHtml(month.label)}</p>
          <div class="calendar-month-grid">
            ${month.days
              .map(
                (day) => `
                  <a class="calendar-month-day calendar-month-day-${day.status}" href="/bible/?canon=${encodeURIComponent(profile.canon)}&start_date=${encodeURIComponent(profile.start_date)}&day=${day.dayNumber}">
                    <strong>${day.dateLabel}</strong>
                    <span>Day ${day.dayNumber}</span>
                  </a>
                `
              )
              .join("")}
          </div>
        </article>
      `
    )
    .join("");
}

function buildCalendarMonths(startDate, planDays, progressSet) {
  const start = new Date(startDate);
  const months = [];
  let cursor = new Date(start.getFullYear(), start.getMonth(), start.getDate());
  for (let monthIndex = 0; monthIndex < 12; monthIndex += 1) {
    const label = cursor.toLocaleDateString(undefined, { month: "long", year: "numeric" });
    const daysInMonth = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0).getDate();
    const monthDays = [];
    for (let day = 1; day <= daysInMonth; day += 1) {
      const currentDate = new Date(cursor.getFullYear(), cursor.getMonth(), day);
      const dayNumber = Math.floor((currentDate.getTime() - start.getTime()) / (24 * 60 * 60 * 1000)) + 1;
      if (dayNumber < 1 || dayNumber > planDays.length) {
        continue;
      }
      let status = "upcoming";
      if (progressSet.has(dayNumber)) {
        status = "read";
      } else if (currentDate.toDateString() === new Date().toDateString()) {
        status = "today";
      } else if (currentDate < new Date()) {
        status = "missed";
      }
      monthDays.push({
        dayNumber,
        status,
        dateLabel: day
      });
    }
    if (monthDays.length) {
      months.push({ label, days: monthDays });
    }
    cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
  }
  return months;
}

function renderBibleArchive(summary, profile) {
  const root = document.getElementById("archive-root");
  if (!root) {
    return;
  }
  const plan = summary?.plans?.[profile.canon] || summary?.plans?.protestant;
  const days = Array.isArray(plan?.days) ? plan.days : [];
  const render = (query = "") => {
    const needle = query.trim().toLowerCase();
    const filtered = needle
      ? days.filter((day) => `${day.day_number} ${day.references} ${day.quote?.text || ""}`.toLowerCase().includes(needle))
      : days;
    root.innerHTML = filtered
      .map(
        (day) => `
          <article class="panel archive-card">
            <p class="panel-label">Day ${day.day_number}</p>
            <h3>${escapeHtml(day.references)}</h3>
            <p>${readingSummary(day)}</p>
            <a class="story-link" href="/bible/?canon=${encodeURIComponent(profile.canon)}&start_date=${encodeURIComponent(profile.start_date)}&day=${day.day_number}">Open reading</a>
          </article>
        `
      )
      .join("");
  };

  render();
  const search = document.getElementById("archive-search");
  if (search) {
    search.addEventListener("input", () => render(search.value));
  }
}

function readingSummary(day) {
  const quote = String(day?.quote?.text || "").trim();
  if (quote) {
    return escapeHtml(quote);
  }
  const chapterCount = Array.isArray(day?.chapters) ? day.chapters.length : 0;
  return escapeHtml(`${chapterCount} complete chapter${chapterCount === 1 ? "" : "s"} for this day.`);
}

function updateBibleProgressUi(summary, profile) {
  const plan = summary?.plans?.[profile.canon] || summary?.plans?.protestant;
  const totalDays = Number(plan?.total_days || 365);
  const progressSet = readLocalProgress(profile);
  const percentage = Math.round((progressSet.size / totalDays) * 1000) / 10;
  document.querySelectorAll(".progress-ring strong").forEach((node) => {
    node.textContent = `${percentage}%`;
  });
  document.querySelectorAll(".progress-ring span").forEach((node) => {
    node.textContent = `${progressSet.size} of ${totalDays} days`;
  });
}

function syncBibleForms(profile) {
  document.querySelectorAll("[data-signup-form]").forEach((form) => {
    const email = form.querySelector('input[name="email"]');
    const startDate = form.querySelector('input[name="start_date"]');
    const subscribed = form.querySelector('input[name="subscribed"]');
    if (email && !email.value && profile.email) {
      email.value = profile.email;
    }
    if (startDate) {
      startDate.value = profile.start_date;
    }
    form.querySelectorAll('input[name="canon"]').forEach((input) => {
      input.checked = input.value === profile.canon;
    });
    if (subscribed) {
      subscribed.checked = profile.subscribed !== false;
    }
  });
}

function readLocalProgress(profile) {
  const scope = `${profile.canon}:${profile.start_date}:${profile.email || "guest"}`;
  const raw = safeJsonParse(localStorage.getItem(`${BIBLE_PROGRESS_KEY}:${scope}`));
  return new Set(Array.isArray(raw) ? raw.map((value) => Number.parseInt(String(value), 10)).filter(Boolean) : []);
}

function writeLocalProgress(profile, progressSet) {
  const scope = `${profile.canon}:${profile.start_date}:${profile.email || "guest"}`;
  const values = Array.from(progressSet).sort((a, b) => a - b);
  localStorage.setItem(`${BIBLE_PROGRESS_KEY}:${scope}`, JSON.stringify(values));
}

function safeJsonParse(value) {
  try {
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
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
        "content-type": "application/json"
      }
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

async function initializeLiveEdition() {
  const page = document.body?.dataset.page || "";
  const metaPromise = fetchSiteMeta();

  if (page === "home" || page === "latest") {
    const gridId = page === "home" ? "home-latest-grid" : "archive-grid";
    const toolbarId = page === "home" ? "home-filter-toolbar" : "archive-filter-toolbar";
    const summaryId = page === "home" ? "home-latest-summary" : "archive-summary";
    const limit = storyCountForGrid(gridId, page === "home" ? 18 : 96);
    const latest = await fetchLatestStories(limit);

    if (latest?.generatedAt) {
      applyGeneratedAt(latest.generatedAt);
    }
    if (Array.isArray(latest?.stories) && latest.stories.length) {
      renderBreakingTicker(latest.stories.slice(0, 16));
      renderLatestGrid(gridId, toolbarId, summaryId, latest.stories);
    }
  } else {
    const latest = await fetchLatestStories(16);
    if (latest?.generatedAt) {
      applyGeneratedAt(latest.generatedAt);
    }
    if (Array.isArray(latest?.stories) && latest.stories.length) {
      renderBreakingTicker(latest.stories);
    }
  }

  const meta = await metaPromise;
  if (meta?.generatedAt) {
    applyGeneratedAt(meta.generatedAt);
  }
}

async function fetchSiteMeta() {
  try {
    const response = await fetch(LOCAL_META_ENDPOINT, {
      cache: "no-store"
    });
    if (!response.ok) {
      return null;
    }

    const payload = await response.json();
    return payload?.ok ? payload : null;
  } catch {
    return null;
  }
}

async function fetchLatestStories(limit) {
  try {
    const response = await fetch(`${LOCAL_LATEST_ENDPOINT}?limit=${encodeURIComponent(limit)}`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return null;
    }

    const payload = await response.json();
    return payload?.ok ? payload : null;
  } catch {
    return null;
  }
}

function applyGeneratedAt(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return;
  }

  const stamp = formatGeneratedTimestamp(date);
  document.querySelectorAll("[data-generated-at]").forEach((node) => {
    node.textContent = stamp;
  });

  const editionStamp = document.querySelector("[data-edition-stamp]");
  if (editionStamp) {
    editionStamp.textContent = formatEditionDate(date);
  }
}

function storyCountForGrid(gridId, fallback) {
  const grid = document.getElementById(gridId);
  if (!grid) {
    return fallback;
  }

  return Math.max(grid.children.length || 0, fallback);
}

function renderBreakingTicker(stories) {
  const track = document.getElementById("breaking-ticker-track");
  if (!track || !stories.length) {
    return;
  }

  track.innerHTML = stories
    .map((story, index) => {
      const divider = index === stories.length - 1
        ? ""
        : '<span class="ticker-divider" aria-hidden="true">•</span>';

      return `
        <a class="ticker-item" href="${safeUrlOrPath(story.link)}" target="_blank" rel="noreferrer noopener">
          <span>${escapeHtml(story.title || "Latest headline")}</span>
        </a>
        ${divider}
      `;
    })
    .join("");
}

function renderLatestGrid(gridId, toolbarId, summaryId, stories) {
  const grid = document.getElementById(gridId);
  if (!grid || !stories.length) {
    return;
  }

  grid.innerHTML = stories.map((story) => storyCardMarkup(story)).join("");

  const toolbar = document.getElementById(toolbarId);
  const summary = document.getElementById(summaryId);
  if (!toolbar || !summary) {
    return;
  }

  const activeButton = toolbar.querySelector('[aria-pressed="true"]') || toolbar.querySelector('[data-filter-key="all"]');
  applyToolbarFilter(toolbar, grid, summary, activeButton?.dataset.filterKey || "all");
}

function storyCardMarkup(story) {
  const headline = escapeHtml(story.title || "Latest headline");
  const summary = escapeHtml(trimSummary(story.summary || ""));
  const sectionLabel = escapeHtml(story.section || "Latest");
  const sourceLabel = escapeHtml(story.source || "Source");
  const sectionHref = story.section_key ? `/sections/${encodeURIComponent(story.section_key)}/` : "#";
  const sourceHref = story.source_key ? `/sources/${encodeURIComponent(story.source_key)}/` : "#";
  const timestamp = formatGeneratedTimestamp(story.timestamp);
  const recency = recencyBadge(story.timestamp);

  return `
    <article class="story-card" data-section-key="${escapeHtml(story.section_key || "latest")}">
      <div class="story-meta">
        <a class="story-tag" href="${safeUrlOrPath(sectionHref)}">${sectionLabel}</a>
        <a class="story-source" href="${safeUrlOrPath(sourceHref)}">${sourceLabel}</a>
        <span class="story-time">${escapeHtml(timestamp)}</span>
        ${recency}
      </div>

      <h3><a class="story-headline-link" href="${safeUrlOrPath(story.link)}" target="_blank" rel="noreferrer noopener">${headline}</a></h3>
      <p>${summary}</p>

      <div class="story-actions">
        <a class="story-source-link" href="${safeUrlOrPath(story.link)}" target="_blank" rel="noreferrer noopener">Read original article</a>
        <a class="story-link" href="${safeUrlOrPath(sourceHref)}">Source page</a>
      </div>
    </article>
  `;
}

function trimSummary(value) {
  const cleaned = String(value || "").replace(/\s+/g, " ").trim();
  if (!cleaned) {
    return "Open the original report for the latest details.";
  }
  if (cleaned.length <= 220) {
    return cleaned;
  }
  return `${cleaned.slice(0, 217).trimEnd()}...`;
}

function formatGeneratedTimestamp(value) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Recently updated";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(date);
}

function formatEditionDate(value) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Latest Edition";
  }

  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric"
  }).format(date);
}

function recencyBadge(timestamp) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const deltaMinutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));
  if (deltaMinutes <= 10) {
    return '<span class="story-recency story-recency-hot">Just in</span>';
  }
  if (deltaMinutes < 60) {
    return `<span class="story-recency story-recency-hot">${deltaMinutes} min ago</span>`;
  }

  const deltaHours = Math.round(deltaMinutes / 60);
  if (deltaHours <= 2) {
    return `<span class="story-recency story-recency-warm">${deltaHours} hr ago</span>`;
  }
  if (deltaHours <= 6) {
    return `<span class="story-recency story-recency-cool">${deltaHours} hr ago</span>`;
  }

  return '<span class="story-recency story-recency-cool">Earlier</span>';
}

async function initializeUtilitySurfaces() {
  const page = document.body?.dataset.page || "";
  const tasks = [];

  if (page === "home") {
    tasks.push(initializeHomeUtilityCards());
  }
  if (page === "weather") {
    tasks.push(initializeWeatherPage());
  }
  if (page === "sports") {
    tasks.push(initializeSportsPage());
  }
  if (page === "markets") {
    tasks.push(initializeMarketsPage());
  }

  await Promise.all(tasks);
}

async function fetchEndpoint(endpoint) {
  const response = await fetch(endpoint, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`Request failed for ${endpoint}`);
  }

  const payload = await response.json();
  if (!payload?.ok) {
    throw new Error(`Invalid payload from ${endpoint}`);
  }
  return payload;
}

async function initializeHomeUtilityCards() {
  const [weather, sports, markets] = await Promise.all([
    fetchEndpoint(LOCAL_WEATHER_ENDPOINT).catch(() => null),
    fetchEndpoint(LOCAL_SPORTS_ENDPOINT).catch(() => null),
    fetchEndpoint(LOCAL_MARKETS_ENDPOINT).catch(() => null)
  ]);

  if (weather) {
    renderHomeWeatherCard(weather);
  }
  if (sports) {
    renderHomeSportsCard(sports);
  }
  if (markets) {
    renderHomeMarketsCard(markets);
  }
}

async function initializeWeatherPage() {
  const payload = await fetchEndpoint(LOCAL_WEATHER_ENDPOINT);
  renderWeatherPage(payload);
}

async function initializeSportsPage() {
  const payload = await fetchEndpoint(LOCAL_SPORTS_ENDPOINT);
  renderSportsPage(payload);
}

async function initializeMarketsPage() {
  const payload = await fetchEndpoint(LOCAL_MARKETS_ENDPOINT);
  renderMarketsPage(payload);
}

function renderHomeWeatherCard(payload) {
  const card = document.getElementById("home-weather-card");
  if (!card) {
    return;
  }

  const current = payload.current;
  const nextPeriods = (payload.forecast || []).slice(0, 3);
  if (!current) {
    return;
  }

  card.innerHTML = `
    <p class="panel-label">Weather</p>
    <h3>${escapeHtml(payload.location?.shortLabel || "Local forecast")}</h3>
    <p class="utility-value">${escapeHtml(String(current.temperature ?? "--"))}&deg;${escapeHtml(current.temperatureUnit || "F")}</p>
    <p class="utility-copy">${escapeHtml(current.shortForecast || "Forecast unavailable.")}</p>
    <div class="mini-forecast">
      ${nextPeriods.map((period) => `
        <article>
          <strong>${escapeHtml(period.name || "")}</strong>
          <span>${escapeHtml(String(period.temperature ?? "--"))}&deg;${escapeHtml(period.temperatureUnit || "F")}</span>
        </article>
      `).join("")}
    </div>
    <div class="story-actions">
      <a class="story-link" href="/weather/">Open weather desk</a>
    </div>
  `;
}

function renderHomeSportsCard(payload) {
  const card = document.getElementById("home-sports-card");
  if (!card) {
    return;
  }

  const games = flattenGames(payload.scoreboards || []).slice(0, 3);
  if (!games.length) {
    return;
  }

  card.innerHTML = `
    <p class="panel-label">Sports</p>
    <h3>Live boards and tonight&apos;s best windows</h3>
    <div class="mini-score-list">
      ${games.map((game) => `
        <article>
          <strong>${escapeHtml(game.league)}</strong>
          <span>${escapeHtml(shortGameLabel(game))}</span>
          <small>${escapeHtml(game.status || "")}</small>
        </article>
      `).join("")}
    </div>
    <div class="story-actions">
      <a class="story-link" href="/sports/">Open sports desk</a>
    </div>
  `;
}

function renderHomeMarketsCard(payload) {
  const card = document.getElementById("home-markets-card");
  if (!card) {
    return;
  }

  const watchlist = (payload.watchlist || []).slice(0, 4);
  if (!watchlist.length) {
    return;
  }

  card.innerHTML = `
    <p class="panel-label">Markets</p>
    <h3>Indices and crypto in one scan</h3>
    <div class="mini-market-list">
      ${watchlist.map((quote) => `
        <article>
          <strong>${escapeHtml(quote.symbol || "")}</strong>
          <span>${escapeHtml(quote.valueDisplay || "Unavailable")}</span>
          <small class="${quoteToneClass(quote)}">${escapeHtml(quote.changePercentDisplay || quote.changeDisplay || "Flat")}</small>
        </article>
      `).join("")}
    </div>
    <div class="story-actions">
      <a class="story-link" href="/markets/">Open markets desk</a>
    </div>
  `;
}

function renderWeatherPage(payload) {
  const currentNode = document.getElementById("weather-current");
  const forecastNode = document.getElementById("weather-forecast-grid");
  const alertsNode = document.getElementById("weather-alerts");
  if (!currentNode || !forecastNode || !alertsNode) {
    return;
  }

  const current = payload.current;
  if (current) {
    currentNode.innerHTML = `
      <div class="utility-reading">
        <p class="utility-value">${escapeHtml(String(current.temperature ?? "--"))}&deg;${escapeHtml(current.temperatureUnit || "F")}</p>
        <p class="utility-copy">${escapeHtml(current.shortForecast || "")}</p>
        <p class="utility-subcopy">${escapeHtml(current.windSpeed || "")} ${escapeHtml(current.windDirection || "")}</p>
      </div>
    `;
  }

  forecastNode.innerHTML = (payload.forecast || []).map((period) => `
    <article class="forecast-card">
      <strong>${escapeHtml(period.name || "")}</strong>
      <span>${escapeHtml(String(period.temperature ?? "--"))}&deg;${escapeHtml(period.temperatureUnit || "F")}</span>
      <p>${escapeHtml(period.shortForecast || "")}</p>
    </article>
  `).join("");

  const alerts = payload.alerts || [];
  alertsNode.innerHTML = alerts.length
    ? `<div class="alert-list">${alerts.map((alert) => `
        <article class="alert-card">
          <strong>${escapeHtml(alert.event || "Alert")}</strong>
          <p>${escapeHtml(alert.headline || "")}</p>
          <small>${escapeHtml([alert.severity, alert.urgency].filter(Boolean).join(" • "))}</small>
        </article>
      `).join("")}</div>`
    : '<p class="utility-copy">No active alerts for home right now.</p>';
}

function renderSportsPage(payload) {
  const scoreboardsNode = document.getElementById("sports-scoreboards");
  if (!scoreboardsNode) {
    return;
  }

  const boards = payload.scoreboards || [];
  if (!boards.length) {
    scoreboardsNode.innerHTML = '<p class="utility-copy">No live scoreboards are available right now.</p>';
    return;
  }

  scoreboardsNode.innerHTML = boards.map((board) => `
    <section class="scoreboard-section">
      <div class="section-heading section-heading-compact">
        <div>
          <p class="eyebrow">${escapeHtml(board.league)}</p>
          <h3>${escapeHtml(board.league)} scoreboard</h3>
        </div>
      </div>
      <div class="scoreboard-grid">
        ${(board.games || []).map((game) => `
          <article class="score-card">
            <div class="score-card-top">
              <strong>${escapeHtml(shortGameLabel(game))}</strong>
              <span>${escapeHtml(game.status || "")}</span>
            </div>
            <div class="team-stack">
              ${(game.competitors || []).map((team) => `
                <div class="team-row">
                  <span>${escapeHtml(team.abbreviation || team.name || "")}</span>
                  <strong>${escapeHtml(team.score || "0")}</strong>
                </div>
              `).join("")}
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `).join("");
}

function renderMarketsPage(payload) {
  const watchlistNode = document.getElementById("markets-watchlist");
  if (!watchlistNode) {
    return;
  }

  const watchlist = payload.watchlist || [];
  if (!watchlist.length) {
    watchlistNode.innerHTML = '<p class="utility-copy">Market data is temporarily unavailable.</p>';
    return;
  }

  watchlistNode.innerHTML = `
    <div class="watchlist-grid">
      ${watchlist.map((quote) => `
        <article class="market-card">
          <p class="panel-label">${escapeHtml(quote.symbol || "")}</p>
          <h3>${escapeHtml(quote.valueDisplay || "Unavailable")}</h3>
          <p class="market-move ${quoteToneClass(quote)}">${escapeHtml(quote.changePercentDisplay || quote.changeDisplay || "Flat")}</p>
          <small>${escapeHtml(quote.asOf || "")}</small>
        </article>
      `).join("")}
    </div>
  `;
}

function flattenGames(scoreboards) {
  return scoreboards.flatMap((board) =>
    (board.games || []).map((game) => ({
      ...game,
      league: board.league
    }))
  );
}

function shortGameLabel(game) {
  const competitors = game.competitors || [];
  if (competitors.length < 2) {
    return game.name || "Game";
  }
  return `${competitors[1].abbreviation || competitors[1].name} @ ${competitors[0].abbreviation || competitors[0].name}`;
}

function quoteToneClass(quote) {
  const value = typeof quote.changePercent === "number"
    ? quote.changePercent
    : parseFloat(String(quote.changePercentDisplay || quote.changeDisplay || "0").replace(/[^\d.-]/g, ""));

  if (Number.isNaN(value) || value === 0) {
    return "utility-flat";
  }
  return value > 0 ? "utility-up" : "utility-down";
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
      summaryNode.textContent = "Type a topic, person, company, place, source, or journal idea to pull up matching pages.";
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
    summaryNode.textContent = `Showing ${ranked.length} result${ranked.length === 1 ? "" : "s"} across briefs, journal posts, topics, sources, and coverage pages.`;
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
