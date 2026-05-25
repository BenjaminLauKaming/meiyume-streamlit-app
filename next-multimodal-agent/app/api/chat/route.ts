import { NextResponse } from "next/server";
import { answerFromContext, createEmbedding, identifyCategory, rephraseForRetrieval } from "@/lib/openai";
import { getSupabaseAdmin } from "@/lib/supabase";
import { ChatMessage, RetrievedDocument } from "@/types/rag";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ChatRequest = {
  message?: string;
  history?: ChatMessage[];
};

function isChatMessage(value: unknown): value is ChatMessage {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return (
    (candidate.role === "user" || candidate.role === "assistant") &&
    typeof candidate.content === "string"
  );
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as ChatRequest;
    const message = body.message?.trim();
    const history = Array.isArray(body.history)
      ? body.history.filter(isChatMessage)
      : [];

    if (!message) {
      return NextResponse.json({ error: "Missing message." }, { status: 400 });
    }

    const category = await identifyCategory(message, history);
    if (category === "Unknown") {
      return NextResponse.json({
        category,
        answer:
          "I'm not quite sure which material category you are asking about. Please specify Stones, Aluminium and Anodizing, Electroplating, or Plastics."
      });
    }

    const retrievalPrompt = await rephraseForRetrieval(message, history);
    const queryEmbedding = await createEmbedding(retrievalPrompt);
    const supabase = getSupabaseAdmin();

    const { data: matches, error: matchError } = await supabase.rpc("match_documents", {
      query_embedding: queryEmbedding,
      match_count: 10,
      filter: { category }
    });

    if (matchError) {
      throw new Error(`Supabase search failed: ${matchError.message}`);
    }

    const retrieved = (matches || []) as RetrievedDocument[];
    if (retrieved.length === 0) {
      return NextResponse.json({
        category,
        answer: `I didn't find any relevant documents in the ${category} category.`
      });
    }

    const sectionIds = Array.from(
      new Set(
        retrieved
          .map((doc) => doc.metadata?.section_id)
          .filter((sectionId): sectionId is string => Boolean(sectionId))
      )
    );

    let expandedContext = "";

    for (const sectionId of sectionIds) {
      const { data: chunks, error } = await supabase
        .from("documents")
        .select("content, metadata")
        .contains("metadata", { section_id: sectionId });

      if (error) {
        throw new Error(`Supabase section expansion failed: ${error.message}`);
      }

      const ordered = ((chunks || []) as RetrievedDocument[]).sort(
        (a, b) => (a.metadata?.chunk_id || 0) - (b.metadata?.chunk_id || 0)
      );

      expandedContext += `--- Document Section Identified: ${sectionId} ---\n`;
      for (const chunk of ordered) {
        expandedContext += `${chunk.content}\n\n`;
      }
      expandedContext += "--- End of Section ---\n\n";
    }

    const answer = await answerFromContext(expandedContext, message);

    return NextResponse.json({
      category,
      answer
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown chat error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
