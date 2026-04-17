import { describe, expect, it } from "vitest";
import { GoogleSheetsGateway, shouldUseGoogleSheetsGateway } from "../../../src/adapters/sheets/google-sheets-gateway.js";

function createFakeSheetsApi(existingValues: string[][] = []) {
  const calls = {
    get: [] as Array<Record<string, unknown>>,
    update: [] as Array<Record<string, unknown>>,
    batchUpdate: [] as Array<Record<string, unknown>>,
    append: [] as Array<Record<string, unknown>>
  };

  const api = {
    spreadsheets: {
      values: {
        async get(args: Record<string, unknown>) {
          calls.get.push(args);
          return { data: { values: existingValues } };
        },
        async update(args: Record<string, unknown>) {
          calls.update.push(args);
          return { data: {} };
        },
        async batchUpdate(args: Record<string, unknown>) {
          calls.batchUpdate.push(args);
          return { data: {} };
        },
        async append(args: Record<string, unknown>) {
          calls.append.push(args);
          return { data: {} };
        }
      }
    }
  };

  return { api, calls };
}

describe("GoogleSheetsGateway", () => {
  it("updates existing rows by key and appends new rows", async () => {
    const { api, calls } = createFakeSheetsApi([
      ["entry_id", "status", "amount"],
      ["a", "approved", "100"]
    ]);

    const gateway = new GoogleSheetsGateway({
      spreadsheetId: "sheet_1",
      serviceAccountJson: JSON.stringify({
        client_email: "svc@example.com",
        private_key: "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----"
      }),
      sheetsApi: api as never
    });

    await gateway.upsertRows(
      "normalized_entries",
      [
        { entry_id: "a", status: "approved", amount: 120 },
        { entry_id: "b", status: "approved", amount: 90 }
      ],
      "entry_id"
    );

    expect(calls.update).toHaveLength(1);
    expect(calls.batchUpdate).toHaveLength(1);
    expect(calls.append).toHaveLength(1);
  });
});

describe("shouldUseGoogleSheetsGateway", () => {
  it("returns true only when all required env values are present", () => {
    expect(
      shouldUseGoogleSheetsGateway({
        GOOGLE_SHEETS_ENABLED: "true",
        GOOGLE_SHEETS_SPREADSHEET_ID: "sheet_1",
        GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON: "{\"client_email\":\"a\",\"private_key\":\"b\"}"
      })
    ).toBe(true);

    expect(
      shouldUseGoogleSheetsGateway({
        GOOGLE_SHEETS_ENABLED: "false",
        GOOGLE_SHEETS_SPREADSHEET_ID: "sheet_1",
        GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON: "x"
      })
    ).toBe(false);
  });
});
