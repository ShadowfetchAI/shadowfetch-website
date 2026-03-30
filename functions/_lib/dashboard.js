import { loadFeedSnapshot } from "./feed.js";

export const HOME_LOCATION = Object.freeze({
  label: "Cornelia, Georgia",
  shortLabel: "Cornelia, GA",
  latitude: 34.5115,
  longitude: -83.5302,
});

const DEFAULT_HEADERS = {
  "user-agent": "ShadowFetch News (https://www.shadowfetch.com)",
  accept: "application/json, application/geo+json;q=0.9, */*;q=0.8",
};

export async function fetchJson(url, init = {}) {
  const response = await fetch(url, {
    ...init,
    headers: {
      ...DEFAULT_HEADERS,
      ...(init.headers || {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${url}: ${response.status}`);
  }

  return response.json();
}

export function json(payload, status = 200, cacheControl = "public, max-age=300") {
  return Response.json(payload, {
    status,
    headers: {
      "cache-control": cacheControl,
    },
  });
}

export async function loadUtilityFeed(context) {
  return loadFeedSnapshot(context);
}

export function selectStories(feed, sectionKeys = [], limit = 8) {
  const wanted = new Set(sectionKeys.map((value) => String(value || "").toLowerCase()));
  const stories = Array.isArray(feed?.latest) ? feed.latest : [];
  return stories
    .filter((story) => wanted.has(String(story?.section_key || "").toLowerCase()))
    .slice(0, limit)
    .map(normalizeStory);
}

export function normalizeStory(story) {
  return {
    title: story?.title || "Untitled",
    link: story?.link || "#",
    summary: story?.summary || "",
    source: story?.source || "Source",
    section: story?.section || "News",
    sectionKey: story?.section_key || "",
    timestamp: story?.timestamp || null,
    sourceKey: story?.source_key || "",
  };
}

export function toNumber(value) {
  const normalized = String(value ?? "")
    .replace(/[$,%]/g, "")
    .replace(/,/g, "")
    .trim();
  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatSignedNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return null;
  }

  const amount = Number(value);
  const sign = amount > 0 ? "+" : amount < 0 ? "-" : "";
  return `${sign}${Math.abs(amount).toFixed(digits)}`;
}
