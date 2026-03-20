const siteConfig = {
  brandName: "ShadowFetch News",
  social: {
    x: {
      label: "Follow on X",
      url: "https://x.com/MrBobCorbin"
    },
    bluesky: {
      label: "Follow on Bluesky",
      url: "https://bsky.app/profile/mrbobcorbin.bsky.social"
    }
  },
  sections: [
    {
      key: "linux",
      title: "Linux & Distros",
      containerId: "beat-linux",
      sources: [
        { name: "OMG! Ubuntu", url: "https://www.omgubuntu.co.uk/feed" },
        { name: "9to5Linux", url: "https://9to5linux.com/feed" },
        { name: "Phoronix", url: "https://www.phoronix.com/rss.php" }
      ]
    },
    {
      key: "open-source",
      title: "Open Source & Dev",
      containerId: "beat-open-source",
      sources: [
        { name: "It's FOSS", url: "https://itsfoss.com/feed/" },
        { name: "Hacker News", url: "https://hnrss.org/frontpage" },
        { name: "Ars Technica", url: "https://feeds.arstechnica.com/arstechnica/index" }
      ]
    },
    {
      key: "privacy",
      title: "Privacy & Security",
      containerId: "beat-privacy",
      sources: [
        { name: "Krebs on Security", url: "https://krebsonsecurity.com/feed/" },
        { name: "Schneier on Security", url: "https://www.schneier.com/feed/atom/" },
        { name: "The Register", url: "https://www.theregister.com/headlines.atom" }
      ]
    }
  ]
};

const FEED_PROXY = "https://api.allorigins.win/get?url=";

document.addEventListener("DOMContentLoaded", () => {
  applySocialLinks();
  loadFeeds().catch(handleFeedFailure);
});

function applySocialLinks() {
  const socialTargets = [
    {
      config: siteConfig.social.x,
      anchorId: "social-x",
      urlTextId: "social-x-url",
      copyId: "social-x-copy"
    },
    {
      config: siteConfig.social.bluesky,
      anchorId: "social-bluesky",
      urlTextId: "social-bluesky-url",
      copyId: "social-bluesky-copy"
    }
  ];

  socialTargets.forEach(({ config, anchorId, urlTextId, copyId }) => {
    const anchor = document.getElementById(anchorId);
    const urlText = document.getElementById(urlTextId);
    const copy = document.getElementById(copyId);
    const isPlaceholder = isPlaceholderUrl(config.url);

    anchor.href = isPlaceholder ? "#follow" : safeUrl(config.url);
    urlText.textContent = readableUrl(config.url);

    if (isPlaceholder) {
      anchor.removeAttribute("target");
      anchor.removeAttribute("rel");
      copy.textContent = "Add your real profile URL in assets/app.js so readers can find you here.";
    }
  });
}

async function loadFeeds() {
  const statusNode = document.getElementById("feed-status");
  const updatedNode = document.getElementById("last-updated");

  const results = await Promise.all(
    siteConfig.sections.map(async (section) => {
      const feeds = await Promise.allSettled(section.sources.map((source) => fetchFeed(source, section.title)));
      const successfulStories = feeds
        .filter((result) => result.status === "fulfilled")
        .flatMap((result) => result.value);

      return {
        ...section,
        stories: dedupeStories(successfulStories)
          .sort((left, right) => right.timestamp - left.timestamp)
          .slice(0, 6),
        successfulSources: feeds.filter((result) => result.status === "fulfilled").length,
        totalSources: feeds.length
      };
    })
  );

  const allStories = dedupeStories(results.flatMap((section) => section.stories))
    .sort((left, right) => right.timestamp - left.timestamp);

  renderLeadStory(allStories[0]);
  renderSectionLists(results);
  renderLatestStories(allStories.slice(0, 8));

  const successfulSources = results.reduce((total, section) => total + section.successfulSources, 0);
  const totalSources = results.reduce((total, section) => total + section.totalSources, 0);
  statusNode.textContent = `${successfulSources}/${totalSources} sources online`;
  updatedNode.textContent = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date());
}

async function fetchFeed(source, sectionTitle) {
  const response = await fetch(`${FEED_PROXY}${encodeURIComponent(source.url)}`);
  if (!response.ok) {
    throw new Error(`Feed request failed for ${source.name}`);
  }

  const payload = await response.json();
  const xml = new window.DOMParser().parseFromString(payload.contents, "text/xml");
  const entries = [...xml.querySelectorAll("item"), ...xml.querySelectorAll("entry")].slice(0, 6);

  return entries.map((entry) => {
    const linkNode = entry.querySelector("link");
    const rawLink = linkNode ? linkNode.getAttribute("href") || linkNode.textContent : "";
    const summary =
      readText(entry, ["description", "content", "summary", "content\\:encoded"]) ||
      "Open the original source for the full story.";
    const published =
      readText(entry, ["pubDate", "published", "updated"]) || new Date().toISOString();
    const timestamp = Date.parse(published) || Date.now();

    return {
      title: readText(entry, ["title"]) || "Untitled story",
      link: safeUrl(rawLink.trim()),
      summary: summarize(stripHtml(summary)),
      source: source.name,
      section: sectionTitle,
      timestamp
    };
  }).filter((story) => story.link !== "#");
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

  if (text.length <= 155) {
    return text;
  }

  return `${text.slice(0, 152).trim()}...`;
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

function renderLeadStory(story) {
  const container = document.getElementById("lead-story");

  if (!story) {
    container.innerHTML = `
      <p class="empty-copy">
        Live feeds are temporarily quiet. The page shell is ready; the next step is improving feed
        reliability with scheduled builds or a small backend.
      </p>
    `;
    return;
  }

  container.innerHTML = `
    <div class="story-meta">
      <span class="story-tag">${story.section}</span>
      <span class="story-source">${story.source}</span>
      <span class="story-time">${formatStoryTime(story.timestamp)}</span>
    </div>
    <h3>${escapeHtml(story.title)}</h3>
    <p>${escapeHtml(story.summary)}</p>
    <a class="story-cta" href="${story.link}" target="_blank" rel="noreferrer noopener">
      Read the original story
    </a>
  `;
}

function renderSectionLists(sections) {
  sections.forEach((section) => {
    const container = document.getElementById(section.containerId);

    if (!section.stories.length) {
      container.innerHTML = `
        <p class="empty-copy">
          This beat is ready, but the live sources are not responding right now. GitHub Pages can
          still host the site well; the stronger next step is scheduled feed generation.
        </p>
      `;
      return;
    }

    container.innerHTML = section.stories.slice(0, 3).map((story) => `
      <a class="story-link" href="${story.link}" target="_blank" rel="noreferrer noopener">
        <div class="story-meta">
          <span class="story-source">${story.source}</span>
          <span class="story-time">${formatStoryTime(story.timestamp)}</span>
        </div>
        <h3>${escapeHtml(story.title)}</h3>
        <p>${escapeHtml(story.summary)}</p>
      </a>
    `).join("");
  });
}

function renderLatestStories(stories) {
  const container = document.getElementById("latest-stories");

  if (!stories.length) {
    container.innerHTML = `
      <p class="empty-copy">
        The live wire will appear here once feed requests succeed. Until then, the design and
        structure are ready for real publishing.
      </p>
    `;
    return;
  }

  container.innerHTML = stories.map((story) => `
    <a class="latest-card" href="${story.link}" target="_blank" rel="noreferrer noopener">
      <div class="story-meta">
        <span class="story-tag">${story.section}</span>
        <span class="story-source">${story.source}</span>
      </div>
      <h3>${escapeHtml(story.title)}</h3>
      <p>${escapeHtml(story.summary)}</p>
      <div class="story-meta">
        <span class="story-time">${formatStoryTime(story.timestamp)}</span>
      </div>
    </a>
  `).join("");
}

function formatStoryTime(timestamp) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(timestamp));
}

function readableUrl(url) {
  return url.replace(/^https?:\/\//, "");
}

function safeUrl(url) {
  try {
    const parsed = new URL(url);
    return /^https?:$/i.test(parsed.protocol) ? parsed.toString() : "#";
  } catch {
    return "#";
  }
}

function isPlaceholderUrl(url) {
  return /your-handle/i.test(url);
}

function handleFeedFailure() {
  const statusNode = document.getElementById("feed-status");
  const updatedNode = document.getElementById("last-updated");

  if (statusNode) {
    statusNode.textContent = "Feed sync unavailable";
  }

  if (updatedNode) {
    updatedNode.textContent = "Refresh in a moment";
  }

  renderLeadStory(null);
  renderLatestStories([]);
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
