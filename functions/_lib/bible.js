const SUMMARY_PATH = "/assets/data/bible-edition.json";
const READING_BASE_PATH = "/assets/data/bible-readings";

export async function loadBibleEdition(context) {
  const assetUrl = new URL(SUMMARY_PATH, context.request.url);
  const response = await context.env.ASSETS.fetch(assetUrl);
  if (!response.ok) {
    throw new Error(`Could not load bible edition data: ${response.status}`);
  }
  return response.json();
}

export async function loadReading(context, canon = "protestant", dayNumber = 1) {
  const safeCanon = normalizeCanon(canon);
  const safeDay = clampDayNumber(dayNumber);
  const path = `${READING_BASE_PATH}/${safeCanon}/day-${String(safeDay).padStart(3, "0")}.json`;
  const assetUrl = new URL(path, context.request.url);
  const response = await context.env.ASSETS.fetch(assetUrl);
  if (!response.ok) {
    throw new Error(`Could not load reading payload: ${response.status}`);
  }
  return response.json();
}

export function normalizeCanon(value) {
  return String(value || "").trim().toLowerCase() === "catholic" ? "catholic" : "protestant";
}

export function normalizeStartDate(value) {
  const raw = String(value || "").trim();
  if (!raw) {
    return new Date().toISOString().slice(0, 10);
  }
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) {
    return new Date().toISOString().slice(0, 10);
  }
  return parsed.toISOString().slice(0, 10);
}

export function clampDayNumber(value, totalDays = 365) {
  const parsed = Number.parseInt(String(value || "1"), 10);
  if (!Number.isFinite(parsed)) {
    return 1;
  }
  return Math.min(Math.max(parsed, 1), totalDays);
}

export function computeDayNumber(startDate, baseDate = new Date(), totalDays = 365) {
  const start = new Date(normalizeStartDate(startDate));
  if (Number.isNaN(start.getTime())) {
    return 1;
  }
  const today = new Date(baseDate.getFullYear(), baseDate.getMonth(), baseDate.getDate());
  const localStart = new Date(start.getFullYear(), start.getMonth(), start.getDate());
  const msPerDay = 24 * 60 * 60 * 1000;
  const diff = Math.floor((today.getTime() - localStart.getTime()) / msPerDay);
  return clampDayNumber(diff + 1, totalDays);
}

export function selectPlan(data, canon = "protestant") {
  const safeCanon = normalizeCanon(canon);
  return data?.plans?.[safeCanon] || data?.plans?.protestant || null;
}

export function validateEmail(value) {
  const email = String(value || "").trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return null;
  }
  return email;
}

export function todayIsoString() {
  return new Date().toISOString().slice(0, 10);
}
