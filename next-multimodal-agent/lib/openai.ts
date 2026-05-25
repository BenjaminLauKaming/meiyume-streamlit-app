import OpenAI from "openai";
import { getEnv } from "@/lib/env";
import { CATEGORIES, ChatMessage, Category } from "@/types/rag";

export function getOpenAI() {
  const env = getEnv();
  return new OpenAI({ apiKey: env.MULTIMODAL_OPENAI_API_KEY });
}

export async function createEmbedding(input: string) {
  const openai = getOpenAI();
  const response = await openai.embeddings.create({
    model: "text-embedding-ada-002",
    input
  });

  return response.data[0].embedding;
}

export async function identifyCategory(
  query: string,
  history: ChatMessage[]
): Promise<Category | "Unknown"> {
  const openai = getOpenAI();
  const historyText = history
    .slice(-4)
    .map(
      (message) =>
        `${message.role.charAt(0).toUpperCase()}${message.role.slice(1)}: ${message.content}\n`
    )
    .join("");
  const systemPrompt = `Your job is to classify the user's latest query into one of these exact categories: ${CATEGORIES.join(", ")}.

Instead of just looking for exact word matches, analyze the user's intent and the semantics of their question. Here is a guide to what each category covers:
- Stones: relates to rocks, marble, gems, natural hard materials, etc.
- Aluminium and Anodizing: relates to lightweight metals, oxidation processes, aluminum parts, metal finishes, etc.
- Electroplating: relates to coating metals, dipping in chemical solutions, metallic shiny finishes, etc.
- Plastics: relates to polymers, injection molding, synthetic materials, acrylic, resins, etc.

IMPORTANT: Use the provided Chat History to understand the context. If the user uses words like "it", "that", or asks a follow-up question, look at the chat history to determine which category they are talking about.

If the query explicitly or implicitly matches one of the categories based on its meaning or the previous conversation context, respond with ONLY the exact category name.
If the query is just a generic greeting or completely unrelated to these topics, respond ONLY with 'Unknown'.`;

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    temperature: 0,
    messages: [
      {
        role: "system",
        content: systemPrompt
      },
      {
        role: "user",
        content: `Chat History:\n${historyText}\n\nUser Query:\n${query}`
      }
    ]
  });

  const category = response.choices[0]?.message.content?.trim();
  return CATEGORIES.includes(category as Category)
    ? (category as Category)
    : "Unknown";
}

export async function rephraseForRetrieval(query: string, history: ChatMessage[]) {
  const openai = getOpenAI();
  const historyText = history
    .slice(-4)
    .map(
      (message) =>
        `${message.role.charAt(0).toUpperCase()}${message.role.slice(1)}: ${message.content}\n`
    )
    .join("");
  const systemPrompt = `You are an AI assistant helping to improve vector database search retrieval.
Given the chat history and the user's latest query, write a hypothetical, detailed paragraph that perfectly answers the user's question. 
Use technical terminology that is likely to appear in a technical manual or plating handbook (e.g., translate "deep holes" to "cavities" or "recesses", "without power" to "currentless deposition").
Do NOT formulate a question. Write a declarative, factual paragraph that sounds like it came straight out of a textbook.
Return ONLY this hypothetical paragraph, without quotes or additional text.`;

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    temperature: 0,
    messages: [
      {
        role: "system",
        content: systemPrompt
      },
      {
        role: "user",
        content: `Chat History:\n${historyText}\n\nUser Query:\n${query}`
      }
    ]
  });

  return response.choices[0]?.message.content?.trim() || query;
}

export async function answerFromContext(context: string, question: string) {
  const openai = getOpenAI();
  const systemPrompt =
    "You are a highly precise technical assistant. Your goal is to answer questions based STRICTLY on the provided Document Sections.\n\n" +
    "RULES:\n" +
    "1. FIDELITY: Use the EXACT terminology and wording found in the source text as much as possible. Do not rephrase technical details into generic language.\n" +
    "2. INTEGRATION: You may streamline, summarize, or combine information logically to answer the user, but you must not change the meaning or the specific values/data points.\n" +
    "3. ZERO EXTERNAL KNOWLEDGE: Answer using ONLY the provided context. If the answer is not in the context, state that clearly.\n" +
    "4. VISUALS: If any images (markdown format) are present in the retrieved sections, you MUST include them at the relevant point in your response.\n" +
    "5. GROUNDING: If you are combining multiple sections, prioritize showing the most important technical highlights first.\n" +
    "6. FORMATTING: Use Markdown extensively to make your answer highly readable. Use bullet points for lists, bold text for key terms, and keep paragraphs short.";

  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    temperature: 0.1,
    messages: [
      {
        role: "system",
        content: systemPrompt
      },
      {
        role: "user",
        content: `Retrieved Document Sections:\n${context}\n\nUser Question: ${question}`
      }
    ]
  });

  return response.choices[0]?.message.content?.trim() || "";
}
