export const DEFAULT_CAD_WEBHOOK_URL =
  "https://meiyume.app.n8n.cloud/webhook/dcd53389-3d85-469d-840e-35ecae130592";

export function getCadWebhookUrl() {
  return process.env.N8N_CAD_WORKFLOW_URL || DEFAULT_CAD_WEBHOOK_URL;
}

export function normalizeEngineeringResult(data: unknown) {
  if (!data || typeof data !== "object") return null;
  const value = data as Record<string, unknown>;

  if (
    value.data &&
    typeof value.data === "object" &&
    !Array.isArray(value.data)
  ) {
    const nested = value.data as Record<string, unknown>;
    if (Array.isArray(nested.data) && nested.data.length > 0) {
      return nested.data[0];
    }
  }

  if (Array.isArray(value.data) && value.data.length > 0) {
    return value.data[0];
  }

  return value;
}
