"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowLeft,
  FileSearch,
  FileUp,
  Loader2
} from "lucide-react";
import { EngineeringResults } from "@/components/EngineeringResults";
import { EngineeringResultPayload } from "@/types/engineering";

type Job = {
  sessionId: string;
  filename: string;
  pageCount: number;
  status: "processing" | "completed" | "error";
  error?: string;
};

export default function EngineeringPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [result, setResult] = useState<EngineeringResultPayload | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!job || job.status !== "processing") return;

    const poll = window.setInterval(async () => {
      try {
        const response = await fetch(
          `/api/engineering/status?session_id=${encodeURIComponent(job.sessionId)}`,
          { cache: "no-store" }
        );
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || "Unable to check analysis status.");
        }

        if (data.status === "completed") {
          setResult(data.result);
          setJob((current) =>
            current ? { ...current, status: "completed" } : current
          );
        }
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unable to check analysis status.";
        setJob((current) =>
          current ? { ...current, status: "error", error: message } : current
        );
      }
    }, 3000);

    return () => window.clearInterval(poll);
  }, [job]);

  async function submitDrawing(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;

    setSubmitting(true);
    setResult(null);
    const sessionId = crypto.randomUUID();
    const body = new FormData();
    body.append("file", file);
    body.append("session_id", sessionId);

    try {
      const response = await fetch("/api/engineering/submit", {
        method: "POST",
        body
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Unable to submit technical drawing.");
      }

      setJob({
        sessionId,
        filename: data.filename,
        pageCount: data.page_count,
        status: "processing"
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to submit technical drawing.";
      setJob({
        sessionId,
        filename: file.name,
        pageCount: 0,
        status: "error",
        error: message
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="engineering-shell">
      <header className="engineering-topbar">
        <Link className="back-link" href="/">
          <ArrowLeft size={18} />
          Material RAG
        </Link>
        <div>
          <h1>Engineering Drawing Agent</h1>
          <p>Extract dimensions and identify connected-part fit risks.</p>
        </div>
      </header>

      <div className="engineering-content">
        <section className="engineering-upload">
          <div className="engineering-upload-copy">
            <FileSearch size={30} />
            <div>
              <h2>Analyze a technical drawing</h2>
              <p>Upload one multi-page 2D CAD drawing in PDF format.</p>
            </div>
          </div>

          <form onSubmit={submitDrawing}>
            <input ref={fileRef} type="file" accept=".pdf,application/pdf" />
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? <Loader2 size={18} /> : <FileUp size={18} />}
              Start analysis
            </button>
          </form>
        </section>

        {job ? (
          <section className={`engineering-job ${job.status}`}>
            <Activity size={20} />
            <div>
              <strong>
                {job.status === "processing"
                  ? "n8n analysis in progress"
                  : job.status === "completed"
                    ? "Analysis completed"
                    : "Analysis failed"}
              </strong>
              <span>
                {job.error ||
                  `${job.filename}${job.pageCount ? ` · ${job.pageCount} pages` : ""}`}
              </span>
              <small>Session: {job.sessionId}</small>
            </div>
          </section>
        ) : null}

        {result ? <EngineeringResults result={result} /> : null}
      </div>
    </main>
  );
}
