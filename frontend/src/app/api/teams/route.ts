import { NextResponse } from "next/server";
import { env } from "@/config/env";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const response = await fetch(`${env.get("NEXT_PUBLIC_API_URL")}/api/v1/teams`, {
      credentials: "include",
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}
