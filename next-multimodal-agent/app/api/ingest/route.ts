import { NextResponse } from "next/server";
import { splitMarkdownIntoChunks } from "@/lib/chunking";
import { convertOfficeToPdf, isOfficeFile } from "@/lib/officeToPdf";
import { createEmbedding } from "@/lib/openai";
import { runMistralOcr } from "@/lib/mistral";
import { getSupabaseAdmin } from "@/lib/supabase";
import { CATEGORIES, Category } from "@/types/rag";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function isCategory(value: FormDataEntryValue | null): value is Category {
  return typeof value === "string" && CATEGORIES.includes(value as Category);
}

async function extractMarkdown(file: File, buffer: Buffer) {
  const lower = file.name.toLowerCase();

  if (isOfficeFile(lower)) {
    const pdf = await convertOfficeToPdf(buffer, file.name);
    return runMistralOcr(pdf.buffer, pdf.filename, "application/pdf");
  }

  return runMistralOcr(buffer, file.name, file.type);
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    const category = formData.get("category");

    if (!(file instanceof File)) {
      return NextResponse.json({ error: "Missing uploaded file." }, { status: 400 });
    }

    if (!isCategory(category)) {
      return NextResponse.json({ error: "Invalid category." }, { status: 400 });
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    const markdown = await extractMarkdown(file, buffer);
    const chunks = splitMarkdownIntoChunks(markdown, file.name, category);

    if (chunks.length === 0) {
      return NextResponse.json(
        { error: "No readable text was extracted from this file." },
        { status: 422 }
      );
    }

    const rows = await Promise.all(
      chunks.map(async (chunk) => ({
        content: chunk.content,
        metadata: chunk.metadata,
        embedding: await createEmbedding(chunk.content)
      }))
    );

    const supabase = getSupabaseAdmin();
    const { error } = await supabase.from("documents").insert(rows);

    if (error) {
      throw new Error(`Supabase insert failed: ${error.message}`);
    }

    return NextResponse.json({
      filename: file.name,
      category,
      chunks: rows.length
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown ingest error";
    console.error("POST /api/ingest failed", error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
