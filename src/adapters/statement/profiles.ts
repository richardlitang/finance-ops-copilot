export type StatementHeaderAliases = Record<string, string>;

export const BANK_STATEMENT_HEADER_ALIASES: StatementHeaderAliases = {
  txn_date: "transaction_date",
  trans_date: "transaction_date",
  transaction_date_: "transaction_date",
  posting_date_: "posting_date",
  post_date: "posting_date",
  posted_date: "posting_date",
  book_date: "posting_date",
  transaction_details: "description",
  transaction_description: "description",
  remarks: "description",
  particulars: "description",
  reference_no: "reference",
  reference_number: "reference",
  transaction_id: "reference",
  amount_php: "amount",
  amount_usd: "amount",
  withdrawal_amount: "debit",
  deposit_amount: "credit",
  debit_amount: "debit",
  credit_amount: "credit",
  currency_code: "currency",
  payee_name: "payee",
  merchant_name: "merchant"
};

export const CREDIT_CARD_HEADER_ALIASES: StatementHeaderAliases = {
  trans_date: "transaction_date",
  transaction_date_: "transaction_date",
  post_date: "posting_date",
  posting_date_: "posting_date",
  merchant_name: "merchant",
  card_acceptor: "merchant",
  transaction_details: "description",
  narrative: "description",
  reference_no: "reference_number",
  reference_num: "reference_number",
  ref_no: "reference_number",
  auth_code: "reference_number",
  amount_usd: "amount",
  amount_php: "amount",
  billed_amount: "amount",
  transaction_amount: "amount",
  currency_code: "currency",
  payment_amount: "payments",
  charge_amount: "charges"
};
