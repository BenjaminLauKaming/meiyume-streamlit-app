import { NextResponse } from "next/server";
import { getEngineeringPool } from "@/lib/database";
import { normalizeEngineeringResult } from "@/lib/engineering";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const sessionId = new URL(request.url).searchParams.get("session_id");
    if (!sessionId) {
      return NextResponse.json({ error: "Missing session ID." }, { status: 400 });
    }

    const pool = getEngineeringPool();
    const query = await pool.query(
      `select data
       from results
       where session_id = $1 and agent_type = 'cad'
       order by created_at desc
       limit 1`,
      [sessionId]
    );
    const data = query.rows[0];

    if (!data) {
      return NextResponse.json({ status: "processing", session_id: sessionId });
    }

    return NextResponse.json({
      status: "completed",
      session_id: sessionId,
      result: normalizeEngineeringResult(data.data)
    });
  } catch (error) {
    console.error("GET /api/engineering/status failed", error);
    const message =
      error instanceof Error ? error.message : "Unknown engineering status error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
