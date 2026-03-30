import { HOME_LOCATION, fetchJson, json } from "../_lib/dashboard.js";

function normalizeForecastPeriod(period) {
  if (!period) {
    return null;
  }

  return {
    name: period.name || "",
    startTime: period.startTime || null,
    temperature: period.temperature ?? null,
    temperatureUnit: period.temperatureUnit || "F",
    shortForecast: period.shortForecast || "",
    detailedForecast: period.detailedForecast || "",
    windSpeed: period.windSpeed || "",
    windDirection: period.windDirection || "",
    icon: period.icon || "",
    isDaytime: Boolean(period.isDaytime),
  };
}

function normalizeAlert(feature) {
  const props = feature?.properties || {};
  return {
    id: feature?.id || props.id || "",
    event: props.event || "Weather alert",
    severity: props.severity || "",
    urgency: props.urgency || "",
    area: props.areaDesc || "",
    headline: props.headline || props.description || "",
    link: props["@id"] || feature?.id || "",
  };
}

export async function onRequestGet() {
  try {
    const pointUrl = `https://api.weather.gov/points/${HOME_LOCATION.latitude},${HOME_LOCATION.longitude}`;
    const pointData = await fetchJson(pointUrl);
    const pointProps = pointData?.properties || {};

    const [forecastData, hourlyData, alertsData] = await Promise.all([
      fetchJson(pointProps.forecast),
      fetchJson(pointProps.forecastHourly),
      fetchJson(`https://api.weather.gov/alerts/active?point=${HOME_LOCATION.latitude},${HOME_LOCATION.longitude}`),
    ]);

    const currentPeriod = normalizeForecastPeriod(hourlyData?.properties?.periods?.[0]);
    const forecast = (forecastData?.properties?.periods || [])
      .slice(0, 6)
      .map(normalizeForecastPeriod)
      .filter(Boolean);

    const alerts = (alertsData?.features || []).slice(0, 4).map(normalizeAlert);

    return json({
      ok: true,
      location: HOME_LOCATION,
      updatedAt:
        hourlyData?.properties?.updateTime ||
        forecastData?.properties?.updateTime ||
        new Date().toISOString(),
      current: currentPeriod,
      forecast,
      alerts,
    });
  } catch (error) {
    return json(
      {
        ok: false,
        error: "Could not load the weather desk.",
      },
      502,
      "no-store"
    );
  }
}
