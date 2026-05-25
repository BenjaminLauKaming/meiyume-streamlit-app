export const CATEGORIES = [
  "Stones",
  "Aluminium and Anodizing",
  "Electroplating",
  "Plastics"
] as const;

export type Category = (typeof CATEGORIES)[number];

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;
};

export type DocumentMetadata = {
  category: Category;
  source: string;
  section_id: string;
  chunk_id: number;
  headers?: Record<string, string>;
};

export type RetrievedDocument = {
  content: string;
  metadata: DocumentMetadata;
};
