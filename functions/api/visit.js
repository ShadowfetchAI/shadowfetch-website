import { incrementCounter, readCounter } from "../_lib/counter.js";

export async function onRequestGet(context) {
  try {
    const counter = await readCounter(context.env);
    return json(
      {
        ok: true,
        incremented: false,
        ...counter
      },
      200
    );
  } catch (error) {
    return json(
      {
        ok: false,
        error: "Could not read the visitor counter."
      },
      502
    );
  }
}

export async function onRequestPost(context) {
  try {
    const counter = await incrementCounter(context.env);
    return json(
      {
        ok: true,
        incremented: true,
        ...counter
      },
      200
    );
  } catch (error) {
    return json(
      {
        ok: false,
        error: "Could not update the visitor counter."
      },
      502
    );
  }
}

function json(payload, status) {
  return Response.json(payload, {
    status,
    headers: {
      "cache-control": "no-store"
    }
  });
}
