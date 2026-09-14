import { NextResponse } from "next/server";

/**
 * Proxies the BACKEND's /health check (redis/poller status, uptime).
 *
 * Deliberately not named /api/health — that path is already Next.js's own
 * trivial self-check (see ../health/route.ts) and takes routing precedence
 * over the catch-all proxy, so it can never reach the backend. And the
 * generic [...path] catch-all can't be reused here either: it always
 * forwards to `${INTERNAL_API_URL}/api/${path}`, but the backend's real
 * health route lives at plain /health, outside the /api/ prefix used by
 * every other backend route.
 */
const BACKEND = process.env.INTERNAL_API_URL ?? "http://localhost:8001";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/health`, {
      signal: AbortSignal.timeout(5_000),
      cache: "no-store",
    });
    const body = await res.text();
    return new NextResponse(body, {
      status: res.status,
      headers: { "content-type": "application/json" },
    });
  } catch (err) {
    console.error("[backend-health] failed to reach backend:", err);
    return NextResponse.json(
      { status: "degraded", redis: "unavailable", poller: "stopped", universe_size: 0, uptime_seconds: 0 },
      { status: 502 }
    );
  }
}
