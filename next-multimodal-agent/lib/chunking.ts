import { Category, DocumentMetadata, RetrievedDocument } from "@/types/rag";

type HeaderState = {
  h1: string;
  h2: string;
  h3: string;
};

function currentSection(headers: HeaderState) {
  const label = [headers.h1, headers.h2, headers.h3].filter(Boolean).join("|");
  return label || "global_document_body";
}

function safeSectionId(filename: string, section: string) {
  return `${filename}_${section.replace(/\s+/g, "_").toLowerCase()}`;
}

function splitRecursive(text: string, chunkSize = 1000, chunkOverlap = 200) {
  const chunks: string[] = [];
  const separators = ["\n\n", "\n", " ", ""];

  const splitText = (input: string, separatorIndex: number): string[] => {
    if (input.length <= chunkSize) return [input];

    const separator = separators[separatorIndex];
    if (separator === "") {
      const pieces: string[] = [];
      for (let start = 0; start < input.length; start += chunkSize) {
        pieces.push(input.slice(start, start + chunkSize));
      }
      return pieces;
    }

    const rawSplits = input.split(separator);
    if (rawSplits.length === 1) {
      return splitText(input, separatorIndex + 1);
    }

    const output: string[] = [];
    let current = "";

    for (const split of rawSplits) {
      const next = current ? `${current}${separator}${split}` : split;
      if (next.length <= chunkSize) {
        current = next;
      } else {
        if (current) output.push(current);
        if (split.length > chunkSize) {
          output.push(...splitText(split, separatorIndex + 1));
          current = "";
        } else {
          current = split;
        }
      }
    }

    if (current) output.push(current);
    return output;
  };

  for (const piece of splitText(text, 0)) {
    const trimmed = piece.trim();
    if (!trimmed) continue;

    if (chunks.length === 0 || chunkOverlap <= 0) {
      chunks.push(trimmed);
      continue;
    }

    const previous = chunks[chunks.length - 1];
    const overlap = previous.slice(Math.max(0, previous.length - chunkOverlap));
    chunks.push(`${overlap}${trimmed}`.slice(0, chunkSize).trim());
  }

  return chunks;
}

export function splitMarkdownIntoChunks(
  markdown: string,
  filename: string,
  category: Category
): RetrievedDocument[] {
  const lines = markdown.split(/\r?\n/);
  const sections: Array<{ headers: HeaderState; content: string }> = [];
  let headers: HeaderState = { h1: "", h2: "", h3: "" };
  let buffer: string[] = [];

  const flush = () => {
    const content = buffer.join("\n").trim();
    if (content) {
      sections.push({ headers: { ...headers }, content });
    }
    buffer = [];
  };

  for (const line of lines) {
    const match = /^(#{1,3})\s+(.+)$/.exec(line);
    if (match) {
      flush();
      const level = match[1].length;
      const title = match[2].trim();

      if (level === 1) {
        headers = { h1: title, h2: "", h3: "" };
      } else if (level === 2) {
        headers = { ...headers, h2: title, h3: "" };
      } else {
        headers = { ...headers, h3: title };
      }
      continue;
    }

    buffer.push(line);
  }
  flush();

  const chunks: RetrievedDocument[] = [];

  sections.forEach((section) => {
    const sectionId = safeSectionId(filename, currentSection(section.headers));
    const splitContents = splitRecursive(section.content, 1000, 200);

    splitContents.forEach((content) => {
      if (content) {
        const metadata: DocumentMetadata = {
          category,
          source: filename,
          section_id: sectionId,
          chunk_id: chunks.length,
          headers: {
            "Header 1": section.headers.h1,
            "Header 2": section.headers.h2,
            "Header 3": section.headers.h3
          }
        };

        chunks.push({ content, metadata });
      }
    });
  });

  return chunks;
}
