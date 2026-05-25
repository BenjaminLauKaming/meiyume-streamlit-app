import { createClient } from "@supabase/supabase-js";
import { getEnv } from "@/lib/env";

export function getSupabaseAdmin() {
  const env = getEnv();

  return createClient(env.MULTIMODAL_SUPABASE_URL, env.MULTIMODAL_SUPABASE_KEY, {
    auth: {
      persistSession: false,
      autoRefreshToken: false
    }
  });
}

export async function uploadImageToStorage(
  image: Buffer,
  imageId: string,
  contentType: string
) {
  const env = getEnv();
  const supabase = getSupabaseAdmin();
  const extension = contentType.split("/")[1] || "jpg";
  const path = `${Date.now()}_${imageId}.${extension}`;

  const { error } = await supabase.storage
    .from(env.MULTIMODAL_SUPABASE_BUCKET)
    .upload(path, image, {
      contentType,
      upsert: false
    });

  if (error) {
    throw new Error(`Failed to upload image ${imageId}: ${error.message}`);
  }

  const { data } = supabase.storage
    .from(env.MULTIMODAL_SUPABASE_BUCKET)
    .getPublicUrl(path);

  return data.publicUrl;
}
