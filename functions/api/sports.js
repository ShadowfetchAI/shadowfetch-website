import { fetchJson, json, loadUtilityFeed, selectStories } from "../_lib/dashboard.js";

const LEAGUES = [
  {
    key: "mlb",
    label: "MLB",
    url: "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
  },
  {
    key: "nba",
    label: "NBA",
    url: "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
  },
  {
    key: "nhl",
    label: "NHL",
    url: "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
  },
];

function normalizeTeam(competitor) {
  const team = competitor?.team || {};
  return {
    name: team.displayName || team.shortDisplayName || team.name || "Team",
    abbreviation: team.abbreviation || "",
    logo: team.logo || "",
    score: competitor?.score || "0",
    homeAway: competitor?.homeAway || "",
    record: competitor?.records?.[0]?.summary || "",
  };
}

function normalizeGame(event, league) {
  const competition = event?.competitions?.[0] || {};
  return {
    id: event?.id || "",
    league,
    name: event?.shortName || event?.name || "Game",
    status:
      competition?.status?.type?.shortDetail ||
      competition?.status?.type?.detail ||
      competition?.status?.type?.description ||
      "Scheduled",
    startTime: event?.date || competition?.date || null,
    link: event?.links?.[0]?.href || "",
    competitors: (competition?.competitors || []).slice(0, 2).map(normalizeTeam),
  };
}

async function fetchLeague(league) {
  try {
    const payload = await fetchJson(league.url);
    return {
      league: league.label,
      games: (payload?.events || []).slice(0, 4).map((event) => normalizeGame(event, league.label)),
    };
  } catch {
    return {
      league: league.label,
      games: [],
    };
  }
}

export async function onRequestGet(context) {
  try {
    const [feed, scoreboards] = await Promise.all([
      loadUtilityFeed(context),
      Promise.all(LEAGUES.map(fetchLeague)),
    ]);

    return json({
      ok: true,
      updatedAt: new Date().toISOString(),
      scoreboards: scoreboards.filter((league) => league.games.length > 0),
      headlines: selectStories(feed, ["sports"], 8),
    });
  } catch {
    return json(
      {
        ok: false,
        error: "Could not load the sports desk.",
      },
      502,
      "no-store"
    );
  }
}
