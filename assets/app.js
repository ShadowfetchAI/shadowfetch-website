const siteConfig = {
  brandName: "ShadowFetch News",
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

const FEED_PROXY = "https://api.allorigins.win/get?url=";
const FEED_CONFIG_URL = "/assets/data/feed-config.json";
const FEED_DATA_URL = "/assets/data/feed.json";

const appState = {
  feedConfig: null,
  payload: null,
  filters: {
    home: "all",
    archive: "all"
  }
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootSite);
} else {
  bootSite();
}

function bootSite() {
  try {
    applySocialLinks();
  } catch {
    // Keep the static fallback links if enhancement fails.
  }

  initializeVisitorCounter().catch(() => {
    setVisitCount("Unavailable");
  });

  initializeSite().catch(handleFeedFailure);
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

  Object.entries(siteConfig.social).forEach(([key, config]) => {
    document.querySelectorAll(`[data-social-url="${key}"]`).forEach((node) => {
      node.textContent = readableUrl(config.url);
    });
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

  try {
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
  } catch {
    setVisitCount("Unavailable");
  }
}

function setVisitCount(value) {
  document.querySelectorAll("[data-visit-count]").forEach((node) => {
    node.textContent = value;
  });
}

async function initializeSite() {
  appState.feedConfig = await loadFeedConfig();
  renderGlobalStats(appState.feedConfig);

  const prepared = await loadPreparedFeedData();
  if (prepared) {
    appState.payload = normalizePayload(prepared);
    renderAll("Prepared snapshot");
    return;
  }

  const live = await loadFeedsFromNetwork(appState.feedConfig);
  appState.payload = normalizePayload(live);
  renderAll("Live fallback");
}

async function loadFeedConfig() {
  const response = await fetch(FEED_CONFIG_URL, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Could not load feed configuration");
  }

  return response.json();
}

async function loadPreparedFeedData() {
  const response = await fetch(FEED_DATA_URL, { cache: "no-store" });
  if (!response.ok) {
    return null;
  }

  const payload = await response.json();
  return payload && Array.isArray(payload.sections) ? payload : null;
}

async function loadFeedsFromNetwork(config) {
  const results = await Promise.all(
    config.sections.map(async (section) => {
      const feeds = await Promise.allSettled(section.sources.map((source) => fetchFeed(source, section, config)));
      const stories = dedupeStories(
        feeds.filter((result) => result.status === "fulfilled").flatMap((result) => result.value)
      ).sort(sortStoriesDesc);

      return {
        key: section.key,
        title: section.title,
        short_label: section.short_label,
        description: section.description,
        stories: stories.slice(0, section.story_limit || config.per_section_limit || 8),
        successful_sources: feeds.filter((result) => result.status === "fulfilled").length,
        total_sources: feeds.length
      };
    })
  );

  const latest = dedupeStories(results.flatMap((section) => section.stories))
    .sort(sortStoriesDesc)
    .slice(0, config.latest_limit || 30);

  return {
    generated_at: new Date().toISOString(),
    successful_sources: results.reduce((total, section) => total + section.successful_sources, 0),
    total_sources: results.reduce((total, section) => total + section.total_sources, 0),
    featured: latest.slice(0, config.featured_limit || 3),
    latest,
    sections: results
  };
}

async function fetchFeed(source, section, config) {
  const response = await fetch(`${FEED_PROXY}${encodeURIComponent(source.url)}`);
  if (!response.ok) {
    throw new Error(`Feed request failed for ${source.name}`);
  }

  const payload = await response.json();
  const xml = new window.DOMParser().parseFromString(payload.contents, "text/xml");
  const entries = [...xml.querySelectorAll("item"), ...xml.querySelectorAll("entry")]
    .slice(0, source.item_limit || config.source_item_limit || 10);

  return entries.map((entry) => {
    const linkNode = entry.querySelector("link");
    const rawLink = linkNode ? linkNode.getAttribute("href") || linkNode.textContent : "";
    const summary =
      readText(entry, ["description", "content", "summary", "content\\:encoded"]) ||
      "Open the original source for the full story.";
    const published = readText(entry, ["pubDate", "published", "updated", "dc\\:date", "date"]) || new Date().toISOString();
    const timestamp = parseFeedTimestamp(published);

    return {
      title: readText(entry, ["title"]) || "Untitled story",
      link: safeUrl(rawLink.trim()),
      summary: summarize(stripHtml(summary)),
      source: source.name,
      section: section.title,
      section_key: section.key,
      timestamp
    };
  }).filter((story) => story.link !== "#");
}

function normalizePayload(payload) {
  const latest = Array.isArray(payload.latest)
    ? dedupeStories(payload.latest).sort(sortStoriesDesc)
    : dedupeStories((payload.sections || []).flatMap((section) => section.stories || [])).sort(sortStoriesDesc);

  return {
    generated_at: payload.generated_at || new Date().toISOString(),
    successful_sources: payload.successful_sources || 0,
    total_sources: payload.total_sources || 0,
    featured: Array.isArray(payload.featured) && payload.featured.length
      ? payload.featured
      : latest.slice(0, (appState.feedConfig && appState.feedConfig.featured_limit) || 3),
    latest,
    sections: (payload.sections || []).map((section) => ({
      ...section,
      stories: (section.stories || []).sort(sortStoriesDesc)
    }))
  };
}

function renderAll(modeLabel) {
  renderHeaderStatus(modeLabel);
  renderBreakingTicker();
  renderHomePage();
  renderLatestPage();
  renderSectionsPage();
  renderSectionDetailPage();
  renderAboutPage();
}

function renderHeaderStatus(modeLabel) {
  const generatedText = `${formatStoryTime(appState.payload.generated_at)} • ${modeLabel}`;
  document.querySelectorAll("[data-generated-at]").forEach((node) => {
    node.textContent = generatedText;
  });
}

function renderGlobalStats(config) {
  const sectionCountNode = document.getElementById("hero-section-count");
  const sourceCountNode = document.getElementById("hero-source-count");

  if (sectionCountNode) {
    sectionCountNode.textContent = String(config.sections.length);
  }

  if (sourceCountNode) {
    sourceCountNode.textContent = String(config.sections.reduce((total, section) => total + section.sources.length, 0));
  }
}

function renderBreakingTicker() {
  const track = document.getElementById("breaking-ticker-track");
  if (!track) {
    return;
  }

  const limit = (appState.feedConfig && appState.feedConfig.breaking_limit) || 12;
  const stories = appState.payload.latest.slice(0, limit);
  if (!stories.length) {
    track.innerHTML = '<span class="ticker-placeholder">Breaking headlines are temporarily unavailable.</span>';
    return;
  }

  const items = stories.map((story) => `
    <a class="ticker-item" href="${story.link}" target="_blank" rel="noreferrer noopener">
      <span>${escapeHtml(story.title)}</span>
    </a>
  `);
  const divider = '\n<span class="ticker-divider" aria-hidden="true">•</span>\n';
  const content = items.join(divider);

  track.innerHTML = `${content}${content}`;
}

function renderHomePage() {
  renderFeaturedGrid();
  renderHomeSectionGrid();
  renderStoryCollection({
    toolbarId: "home-filter-toolbar",
    summaryId: "home-latest-summary",
    gridId: "home-latest-grid",
    stateKey: "home",
    storyLimit: (appState.feedConfig && appState.feedConfig.home_latest_limit) || 12
  });
}

function renderFeaturedGrid() {
  const container = document.getElementById("featured-grid");
  if (!container) {
    return;
  }

  const featured = appState.payload.featured.slice(0, 3);
  if (!featured.length) {
    container.innerHTML = '<p class="empty-card">Featured stories are not available yet.</p>';
    return;
  }

  const [lead, ...sideStories] = featured;
  const sideMarkup = sideStories.map((story) => `
    <a class="featured-side" href="${story.link}" target="_blank" rel="noreferrer noopener">
      ${storyMetaMarkup(story)}
      <h3>${escapeHtml(story.title)}</h3>
      <p>${escapeHtml(story.summary)}</p>
    </a>
  `).join("");

  container.innerHTML = `
    <a class="featured-main" href="${lead.link}" target="_blank" rel="noreferrer noopener">
      ${storyMetaMarkup(lead)}
      <h2>${escapeHtml(lead.title)}</h2>
      <p>${escapeHtml(lead.summary)}</p>
      <span class="story-link">Read the full source</span>
    </a>
    <div class="featured-side-grid">
      ${sideMarkup}
    </div>
  `;
}

function renderHomeSectionGrid() {
  const container = document.getElementById("home-section-grid");
  if (!container) {
    return;
  }

  const storyLimit = (appState.feedConfig && appState.feedConfig.home_section_story_limit) || 3;
  container.innerHTML = appState.feedConfig.sections.map((sectionConfig) => {
    const section = findSection(sectionConfig.key);
    const stories = section ? section.stories.slice(0, storyLimit) : [];
    const storyMarkup = stories.length
      ? stories.map((story) => compactStoryMarkup(story)).join("")
      : '<p class="empty-card">No stories available for this section right now.</p>';

    return `
      <article class="section-card" id="section-${sectionConfig.key}">
        <p class="panel-label">${escapeHtml(sectionConfig.short_label)}</p>
        <h3>${escapeHtml(sectionConfig.title)}</h3>
        <p>${escapeHtml(sectionConfig.description)}</p>
        <div class="story-list">${storyMarkup}</div>
        <a class="story-link" href="/sections/${sectionConfig.key}/">Open section</a>
      </article>
    `;
  }).join("");
}

function renderLatestPage() {
  renderStoryCollection({
    toolbarId: "archive-filter-toolbar",
    summaryId: "archive-summary",
    gridId: "archive-grid",
    stateKey: "archive",
    storyLimit: (appState.feedConfig && appState.feedConfig.latest_page_limit) || 36
  });
}

function renderStoryCollection({ toolbarId, summaryId, gridId, stateKey, storyLimit }) {
  const toolbar = document.getElementById(toolbarId);
  const summary = document.getElementById(summaryId);
  const grid = document.getElementById(gridId);

  if (!toolbar || !summary || !grid) {
    return;
  }

  buildFilterToolbar(toolbar, stateKey);

  const stories = filterStories(appState.payload.latest, appState.filters[stateKey]).slice(0, storyLimit);
  if (!stories.length) {
    summary.textContent = "No stories are available for this filter right now.";
    grid.innerHTML = '<p class="empty-card">The story collection is temporarily empty.</p>';
    return;
  }

  const label = getFilterLabel(appState.filters[stateKey]);
  summary.textContent = appState.filters[stateKey] === "all"
    ? `Showing ${stories.length} story${stories.length === 1 ? "" : "ies"} across every section in this view.`
    : `Showing ${stories.length} ${label.toLowerCase()} story${stories.length === 1 ? "" : "ies"} in this view.`;
  grid.innerHTML = stories.map((story) => storyCardMarkup(story)).join("");
}

function buildFilterToolbar(toolbar, stateKey) {
  const filters = [
    { key: "all", label: "All Stories" },
    ...appState.feedConfig.sections.map((section) => ({
      key: section.key,
      label: section.short_label || section.title
    }))
  ];

  toolbar.innerHTML = filters.map((filter) => `
    <button
      class="filter-pill"
      type="button"
      data-filter-key="${filter.key}"
      aria-pressed="${filter.key === appState.filters[stateKey] ? "true" : "false"}"
    >
      ${escapeHtml(filter.label)}
    </button>
  `).join("");

  toolbar.querySelectorAll("[data-filter-key]").forEach((button) => {
    button.addEventListener("click", () => {
      appState.filters[stateKey] = button.dataset.filterKey;
      renderStoryCollection({
        toolbarId: toolbar.id,
        summaryId: toolbar.nextElementSibling && toolbar.nextElementSibling.id,
        gridId: toolbar.nextElementSibling && toolbar.nextElementSibling.nextElementSibling && toolbar.nextElementSibling.nextElementSibling.id,
        stateKey,
        storyLimit: stateKey === "home"
          ? ((appState.feedConfig && appState.feedConfig.home_latest_limit) || 12)
          : ((appState.feedConfig && appState.feedConfig.latest_page_limit) || 36)
      });
    });
  });
}

function renderSectionsPage() {
  const container = document.getElementById("section-directory");
  if (!container) {
    return;
  }

  container.innerHTML = appState.feedConfig.sections.map((sectionConfig) => {
    const section = findSection(sectionConfig.key);
    const stories = section ? section.stories.slice(0, 4) : [];
    const sources = sectionConfig.sources.map((source) => `
      <a class="source-chip" href="${safeUrl(source.homepage || source.url)}" target="_blank" rel="noreferrer noopener">
        ${escapeHtml(source.name)}
      </a>
    `).join("");

    return `
      <article class="directory-card" id="section-${sectionConfig.key}">
        <p class="panel-label">${escapeHtml(sectionConfig.short_label)}</p>
        <h3>${escapeHtml(sectionConfig.title)}</h3>
        <p>${escapeHtml(sectionConfig.description)}</p>
        <div class="source-row">${sources}</div>
        <div class="story-list">
          ${stories.length ? stories.map((story) => compactStoryMarkup(story)).join("") : '<p class="empty-card">No stories available right now.</p>'}
        </div>
        <a class="story-link" href="/sections/${sectionConfig.key}/">Open ${escapeHtml(sectionConfig.short_label)} desk</a>
      </article>
    `;
  }).join("");
}

function renderSectionDetailPage() {
  const body = document.body;
  if (!body || body.dataset.page !== "section") {
    return;
  }

  const sectionKey = body.dataset.sectionKey;
  const sectionConfig = appState.feedConfig.sections.find((section) => section.key === sectionKey);
  const section = findSection(sectionKey);

  const titleNode = document.getElementById("section-detail-title");
  const descriptionNode = document.getElementById("section-detail-description");
  const summaryNode = document.getElementById("section-detail-summary");
  const sourceCountNode = document.getElementById("section-source-count");
  const storyCountNode = document.getElementById("section-story-count");
  const leadNode = document.getElementById("section-lead-story");
  const storiesNode = document.getElementById("section-story-grid");
  const sourcesNode = document.getElementById("section-source-row");

  if (!sectionConfig || !section || !titleNode || !descriptionNode || !summaryNode || !sourceCountNode || !storyCountNode || !leadNode || !storiesNode || !sourcesNode) {
    return;
  }

  titleNode.textContent = sectionConfig.title;
  descriptionNode.textContent = sectionConfig.description;
  summaryNode.textContent = `This desk currently tracks ${section.stories.length} prepared stories from ${section.successful_sources}/${section.total_sources} active sources.`;
  sourceCountNode.textContent = String(sectionConfig.sources.length);
  storyCountNode.textContent = String(section.stories.length);

  const [lead, ...rest] = section.stories;
  leadNode.innerHTML = lead
    ? `
      <a class="featured-main section-lead-card" href="${lead.link}" target="_blank" rel="noreferrer noopener">
        ${storyMetaMarkup(lead)}
        <h2>${escapeHtml(lead.title)}</h2>
        <p>${escapeHtml(lead.summary)}</p>
        <span class="story-link">Read the full source</span>
      </a>
    `
    : '<p class="empty-card">No lead story is available for this section right now.</p>';

  storiesNode.innerHTML = rest.length
    ? rest.map((story) => storyCardMarkup(story)).join("")
    : '<p class="empty-card">More section stories will appear here when the feed refreshes.</p>';

  sourcesNode.innerHTML = sectionConfig.sources.map((source) => `
    <a class="source-chip" href="${safeUrl(source.homepage || source.url)}" target="_blank" rel="noreferrer noopener">
      ${escapeHtml(source.name)}
    </a>
  `).join("");
}

function renderAboutPage() {
  const sourceWall = document.getElementById("source-wall");
  const sourceSummary = document.getElementById("source-summary");
  if (!sourceWall || !sourceSummary) {
    return;
  }

  const sourceCount = appState.feedConfig.sections.reduce((total, section) => total + section.sources.length, 0);
  sourceSummary.textContent = `The site currently tracks ${appState.feedConfig.sections.length} sections across ${sourceCount} feed sources, mixing official institutional feeds with long-running publisher feeds.`;

  const cards = [];
  appState.feedConfig.sections.forEach((section) => {
    section.sources.forEach((source) => {
      cards.push(`
        <a class="source-card" href="${safeUrl(source.homepage || source.url)}" target="_blank" rel="noreferrer noopener">
          <span class="source-label">${escapeHtml(section.title)}</span>
          <strong>${escapeHtml(source.name)}</strong>
        </a>
      `);
    });
  });

  sourceWall.innerHTML = cards.join("");
}

function filterStories(stories, filterKey) {
  if (filterKey === "all") {
    return stories;
  }

  return stories.filter((story) => story.section_key === filterKey);
}

function getFilterLabel(filterKey) {
  if (filterKey === "all") {
    return "All stories";
  }

  const section = appState.feedConfig.sections.find((candidate) => candidate.key === filterKey);
  return section ? section.title : "Filtered";
}

function findSection(key) {
  return appState.payload.sections.find((section) => section.key === key);
}

function storyCardMarkup(story) {
  return `
    <a class="story-card" href="${story.link}" target="_blank" rel="noreferrer noopener">
      ${storyMetaMarkup(story)}
      <h3>${escapeHtml(story.title)}</h3>
      <p>${escapeHtml(story.summary)}</p>
    </a>
  `;
}

function compactStoryMarkup(story) {
  return `
    <a class="story-compact" href="${story.link}" target="_blank" rel="noreferrer noopener">
      <div class="story-meta">
        <span class="story-source">${escapeHtml(story.source)}</span>
        <span class="story-time">${formatStoryTime(story.timestamp)}</span>
      </div>
      <h3>${escapeHtml(story.title)}</h3>
      <p>${escapeHtml(story.summary)}</p>
    </a>
  `;
}

function storyMetaMarkup(story) {
  return `
    <div class="story-meta">
      <span class="story-tag">${escapeHtml(story.section)}</span>
      <span class="story-source">${escapeHtml(story.source)}</span>
      <span class="story-time">${formatStoryTime(story.timestamp)}</span>
    </div>
  `;
}

function handleFeedFailure() {
  document.querySelectorAll("[data-generated-at]").forEach((node) => {
    if (!node.textContent.trim()) {
      node.textContent = "Feed sync unavailable";
    }
  });

  const track = document.getElementById("breaking-ticker-track");
  if (track && !track.querySelector(".ticker-item")) {
    track.innerHTML = '<span class="ticker-placeholder">Breaking headlines are temporarily unavailable.</span>';
  }

  [
    "home-latest-summary",
    "archive-summary",
    "source-summary"
  ].forEach((id) => {
    const node = document.getElementById(id);
    if (node && !node.textContent.trim()) {
      node.textContent = "Feed data is temporarily unavailable.";
    }
  });
}

function readText(root, selectors) {
  for (const selector of selectors) {
    const node = root.querySelector(selector);
    if (node && node.textContent) {
      return node.textContent.trim();
    }
  }

  return "";
}

function stripHtml(value) {
  const template = document.createElement("template");
  template.innerHTML = value;
  return template.content.textContent ? template.content.textContent.trim() : "";
}

function summarize(text) {
  if (!text) {
    return "Open the original source for the full story.";
  }

  if (text.length <= 180) {
    return text;
  }

  return `${text.slice(0, 177).trim()}...`;
}

function dedupeStories(stories) {
  const seen = new Set();
  return stories.filter((story) => {
    const key = story.link || `${story.source}-${story.title}`;
    if (seen.has(key)) {
      return false;
    }

    seen.add(key);
    return true;
  });
}

function sortStoriesDesc(left, right) {
  return new Date(right.timestamp) - new Date(left.timestamp);
}

function parseFeedTimestamp(value) {
  const native = Date.parse(value);
  if (!Number.isNaN(native)) {
    return new Date(native).toISOString();
  }

  const custom = value.match(/^[A-Za-z]{3},\s*(\d{2})\/(\d{2})\/(\d{4})\s*-\s*(\d{2}):(\d{2})/);
  if (custom) {
    const [, month, day, year, hour, minute] = custom;
    return new Date(Date.UTC(Number(year), Number(month) - 1, Number(day), Number(hour), Number(minute))).toISOString();
  }

  return new Date().toISOString();
}

function formatStoryTime(timestamp) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(timestamp));
}

function formatInteger(value) {
  return new Intl.NumberFormat("en-US").format(Number(value) || 0);
}

function readableUrl(url) {
  return url.replace(/^https?:\/\//, "");
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
    // Ignore storage failures and keep the in-memory page working.
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

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
