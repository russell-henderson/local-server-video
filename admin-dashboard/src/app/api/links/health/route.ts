import { NextResponse } from "next/server";

export async function GET() {
  // Placeholder: wire to real sentinel scan later
  return NextResponse.json({
    status: "idle",
    checked: 0,
    failures: [],
  });
}
