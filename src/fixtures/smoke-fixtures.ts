import path from "node:path";

export type SmokeFixture = {
  label: string;
  filePath: string;
  sourceHint: string;
};

export function getSmokeFixtures(): SmokeFixture[] {
  return [
    {
      label: "ph-receipt",
      filePath: path.resolve("src/fixtures/receipts/receipt-text.txt"),
      sourceHint: "receipt_text"
    },
    {
      label: "us-receipt",
      filePath: path.resolve("src/fixtures/receipts/us-receipt-text.txt"),
      sourceHint: "receipt_text"
    },
    {
      label: "bank-statement",
      filePath: path.resolve("src/fixtures/statements/bank-sample.csv"),
      sourceHint: "bank_statement"
    },
    {
      label: "credit-card-statement",
      filePath: path.resolve("src/fixtures/statements/credit-card-sample.csv"),
      sourceHint: "credit_card_statement"
    },
    {
      label: "bank-statement-duplicate",
      filePath: path.resolve("src/fixtures/statements/bank-sample.csv"),
      sourceHint: "bank_statement"
    }
  ];
}

export function getDefaultMappingRulesFixturePath(): string {
  return path.resolve("src/fixtures/mapping-rules/default-mapping-rules.csv");
}
