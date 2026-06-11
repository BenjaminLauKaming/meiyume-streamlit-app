"use client";

import Link from "next/link";
import { FormEvent, useMemo, useRef, useState } from "react";
import { FileUp, Loader2, Send, Trash2, Wrench } from "lucide-react";
import { MarkdownMessage } from "@/components/MarkdownMessage";
import { CATEGORIES, Category, ChatMessage } from "@/types/rag";

type UploadState = {
  kind: "idle" | "loading" | "success" | "error";
  text: string;
};

export default function Home() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [category, setCategory] = useState<Category>("Stones");
  const [uploadState, setUploadState] = useState<UploadState>({
    kind: "idle",
    text: "Upload PDF, image, Word, or PowerPoint files into the material knowledge base."
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);

  const canAsk = useMemo(() => question.trim().length > 0 && !isAsking, [question, isAsking]);

  async function uploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setUploadState({ kind: "error", text: "Choose a file before uploading." });
      return;
    }

    setUploadState({ kind: "loading", text: "Processing document and building vectors..." });

    const body = new FormData();
    body.append("file", file);
    body.append("category", category);

    const response = await fetch("/api/ingest", {
      method: "POST",
      body
    });
    const data = await response.json();

    if (!response.ok) {
      setUploadState({ kind: "error", text: data.error || "Upload failed." });
      return;
    }

    setUploadState({
      kind: "success",
      text: `Indexed ${data.filename} into ${data.category} with ${data.chunks} chunks.`
    });
    if (fileRef.current) fileRef.current.value = "";
  }

  async function askQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    setQuestion("");
    setIsAsking(true);

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: trimmed,
        history: nextMessages
      })
    });
    const data = await response.json();

    setMessages([
      ...nextMessages,
      {
        role: "assistant",
        content: response.ok ? data.answer : data.error || "Something went wrong."
      }
    ]);
    setIsAsking(false);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div>
            <h1>Meiyume RAG</h1>
            <p>Multimodal document assistant</p>
          </div>
        </div>

        <Link className="agent-link" href="/engineering">
          <Wrench size={18} />
          Engineering Drawing Agent
        </Link>

        <form className="panel upload-panel" onSubmit={uploadDocument}>
          <fieldset className="field category-field">
            <span>Material category</span>
            <div className="category-grid" role="radiogroup" aria-label="Material category">
              {CATEGORIES.map((item) => (
                <button
                  className={`category-option ${category === item ? "active" : ""}`}
                  key={item}
                  type="button"
                  role="radio"
                  aria-checked={category === item}
                  onClick={() => setCategory(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </fieldset>

          <label className="field">
            <span>Source file</span>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.doc,.docx,.ppt,.pptx,.png,.jpg,.jpeg,.webp"
            />
          </label>

          <button className="primary-button" type="submit" disabled={uploadState.kind === "loading"}>
            {uploadState.kind === "loading" ? <Loader2 size={18} /> : <FileUp size={18} />}
            Process file
          </button>

          <div className={`status ${uploadState.kind}`}>
            {uploadState.text}
          </div>
        </form>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <h2>Material knowledge chat</h2>
            <p>Answers are grounded in indexed sections and keep relevant images inline.</p>
          </div>
          <button
            className="icon-button"
            type="button"
            title="Clear chat"
            aria-label="Clear chat"
            onClick={() => setMessages([])}
            disabled={messages.length === 0 || isAsking}
          >
            <Trash2 size={18} />
          </button>
        </header>

        <div className="chat-log">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h3>Ask about uploaded materials</h3>
              <p>
                Questions are classified into the four material categories, searched against Supabase vectors, and answered from expanded document sections.
              </p>
            </div>
          ) : (
            messages.map((message, index) => (
              <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
                <div className="bubble">
                  <MarkdownMessage content={message.content} />
                </div>
              </article>
            ))
          )}

          {isAsking ? (
            <article className="message assistant">
              <div className="bubble">Searching indexed sections...</div>
            </article>
          ) : null}
        </div>

        <form className="composer" onSubmit={askQuestion}>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                if (canAsk) {
                  event.currentTarget.form?.requestSubmit();
                }
              }
            }}
            placeholder="Ask a question about stones, anodizing, electroplating, or plastics..."
            rows={1}
          />
          <button className="primary-button" type="submit" disabled={!canAsk}>
            {isAsking ? <Loader2 size={18} /> : <Send size={18} />}
            Send
          </button>
        </form>
      </section>
    </main>
  );
}
