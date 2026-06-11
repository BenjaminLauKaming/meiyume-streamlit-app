"use client";

import { useMemo, useState } from "react";
import { Download, Search } from "lucide-react";
import { decodeBase64Csv, downloadCsv, parseCsv } from "@/lib/csv";
import { CsvRow, EngineeringResultPayload } from "@/types/engineering";

type EngineeringResultsProps = {
  result: EngineeringResultPayload;
};

function ResultsTable({ rows }: { rows: CsvRow[] }) {
  if (rows.length === 0) {
    return <div className="engineering-empty">No rows returned.</div>;
  }

  const columns = Object.keys(rows[0]);

  return (
    <div className="engineering-table-wrap">
      <table className="engineering-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column.replaceAll("_", " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => (
                <td key={column}>{row[column] || "—"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EngineeringResults({ result }: EngineeringResultsProps) {
  const [tab, setTab] = useState<"dimension" | "matching">("dimension");
  const [query, setQuery] = useState("");
  const dimensionCsv = result.dimension ? decodeBase64Csv(result.dimension) : "";
  const matchingCsv = result.matching ? decodeBase64Csv(result.matching) : "";
  const activeCsv = tab === "dimension" ? dimensionCsv : matchingCsv;
  const rows = useMemo(() => parseCsv(activeCsv), [activeCsv]);
  const filteredRows = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return rows;

    return rows.filter((row) =>
      Object.values(row).some((value) => value.toLowerCase().includes(normalized))
    );
  }, [query, rows]);

  return (
    <section className="engineering-results">
      <div className="engineering-results-head">
        <div>
          <h2>Analysis results</h2>
          <p>{filteredRows.length} rows shown</p>
        </div>
        <button
          className="ghost-button"
          type="button"
          disabled={!activeCsv}
          onClick={() => downloadCsv(`${tab}.csv`, activeCsv)}
        >
          <Download size={17} />
          Download CSV
        </button>
      </div>

      <div className="result-tabs" role="tablist" aria-label="Engineering results">
        <button
          className={tab === "dimension" ? "active" : ""}
          type="button"
          role="tab"
          aria-selected={tab === "dimension"}
          onClick={() => setTab("dimension")}
        >
          Dimensions
        </button>
        <button
          className={tab === "matching" ? "active" : ""}
          type="button"
          role="tab"
          aria-selected={tab === "matching"}
          onClick={() => setTab("matching")}
        >
          Matching parts
        </button>
      </div>

      <label className="engineering-search">
        <Search size={17} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter any column..."
        />
      </label>

      <ResultsTable rows={filteredRows} />
    </section>
  );
}
