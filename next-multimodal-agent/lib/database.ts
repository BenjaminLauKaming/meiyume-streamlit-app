import { Pool } from "pg";

const globalForDatabase = globalThis as typeof globalThis & {
  engineeringPool?: Pool;
};

export function getEngineeringPool() {
  const connectionString =
    process.env.CAD_DATABASE_URL || process.env.DATABASE_URL;

  if (!connectionString) {
    throw new Error("Missing CAD_DATABASE_URL or DATABASE_URL.");
  }

  if (!globalForDatabase.engineeringPool) {
    globalForDatabase.engineeringPool = new Pool({
      connectionString,
      max: 2,
      idleTimeoutMillis: 10_000,
      connectionTimeoutMillis: 10_000,
      ssl: { rejectUnauthorized: false }
    });
  }

  return globalForDatabase.engineeringPool;
}
