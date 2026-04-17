export type ParsedCsv = {
  delimiter: string;
  headers: string[];
  rows: Array<Record<string, string>>;
};

function normalizeHeader(header: string): string {
  return header.trim().toLowerCase().replace(/\s+/g, "_");
}

function parseCsvLine(line: string, delimiter: string): string[] {
  const fields: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === "\"") {
      const next = line[i + 1];
      if (inQuotes && next === "\"") {
        current += "\"";
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (!inQuotes && char === delimiter) {
      fields.push(current.trim());
      current = "";
      continue;
    }

    current += char;
  }
  fields.push(current.trim());
  return fields;
}

function detectDelimiter(headerLine: string): string {
  const commaCount = (headerLine.match(/,/g) ?? []).length;
  const semicolonCount = (headerLine.match(/;/g) ?? []).length;
  return semicolonCount > commaCount ? ";" : ",";
}

export function parseCsv(content: string, forcedDelimiter?: string): ParsedCsv {
  const lines = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (lines.length === 0) {
    return { delimiter: ",", headers: [], rows: [] };
  }

  const delimiter = forcedDelimiter ?? detectDelimiter(lines[0] ?? ",");
  const rawHeaders = parseCsvLine(lines[0] ?? "", delimiter);
  const headers = rawHeaders.map(normalizeHeader);
  const rows: Array<Record<string, string>> = [];

  for (const line of lines.slice(1)) {
    const values = parseCsvLine(line, delimiter);
    const record: Record<string, string> = {};
    for (let idx = 0; idx < headers.length; idx += 1) {
      const key = headers[idx] ?? `col_${idx}`;
      record[key] = values[idx] ?? "";
    }
    rows.push(record);
  }

  return { delimiter, headers, rows };
}
