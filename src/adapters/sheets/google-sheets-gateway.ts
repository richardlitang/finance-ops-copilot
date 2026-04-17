import fs from "node:fs";
import { google, type sheets_v4 } from "googleapis";
import type { SheetsGateway } from "./google-sheets-service.js";
import type { SheetsTab } from "./sheets-contract.js";

type ServiceAccountCredentials = {
  client_email: string;
  private_key: string;
};

type RowObject = Record<string, unknown>;

export type GoogleSheetsGatewayOptions = {
  spreadsheetId: string;
  serviceAccountJson: string;
  sheetsApi?: sheets_v4.Sheets;
};

function toStringValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

function parseServiceAccount(value: string): ServiceAccountCredentials {
  const trimmed = value.trim();
  const json = trimmed.startsWith("{") ? trimmed : fs.readFileSync(trimmed, "utf8");
  const parsed = JSON.parse(json) as Partial<ServiceAccountCredentials>;
  if (!parsed.client_email || !parsed.private_key) {
    throw new Error("invalid GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON, missing client_email or private_key");
  }
  return {
    client_email: parsed.client_email,
    private_key: parsed.private_key.replace(/\\n/g, "\n")
  };
}

function mergeColumns(existing: string[], incomingRows: RowObject[]): string[] {
  const seen = new Set(existing);
  const merged = [...existing];
  for (const row of incomingRows) {
    for (const key of Object.keys(row)) {
      if (!seen.has(key)) {
        seen.add(key);
        merged.push(key);
      }
    }
  }
  return merged;
}

function rowToValues(row: RowObject, columns: string[]): string[] {
  return columns.map((column) => toStringValue(row[column]));
}

function a1Column(index: number): string {
  let n = index + 1;
  let col = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    col = String.fromCharCode(65 + rem) + col;
    n = Math.floor((n - 1) / 26);
  }
  return col;
}

export class GoogleSheetsGateway implements SheetsGateway {
  private readonly spreadsheetId: string;
  private readonly sheetsApi: sheets_v4.Sheets;

  constructor(options: GoogleSheetsGatewayOptions) {
    this.spreadsheetId = options.spreadsheetId;
    const credentials = parseServiceAccount(options.serviceAccountJson);
    this.sheetsApi =
      options.sheetsApi ??
      google.sheets({
        version: "v4",
        auth: new google.auth.JWT({
          email: credentials.client_email,
          key: credentials.private_key,
          scopes: ["https://www.googleapis.com/auth/spreadsheets"]
        })
      });
  }

  async upsertRows(tab: SheetsTab, rows: Array<RowObject>, keyField: string): Promise<void> {
    if (rows.length === 0) {
      return;
    }

    const getRes = await this.sheetsApi.spreadsheets.values.get({
      spreadsheetId: this.spreadsheetId,
      range: `${tab}!A:ZZ`
    });
    const existing = (getRes.data.values ?? []).map((row) => row.map((cell) => String(cell)));
    const existingHeaders = existing[0] ?? [];
    const columns = mergeColumns(existingHeaders, rows);
    if (!columns.includes(keyField)) {
      throw new Error(`sheet tab ${tab} is missing required key field ${keyField}`);
    }

    await this.sheetsApi.spreadsheets.values.update({
      spreadsheetId: this.spreadsheetId,
      range: `${tab}!A1:${a1Column(columns.length - 1)}1`,
      valueInputOption: "RAW",
      requestBody: { values: [columns] }
    });

    const keyIndex = columns.indexOf(keyField);
    const existingIndexByKey = new Map<string, number>();
    for (let i = 1; i < existing.length; i += 1) {
      const rowValues = existing[i] ?? [];
      const key = String(rowValues[keyIndex] ?? "").trim();
      if (key) {
        existingIndexByKey.set(key, i + 1);
      }
    }

    const updates: sheets_v4.Schema$ValueRange[] = [];
    const appends: string[][] = [];

    for (const row of rows) {
      const key = toStringValue(row[keyField]).trim();
      if (!key) {
        continue;
      }
      const values = rowToValues(row, columns);
      const existingRowNumber = existingIndexByKey.get(key);
      if (existingRowNumber) {
        updates.push({
          range: `${tab}!A${existingRowNumber}:${a1Column(columns.length - 1)}${existingRowNumber}`,
          values: [values]
        });
      } else {
        appends.push(values);
      }
    }

    if (updates.length > 0) {
      await this.sheetsApi.spreadsheets.values.batchUpdate({
        spreadsheetId: this.spreadsheetId,
        requestBody: {
          valueInputOption: "RAW",
          data: updates
        }
      });
    }

    if (appends.length > 0) {
      await this.sheetsApi.spreadsheets.values.append({
        spreadsheetId: this.spreadsheetId,
        range: `${tab}!A:${a1Column(columns.length - 1)}`,
        valueInputOption: "RAW",
        requestBody: {
          values: appends
        }
      });
    }
  }
}

export function shouldUseGoogleSheetsGateway(env: NodeJS.ProcessEnv): boolean {
  return (
    env.GOOGLE_SHEETS_ENABLED === "true" &&
    Boolean(env.GOOGLE_SHEETS_SPREADSHEET_ID?.trim()) &&
    Boolean(env.GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON?.trim())
  );
}
