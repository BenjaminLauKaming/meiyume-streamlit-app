const envKeys = [
  "MULTIMODAL_SUPABASE_URL",
  "MULTIMODAL_SUPABASE_KEY",
  "MULTIMODAL_SUPABASE_BUCKET",
  "MULTIMODAL_MISTRAL_API_KEY",
  "MULTIMODAL_OPENAI_API_KEY"
] as const;

export type AppEnv = Record<(typeof envKeys)[number], string>;

export function getEnv(): AppEnv {
  const missing = envKeys.filter((key) => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(`Missing environment variables: ${missing.join(", ")}`);
  }

  return Object.fromEntries(
    envKeys.map((key) => [key, process.env[key] as string])
  ) as AppEnv;
}
