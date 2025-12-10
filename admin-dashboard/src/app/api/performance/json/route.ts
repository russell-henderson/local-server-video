import { NextResponse } from "next/server";

const VIDEO_SERVER_BASE =
  process.env.NEXT_PUBLIC_VIDEO_SERVER_URL || "http://localhost:5000";

export async function GET() {
  try {
    const res = await fetch(
      `${VIDEO_SERVER_BASE}/admin/performance/json?include_routes=false&include_workers=false`,
      { cache: "no-store" },
    );
    if (!res.ok) {
      return NextResponse.json(
        { error: "Failed to load performance snapshot" },
        { status: res.status },
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "Performance snapshot unavailable", details: String(err) },
      { status: 502 },
    );
  }
}
