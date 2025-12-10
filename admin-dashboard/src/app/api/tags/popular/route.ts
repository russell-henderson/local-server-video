import { NextResponse } from "next/server";

const VIDEO_SERVER_BASE =
  process.env.NEXT_PUBLIC_VIDEO_SERVER_URL || "http://localhost:5000";

export async function GET() {
  try {
    const res = await fetch(`${VIDEO_SERVER_BASE}/api/tags/popular?limit=20`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json({ tags: [] }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json({ tags: [] }, { status: 502 });
  }
}
