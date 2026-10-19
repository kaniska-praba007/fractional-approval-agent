# Shared Contract: Proof Shape & Reason Codes

This document defines the canonical JSON contract emitted by the fiduciary reasoning layers and consumed by downstream components (the Audit Log, Manager Console, and Streamlit Treasury Dashboard).

---

## 1. Core Financial Principles & Conservation Definition

1. **Integer Minor Units (Zero Float):**
   - All monetary fields (`gross`, `fee`, `artist`, `community`, `dust`, `pool`, and co-owner `amount`) are represented strictly in integer minor units (e.g., USD cents: `$10,000.00` = `1000000`).
   - Floating-point representations (`float`, `decimal`, `/`, or `round()`) are strictly forbidden in runtime code, MeTTa rules, JSON exchanges, and UI rendering.

2. **Sequential Gross Deductions:**
   - Platform fee is deducted first:
     $$\text{fee} = \lfloor (\text{gross} \times \text{fee\_bps}) / 10000 \rfloor$$
   - Net proceeds:
     $$\text{net} = \text{gross} - \text{fee}$$
   - Secondary royalty (*Droit de Suite*):
     $$\text{artist} = \lfloor (\text{net} \times \text{royalty\_bps}) / 10000 \rfloor$$
   - Community arts cut:
     $$\text{community} = \lfloor (\text{net} \times \text{community\_bps}) / 10000 \rfloor$$
   - Distributable pool for fractional co-owners:
     $$\text{pool} = \text{gross} - \text{fee} - \text{artist} - \text{community}$$

3. **Fractional Split & Deterministic Dust Sweep:**
   - Co-owner payouts are calculated in fixed cap-table order:
     $$\text{amount}_i = \lfloor (\text{pool} \times \text{bps}_i) / 10000 \rfloor$$
   - Any single-cent integer remainder is allocated to `dust`:
     $$\sum_{i} \text{amount}_i + \text{dust} \equiv \text{pool}$$
   - **Dust Policy:** Single-cent dust deterministically sweeps to the Community Arts Fund:
     $$\text{community\_total} = \text{community} + \text{dust}$$

4. **Total Conservation Equation:**
   - The system asserts that every transaction satisfies exact monetary conservation:
     $$\text{fee} + \text{artist} + \text{community} + \sum_{i} \text{amount}_i + \text{dust} \equiv \text{gross}$$
   - Or equivalently:
     $$\text{artist} + \text{community\_total} + \sum_{i} \text{amount}_i \equiv \text{gross} - \text{fee}$$

5. **Fail-Closed Security:**
   - When a transaction violates covenants or validation rules, `status` is `"REJECTED"`, a non-null `reason_code` is provided, all monetary distributions are zero, `coowners` is empty (`[]`), and no funds move.

---

## 2. Canonical JSON Schema

### Approved Resale (`status: "APPROVED"`)
```json
{
  "status": "APPROVED",
  "reason_code": null,
  "artwork_id": "HFA-101",
  "currency": "USD",
  "gross": 1000000,
  "fee": 0,
  "artist": 150000,
  "community": 30000,
  "dust": 0,
  "pool": 820000,
  "coowners": [
    {
      "owner": "alice",
      "wallet": "0xalice",
      "amount": 492000
    },
    {
      "owner": "bob",
      "wallet": "0xbob",
      "amount": 328000
    }
  ],
  "producing_layer": "bridge/MeTTa"
}
```

### Rejected Resale (`status: "REJECTED"`)
```json
{
  "status": "REJECTED",
  "reason_code": "BELOW_RESERVE",
  "artwork_id": "HFA-101",
  "currency": "USD",
  "gross": 200000,
  "fee": 0,
  "artist": 0,
  "community": 0,
  "dust": 0,
  "pool": 0,
  "coowners": [],
  "producing_layer": "bridge/MeTTa"
}
```

---

## 3. Field Specifications

| Field | Type | Description |
| :--- | :--- | :--- |
| `status` | `string` | Verdict: `"APPROVED"` or `"REJECTED"`. |
| `reason_code` | `string \| null` | `null` if approved; machine-readable reason code if rejected. |
| `artwork_id` | `string` | Unique asset identifier matching `data/artworks.json` (e.g. `"HFA-101"`). |
| `currency` | `string` | ISO currency code (e.g. `"USD"`, `"KES"`). Must match reserve currency. |
| `gross` | `integer` | Gross resale price in minor units (cents). |
| `fee` | `integer` | Platform fee deducted first (`(/ (* gross fee_bps) 10000)`). |
| `artist` | `integer` | Artist secondary royalty payout in cents (`Droit de Suite`). |
| `community` | `integer` | Base community preservation cut in cents. |
| `dust` | `integer` | Single-cent integer remainder swept to community fund (`pool - sum(coowners)`). |
| `pool` | `integer` | Distributable pool for fractional co-owners (`gross - fee - artist - community`). |
| `coowners` | `array[object]` | Ordered list of co-owner payouts: `owner` (`string`), `wallet` (`string`), and `amount` (`integer` cents). |
| `producing_layer` | `string` | The system layer responsible for the decision (`"bridge/MeTTa"`, `"audit_log"`, `"bridge_fail_closed"`, or `"parser"`). |

---

## 4. Reason Codes Reference

The symbolic engine and bridge emit standard reason codes when rejecting a proposal:

| Reason Code | Origin | Meaning |
| :--- | :--- | :--- |
| `BELOW_RESERVE` | Symbolic Rule | Proposed gross sale price is below the registered reserve price floor covenant. |
| `OVERRIDE_BELOW_FLOOR` | Symbolic Rule | A manager override attempted to set an artist royalty lower than the contractual floor covenant. |
| `OVERRIDE_NOT_ALLOWED` | Symbolic Rule | A manager override attempted to reduce the community fund allocation. |
| `ARTWORK_CONTESTED` | Symbolic Rule | Artwork status is marked `CONTESTED` (e.g., active legal dispute or probate claim). |
| `UNSUPPORTED_CURRENCY` | Symbolic Rule | Settlement currency does not match the artwork's registered reserve currency. |
| `DUPLICATE_NONCE` | Gateway / Audit | Replay attack detected; transaction nonce has already been settled. |
| `ENGINE_UNAVAILABLE` | Bridge Fail-Closed | MeTTa engine returned empty atom set, unmapped entity, timeout, or runtime error; execution halted safely. |
| `LLM_MALFORMED_OUTPUT` | Parser / Intake | Natural language bid could not be deterministically parsed into valid transaction parameters, or LLM output is malformed. |
| `INVALID_AMOUNT` | Input Validation | Gross amount is non-integer, negative, zero, or contains forbidden float/boolean types. |
| `AMOUNT_ABOVE_CAP` | Policy Rule | Proposed gross exceeds maximum supported transaction cap ($10,000,000.00 / 1,000,000,000 cents). |
| `CAP_TABLE_INVALID` | Policy Rule | Cap table shares do not sum to 10,000 bps or deductions equal/exceed 10,000 bps. |

---

## 5. Test Fixtures Reference & Producing Layers

Canonical proof fixtures generated via `scripts/generate_proof_fixtures.py` are stored in:
`tests/fixtures/proofs/`

| Fixture File | Scenario | Producing Layer | Status | Key Verification Point |
| :--- | :--- | :--- | :--- | :--- |
| `sc01_standard_resale.json` | SC-01 | `bridge/MeTTa` | `APPROVED` | Gross 10,000 USD (1,000,000¢); artist 150,000¢; comm 30,000¢; pool 820,000¢ (alice 492,000¢, bob 328,000¢). |
| `sc02_below_reserve.json` | SC-02 | `bridge/MeTTa` | `REJECTED` | Gross 200,000¢ < reserve 300,000¢ -> `BELOW_RESERVE`. |
| `sc03_prompt_injection.json` | SC-03 | `bridge/MeTTa` | `APPROVED` | Rogue 0% prompt ignored; stored 1200 bps applies -> USD 720.00 (72,000¢) royalty. |
| `sc04_manager_override.json` | SC-04 | `bridge/MeTTa` | `APPROVED` | HFA-103 sold at USD 50,000 (5,000,000¢) vs USD 40,000 reserve; estate override 1200 bps -> 600,000¢. |
| `sc05_override_below_floor.json` | SC-05 | `bridge/MeTTa` | `REJECTED` | Override 500 bps < floor 1000 bps -> `OVERRIDE_BELOW_FLOOR`. |
| `sc06_dust_split.json` | SC-06 | `bridge/MeTTa` | `APPROVED` | TEST-DUST gross 10,001¢; cap table 3333/3333/3334; dust 1¢ swept to community fund. |
| `sc07_duplicate_nonce.json` | SC-07 | `audit_log` | `REJECTED` | Nonce already recorded in audit log; blocked at intake -> `DUPLICATE_NONCE`. |
| `sc08_metta_unavailable.json` | SC-08 | `bridge_fail_closed` | `REJECTED` | Unknown entity / empty atom set returned by engine; fails closed -> `ENGINE_UNAVAILABLE`. |
| `sc09_llm_unavailable.json` | SC-09 | `parser` | `APPROVED` | Offline execution; deterministic parser extracts integer bid parameters without LLM. |
