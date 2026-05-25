import { execFile } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const candidateSofficePaths = [
  process.env.OFFICE_CONVERTER_PATH,
  process.env.SOFFICE_PATH,
  "/Applications/LibreOffice.app/Contents/MacOS/soffice",
  "/opt/homebrew/bin/soffice",
  "/usr/local/bin/soffice",
  "soffice",
  "libreoffice"
].filter(Boolean) as string[];

export function isOfficeFile(filename: string) {
  return /\.(doc|docx|ppt|pptx)$/i.test(filename);
}

function pdfFilename(filename: string) {
  return filename.replace(/\.(doc|docx|ppt|pptx)$/i, ".pdf");
}

async function findSoffice() {
  for (const candidate of candidateSofficePaths) {
    try {
      await execFileAsync(candidate, ["--version"], { timeout: 10_000 });
      return candidate;
    } catch {
      // Try the next known executable/path.
    }
  }

  throw new Error(
    "Word/PPT upload needs LibreOffice installed for PDF conversion. Install LibreOffice or set OFFICE_CONVERTER_PATH to the soffice executable."
  );
}

export async function convertOfficeToPdf(file: Buffer, filename: string) {
  const soffice = await findSoffice();
  const tempRoot = await mkdtemp(path.join(tmpdir(), "meiyume-office-"));
  const inputDir = path.join(tempRoot, "input");
  const outputDir = path.join(tempRoot, "output");
  const inputPath = path.join(inputDir, `${randomUUID()}_${filename}`);
  const outputPath = path.join(outputDir, pdfFilename(path.basename(inputPath)));

  try {
    await mkdir(inputDir, { recursive: true });
    await mkdir(outputDir, { recursive: true });
    await writeFile(inputPath, file);

    await execFileAsync(
      soffice,
      ["--headless", "--convert-to", "pdf", "--outdir", outputDir, inputPath],
      { timeout: 120_000 }
    );

    return {
      filename: pdfFilename(filename),
      buffer: await readFile(outputPath)
    };
  } finally {
    await rm(tempRoot, { recursive: true, force: true });
  }
}
