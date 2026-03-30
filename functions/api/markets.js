import {
  fetchJson,
  formatSignedNumber,
  json,
  loadUtilityFeed,
  selectStories,
  toNumber,
} from "../_lib/dashboard.js";

async function fetchJsonWithTimeout(url, init = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort("timeout"), timeoutMs);
  try {
    return await fetchJson(url, {
      ...init,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

async function fetchYahooIndex(symbol, label) {
  const payload = await fetchJsonWithTimeout(
    `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?range=1d&interval=5m`,
    {
      headers: {
        origin: "https://finance.yahoo.com",
        referer: "https://finance.yahoo.com/",
      },
    }
  );

  const meta = payload?.chart?.result?.[0]?.meta || {};
  const value = toNumber(meta?.regularMarketPrice);
  const previousClose = toNumber(meta?.chartPreviousClose ?? meta?.previousClose);
  const change = value !== null && previousClose !== null ? value - previousClose : null;
  const changePercent =
    value !== null && previousClose ? ((value - previousClose) / previousClose) * 100 : null;

  return {
    symbol: label,
    displaySymbol: meta?.symbol || symbol,
    value,
    change,
    changePercent,
    asOf: meta?.regularMarketTime ? new Date(meta.regularMarketTime * 1000).toISOString() : null,
  };
}

async function fetchNasdaqComposite() {
  return fetchYahooIndex("^IXIC", "Nasdaq");
}

async function fetchBitcoin() {
  const payload = await fetchJsonWithTimeout(
    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
  );

  return {
    symbol: "Bitcoin",
    displaySymbol: "BTC",
    value: payload?.bitcoin?.usd ?? null,
    change: null,
    changePercent: payload?.bitcoin?.usd_24h_change ?? null,
    asOf: new Date().toISOString(),
  };
}

async function safeQuote(promiseFactory) {
  try {
    return await promiseFactory();
  } catch {
    return null;
  }
}

function normalizeQuote(quote) {
  return {
    ...quote,
    valueDisplay:
      quote.value === null || quote.value === undefined
        ? "Unavailable"
        : new Intl.NumberFormat("en-US", {
            maximumFractionDigits: quote.symbol === "Bitcoin" ? 0 : 2,
            minimumFractionDigits: quote.symbol === "Bitcoin" ? 0 : 2,
          }).format(quote.value),
    changeDisplay: quote.change === null ? null : formatSignedNumber(quote.change, 2),
    changePercentDisplay:
      quote.changePercent === null ? null : `${quote.changePercent > 0 ? "+" : ""}${quote.changePercent.toFixed(2)}%`,
  };
}

export async function onRequestGet(context) {
  try {
    const [feed, quotes] = await Promise.all([
      loadUtilityFeed(context).catch(() => null),
      Promise.all([
        safeQuote(() => fetchYahooIndex("^DJI", "Dow")),
        safeQuote(() => fetchYahooIndex("^GSPC", "S&P 500")),
        safeQuote(fetchNasdaqComposite),
        safeQuote(fetchBitcoin),
      ]),
    ]);

    return json({
      ok: true,
      updatedAt: new Date().toISOString(),
      watchlist: quotes.filter(Boolean).map(normalizeQuote),
      headlines: feed ? selectStories(feed, ["business-markets", "technology", "crypto-finance"], 8) : [],
    });
  } catch {
    return json(
      {
        ok: false,
        error: "Could not load the markets desk.",
      },
      502,
      "no-store"
    );
  }
}
