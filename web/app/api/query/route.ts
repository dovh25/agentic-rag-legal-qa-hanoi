import { NextResponse } from "next/server";

export const runtime = "nodejs";
const maxRequestBytes = 16_384;

export async function POST(request: Request) {
  const apiBase =
    process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!apiBase) {
    return NextResponse.json(
      { detail: "Backend API URL is not configured." },
      { status: 503 },
    );
  }

  const contentLength = Number(request.headers.get("content-length") ?? 0);
  if (contentLength > maxRequestBytes) {
    return NextResponse.json(
      { detail: "Request body is too large." },
      { status: 413 },
    );
  }

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid JSON request." }, { status: 400 });
  }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return NextResponse.json(
      { detail: "Request body must be a JSON object." },
      { status: 400 },
    );
  }
  const serializedPayload = JSON.stringify(payload);
  if (new TextEncoder().encode(serializedPayload).byteLength > maxRequestBytes) {
    return NextResponse.json(
      { detail: "Request body is too large." },
      { status: 413 },
    );
  }

  try {
    const headers = new Headers({ "Content-Type": "application/json" });
    if (process.env.API_KEY) {
      headers.set("X-API-Key", process.env.API_KEY);
    }
    const upstream = await fetch(
      `${apiBase.replace(/\/$/, "")}/api/v1/query`,
      {
        method: "POST",
        headers,
        body: serializedPayload,
        signal: AbortSignal.timeout(30_000),
        cache: "no-store",
      },
    );
    const contentType = upstream.headers.get("content-type") ?? "application/json";
    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: { "Content-Type": contentType },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      return NextResponse.json(
        { detail: "Backend API request timed out." },
        { status: 504 },
      );
    }
    console.error("Backend API proxy request failed.", error);
    return NextResponse.json(
      { detail: "Backend API is unavailable." },
      { status: 502 },
    );
  }
}
