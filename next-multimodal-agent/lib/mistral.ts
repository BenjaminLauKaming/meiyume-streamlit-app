import { getEnv } from "@/lib/env";
import { uploadImageToStorage } from "@/lib/supabase";

type MistralPage = {
  markdown?: string;
  images?: Array<{
    id?: string;
    image_base64?: string;
  }>;
};

type MistralOcrResponse = {
  pages?: MistralPage[];
};

function inferMime(filename: string, fallback: string) {
  const lower = filename.toLowerCase();
  if (lower.endsWith(".pdf")) return "application/pdf";
  if (lower.endsWith(".png")) return "image/png";
  if (lower.endsWith(".webp")) return "image/webp";
  if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
  return fallback || "application/octet-stream";
}

export async function runMistralOcr(
  file: Buffer,
  filename: string,
  mimeType: string
) {
  const env = getEnv();
  const arrayBuffer = file.buffer.slice(
    file.byteOffset,
    file.byteOffset + file.byteLength
  ) as ArrayBuffer;
  const uploadForm = new FormData();
  uploadForm.append(
    "file",
    new Blob([arrayBuffer], { type: inferMime(filename, mimeType) }),
    filename
  );
  uploadForm.append("purpose", "ocr");

  const uploadResponse = await fetch("https://api.mistral.ai/v1/files", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.MULTIMODAL_MISTRAL_API_KEY}` },
    body: uploadForm
  });

  if (!uploadResponse.ok) {
    throw new Error(`Mistral upload failed: ${await uploadResponse.text()}`);
  }

  const uploadJson = (await uploadResponse.json()) as { id: string };
  const urlResponse = await fetch(
    `https://api.mistral.ai/v1/files/${uploadJson.id}/url?expiry=24`,
    {
      headers: { Authorization: `Bearer ${env.MULTIMODAL_MISTRAL_API_KEY}` }
    }
  );

  if (!urlResponse.ok) {
    throw new Error(`Mistral URL failed: ${await urlResponse.text()}`);
  }

  const urlJson = (await urlResponse.json()) as { url: string };
  const ocrResponse = await fetch("https://api.mistral.ai/v1/ocr", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.MULTIMODAL_MISTRAL_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "mistral-ocr-latest",
      document: {
        type: "document_url",
        document_url: urlJson.url
      },
      bbox_annotation_format: {
        type: "json_schema",
        json_schema: {
          name: "element_summary",
          strict: true,
          schema: {
            type: "object",
            properties: {
              visual_description: {
                type: "string",
                description: "A detailed natural language description of the visual element."
              }
            },
            required: ["visual_description"],
            additionalProperties: false
          }
        }
      },
      include_image_base64: true
    })
  });

  if (!ocrResponse.ok) {
    throw new Error(`Mistral OCR failed: ${await ocrResponse.text()}`);
  }

  const ocrJson = (await ocrResponse.json()) as MistralOcrResponse;
  const markdownPages = await Promise.all(
    (ocrJson.pages || []).map(async (page) => {
      let markdown = page.markdown || "";

      for (const image of page.images || []) {
        const imageId = image.id;
        const raw = image.image_base64;
        if (!imageId || !raw) continue;

        const match = /^data:(image\/[a-zA-Z0-9.+-]+);base64,(.+)$/.exec(raw);
        const contentType = match?.[1] || "image/jpeg";
        const base64 = match?.[2] || raw;
        let publicUrl: string;
        try {
          publicUrl = await uploadImageToStorage(
            Buffer.from(base64, "base64"),
            imageId,
            contentType
          );
        } catch {
          continue;
        }

        markdown = markdown.replaceAll(`![${imageId}](${imageId})`, `![${imageId}](${publicUrl})`);
      }

      return markdown;
    })
  );

  return markdownPages.join("\n\n");
}
