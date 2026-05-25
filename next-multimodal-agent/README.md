# Meiyume Multimodal RAG Agent

A focused Next.js + TypeScript version of the original Streamlit multimodal agent. It keeps only the document/image knowledge workflow:

- Upload PDF, image, Word, or PowerPoint source files.
- Convert Word/PowerPoint files to PDF before OCR so Mistral handles layout and annotations consistently.
- Extract text and images.
- Store extracted images in Supabase Storage.
- Embed chunks into a Supabase `documents` vector table.
- Chat against indexed material categories with image-aware Markdown answers.

## Run Locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Environment

Copy `.env.example` to `.env.local` and fill in:

```env
MULTIMODAL_SUPABASE_URL=
MULTIMODAL_SUPABASE_KEY=
MULTIMODAL_SUPABASE_BUCKET=
MULTIMODAL_MISTRAL_API_KEY=
MULTIMODAL_OPENAI_API_KEY=
```

Use a Supabase service role key for server-side ingestion if your `documents` table and storage bucket are protected by RLS.

For Word and PowerPoint upload, install LibreOffice so the app can convert files to PDF before sending them to Mistral OCR. If `soffice` is not on PATH, set:

```env
OFFICE_CONVERTER_PATH=/Applications/LibreOffice.app/Contents/MacOS/soffice
```

## Supabase Shape

This app expects the same broad table/RPC shape used by the Python `SupabaseVectorStore` flow:

```sql
create extension if not exists vector;

create table if not exists documents (
  id bigserial primary key,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding vector(1536) not null
);

create or replace function match_documents(
  query_embedding vector(1536),
  match_count int,
  filter jsonb default '{}'::jsonb
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where documents.metadata @> filter
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;
```

The image bucket should be public if you want inline images to render directly in chat answers.

## What Was Kept

The old project has CAD, compliance, quality, scraper, and multimodal agents. This folder only ports the multimodal RAG behavior from `multimodalAssistant.py`.

The material categories are:

- Stones
- Aluminium and Anodizing
- Electroplating
- Plastics
