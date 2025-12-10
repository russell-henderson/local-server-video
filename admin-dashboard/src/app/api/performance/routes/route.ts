import { NextResponse } from "next/server";

const VIDEO_SERVER_BASE =
  process.env.NEXT_PUBLIC_VIDEO_SERVER_URL || "http://localhost:5000";

export async function GET() {
  try {
    const res = await fetch(
      `${VIDEO_SERVER_BASE}/api/admin/performance/routes?window_seconds=900&sort_by=p95_latency_ms&order=desc&limit=25`,
      { cache: "no-store" },
    );
    if (!res.ok) {
      return NextResponse.json(
        { error: "Failed to load route metrics" },
        { status: res.status },
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "Route metrics unavailable", details: String(err) },
      { status: 502 },
    );
  }
}
