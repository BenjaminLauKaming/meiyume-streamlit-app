import { NextResponse } from "next/server";
import { PDFDocument } from "pdf-lib";
import { getCadWebhookUrl } from "@/lib/engineering";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

async function splitPdf(file: Uint8Array) {
  const source = await PDFDocument.load(file);
  const pages = await Promise.all(
    source.getPageIndices().map(async (pageIndex) => {
      const pageDocument = await PDFDocument.create();
      const [page] = await pageDocument.copyPages(source, [pageIndex]);
      pageDocument.addPage(page);
      const bytes = await pageDocument.save();

      return {
        page_number: pageIndex + 1,
        data: Buffer.from(bytes).toString("base64"),
        filename: `page_${pageIndex + 1}.pdf`
      };
    })
  );

  return {
    pageCount: source.getPageCount(),
    pages
  };
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    const sessionId = formData.get("session_id");

    if (!(file instanceof File) || !file.name.toLowerCase().endsWith(".pdf")) {
      return NextResponse.json(
        { error: "Upload a PDF technical drawing." },
        { status: 400 }
      );
    }

    if (typeof sessionId !== "string" || !sessionId) {
      return NextResponse.json({ error: "Missing session ID." }, { status: 400 });
    }

    const bytes = new Uint8Array(await file.arrayBuffer());
    const { pageCount, pages } = await splitPdf(bytes);
    const response = await fetch(getCadWebhookUrl(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "Meiyume-AI-Assistant/1.0"
      },
      body: JSON.stringify({
        full_document: {
          data: Buffer.from(bytes).toString("base64"),
          filename: file.name,
          page_count: pageCount
        },
        pages,
        session_id: sessionId
      }),
      signal: AbortSignal.timeout(55_000)
    });

    if (!response.ok) {
      throw new Error(
        `n8n submission failed (${response.status}): ${await response.text()}`
      );
    }

    return NextResponse.json({
      status: "submitted",
      session_id: sessionId,
      filename: file.name,
      page_count: pageCount
    });
  } catch (error) {
    console.error("POST /api/engineering/submit failed", error);
    const message =
      error instanceof Error ? error.message : "Unknown engineering submit error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
