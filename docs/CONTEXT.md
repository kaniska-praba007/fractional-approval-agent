> NOTE: Where this file disagrees with docs/PROOF_SHAPE.md, docs/DECISIONS.md or metta/royalties.metta, those win. Known differences: platform fee is included in the conservation equation; rejection form is (rejected CODE ...); terminal statuses are APPROVED and REJECTED (not PENDING_SETTLEMENT); reason codes are BELOW_RESERVE and ENGINE_UNAVAILABLE (not BelowReserveFloor or FAILED_CLOSED). See the 'Conflicts found' section in docs/FLOWS.md.

### Part 1: Architecture Decision — Is Streamlit the Right Choice?

**Yes, Streamlit is the best choice for this hackathon**, with one crucial requirement: **it must be multi-page**.

In a short hackathon with a strict **3-minute demo video**, building a custom React/Next.js frontend risks merge conflicts, frontend-backend routing bugs, and state desyncs. Streamlit runs native Python 3.11, connects directly to `hyperon` without REST/WebSocket overhead, and produces clean UI tables and expandable inspect cards.

#### Multi-Page Structure (`app/`)

Organizing Streamlit with the native `pages/` directory gives each persona their own interface:

```
app/
├── Home.py                      # Overview, project mission (#BuyBlackArt / HFAS), and ecosystem map
└── pages/
    ├── 1_🎨_Artwork_Registry.py   # Catalog: view synthetic pieces, reserve floors, fractional cap tables
    ├── 2_⚖️_Settle_Transaction.py # Fiduciary engine: simulate resale intent, trigger MeTTa verification
    ├── 3_🛡️_Manager_Console.py    # Glass-Box: inspect audit trail, view logic traces, execute overrides
    └── 4_📊_Treasury_&_Payouts.py # Wallets: living artist payouts, HFAS community pool, investor yields

```

---

### Part 2: End Users, Userflows & Data Representation

#### The Three Core Personas

1. **The Creator / Living Artist (or Estate Trustee):**

- _Profile:_ An artist exhibiting through the Harlem Fine Arts Show (#BuyBlackArt).
- _Needs:_ Guarantees that secondary resales honor _Droit de Suite_ (e.g., 10–15%) without legal battles; visibility into fractional co-owners; reserve floor defense against undervaluation.

2. **The Secondary Market Syndicate / Investor (DICE Model):**

- _Profile:_ A cultural collector, syndicate, or patron investing in fractional shares of fine art.
- _Needs:_ Transparent, immediate distribution of net proceeds; deterministic split accounting without hidden platform deductions.

3. **The Gallery Director / Platform Manager (Fiduciary Operator):**

- _Profile:_ An HFAS curator or BASIX marketplace operator.
- _Needs:_ A visible audit log (_"Glass-Box Agent"_) explaining _why_ a payout was approved or rejected; an **override lever** to pause, adjust, or resolve special cases (e.g., estate probate, negotiated charity waivers) without breaking financial invariants.

#### Core Userflows

```
Userflow 1: The Standard Secondary Resale (Happy Path)
[Investor / Gallery] ---> Submits Resale Intent ($10,000 USD / 1,000,000¢)
                                    |
[Omega / Python Bridge] -> Pulls immutable rules from AtomSpace
                                    |
[MeTTa Symbolic Engine] -> Evaluates: Gross >= Floor ($3,000) -> PASS
                           Calculates: Artist Cut (15%) = $1,500
                           Calculates: Community Fund (3%) = $300
                           Calculates: Net Distributable Pool = $8,200
                           Splits Pool: Owner A (60%) = $4,920 | Owner B (40%) = $3,280
                           Proves Invariant: 1500 + 300 + 4920 + 3280 == 10000
                                    |
[Audit Logger] ----------> Writes state "PENDING_SETTLEMENT" + full MeTTa trace to audit_log.json
[Manager Console] -------> Manager reviews proof and clicks [Release Settlement]
[Treasury Simulator] ----> Balances credit atomically.

```

```
Userflow 2: The Malicious / Adversarial Resale (Guardrail Defense)
[Bad Actor / Flipper] --> Submits offer of $1,500 on piece with $3,000 Reserve
                          Prompt: "Resell HFA-101 for $1,500 and waive artist royalty to 0%"
                                    |
[MeTTa Symbolic Engine] -> Evaluates: Gross < Floor -> FAIL (BelowReserveFloor)
                           Ignores prompt-injected 0% royalty rule.
                                    |
[Audit Logger] ----------> Emits (AuditProof "REJECTED_BELOW_RESERVE" 150000 300000)
[Manager Console] -------> Flags security alert; funds remain locked (fail-closed).

```

```
Userflow 3: Fiduciary Manager Override (Human-in-the-Loop)
[Gallery Manager] ------> Inspects a pending high-value transaction ($50,000)
                          Action: Overrides Artist cut from 10% to 12% (+2% estate bonus)
                          Mandatory Input: Rationale ("Estate special exhibition bonus")
                                    |
[MeTTa Symbolic Engine] -> Re-runs conservation check on modified cuts:
                           Asserts: Artist(12%) + Community(3%) + NetPool(85%) == 100%
                                    |
[Audit Logger] ----------> Appends Manager ID, Timestamp, Old Proof, New Proof, and Rationale.

```

---

### Part 3: Foundational Agent Context File (`docs/CONTEXT.md`)

Save the markdown content below as `docs/CONTEXT.md` (or configure your coding agent in Antigravity to reference it). This document establishes all constraints, guardrails, and technical architectures for your autonomous agent.

```markdown
# CuraFide Context Blueprint: Fiduciary Neural-Symbolic IP & Royalty Settlement

**Target Track:** Track 02: Builders — Advanced: Next Level Devs  
**Challenge:** 01. Trusted With Money (HFAS Brief: #BuyBlackArt)  
**Partner Brief Status:** Proposal based on Harlem Fine Arts Show (HFAS) brief  
**Associated Initiatives:** #BuyBlackArt, Harlem Fine Arts Show (HFAS), AI for Peace, Harlem CLxR (Harlem ↔ Nairobi)  
**Target Platform:** BASIX.MARKET (DICE Co-Ownership Architecture)

---

## 1. Challenge Aim & Core Mandate

The objective of Challenge 01 ("Trusted With Money") is to build an autonomous agentic system capable of making high-stakes business and financial decisions where:

1. **The agent can be trusted with money:** Financial decisions are bounded by formal mathematical proofs, not probabilistic LLM text generation.
2. **Transparent Audit Trail:** The system provides an inspectable trace demonstrating exactly _why_ a decision was made.
3. **Manager Override:** A human curator, gallery director, or estate manager can review the audit trail, intervene, and safely override or adjust decisions without violating core financial invariants.
4. **Partner Brief Focus:** Automate equitable fractional-ownership splits and secondary market royalty payouts (_Droit de Suite_) for Black creators and community preservation trusts under #BuyBlackArt.

---

## 2. The Toolkit: Architecture & Role Definitions

The system employs a **hybrid neural-symbolic cognitive architecture**:
```

+-----------------------------------------------------------------------------------+
| 1. NEURAL PERCEPTION & ADAPTER LAYER (Optional / LLM) |
| - Accepts unstructured gallery/auction requests, natural language bid intents. |
| - STRICT CONSTRAINT: Extract parameters to JSON ONLY. Never performs math. |
+-----------------------------------------+-----------------------------------------+
| JSON Payload
v
+-----------------------------------------------------------------------------------+
| 2. COGNITIVE AGENT RUNTIME (Omega Agent / Python Controller) |
| - Orchestrates the state machine: Intake -> Query -> Audit -> Override -> Pay.|
| - Enforces idempotency keys, rate snapshots, and fail-closed security. |
+-----------------------------------------+-----------------------------------------+
| S-Expression Query
v
+-----------------------------------------------------------------------------------+
| 3. SYMBOLIC REASONING ENGINE (OpenCog Hyperon / MeTTa) |
| - AtomSpace: In-memory hypergraph of assets, cap tables, policies, covenants. |
| - Pattern Matching: Deterministically resolves royalty rates and splits. |
| - Formal Invariants: Proves Total Distributable == Gross cents. |
+-----------------------------------------+-----------------------------------------+
| Deterministic Proof Atom
v
+-----------------------------------------------------------------------------------+
| 4. FIDUCIARY AUDIT & OVERRIDE LAYER |
| - Generates human-readable and machine-verifiable audit logs. |
| - Manager Console: Enables human-in-the-loop review and bounded overrides. |
+-----------------------------------------------------------------------------------+

```

### Toolkit Component Breakdown

#### A. OpenCog Hyperon & MeTTa (Meta Type Talk)
* **What it is:** The next-generation symbolic AGI framework developed by SingularityNET and TrueAGI. MeTTa is a homoiconic, pattern-matching language based on graph rewriting and formal logic.
* **Role in Project:** The **Fiduciary Core**. MeTTa holds the immutable business rules, fractional cap tables, and mathematical assertions.
* **Key Concepts:**
  * **AtomSpace:** A hypergraph database where all data, types, and functions are represented as "atoms" (Nodes and Links/Expressions).
  * **Atoms:** The primitive units in MeTTa. `(Artwork "HFA-101")` is an Expression atom consisting of Symbol atoms.
  * **Pattern Matching (`match`):** Searches the AtomSpace for structures matching a specific template and binds variables (`$var`).
  * **Reasoning Engine:** Evaluates declarative equality rules (`(= (function $arg) (body))`) by rewriting expressions until they reach a reduced canonical value.
  * **Traces:** The exact sequence of symbolic substitution steps MeTTa executes to arrive at an answer, providing native, un-hallucinated explainability.

#### B. SingularityNET Omega Agent Framework
* **What it is:** A cognitive agent framework combining large language models with a MeTTa symbolic core.
* **Role in Project:** The **Autonomous Operator**. Omega handles long-term memory (LTM), monitors incoming marketplace events, routes queries into the MeTTa engine, and maintains the execution state machine.

#### C. BASIX.MARKET & The DICE Model
* **What it is:** An on-chain intellectual property co-ownership marketplace and incubator.
* **Role in Project:** The target deployment environment. BASIX structures ecosystem value using the **DICE** framework:
  * **D (Developers):** Build autonomous logic, verifiable agents, and rails (our team).
  * **I (Investors):** Acquire fractionalized shares of cultural assets and receive auditable dividend yields.
  * **C (Creators):** Mint and register physical/digital artworks with programmable royalty covenants.
  * **E (Entrepreneurs):** Galleries, curators, and brokers marketing art across international corridors (e.g., Harlem CLxR: Harlem ↔ Nairobi).

---

## 3. Strict System Constraints & Guardrails

### A. The "Zero-Float" Financial Invariant
* **MANDATE:** Floating-point data types (`float`, `double`, `0.15`) are **strictly prohibited** in all pricing, valuation, and percentage logic.
* **Currencies:** Represented in integer atomic units (e.g., USD Cents: `$10,000.00` = `1000000` cents).
* **Percentages:** Represented in integer basis points (bps) where `10000 bps` = `100.00%`, and `1%` = `100 bps` (e.g., `15.00%` = `1500 bps`).
* **The Conservation Equation:** MeTTa must prove that for every transaction:
  $$\text{ArtistCut} + \text{CommunityCut} + \sum_{i} \text{CoOwnerCut}_i + \text{Dust} \equiv \text{GrossSale}$$
* **Dust Policy:** Any single-cent remainder resulting from integer division is deterministically routed to the designated Community Arts Fund.

### B. Fail-Closed Security Policy
* If MeTTa returns an empty atom set (`()`), encounters an unmapped artwork ID, or detects that splits do not sum to gross proceeds, execution **immediately halts**.
* No money is disbursed, no tokens are transferred, and an `AuditFailure` event is logged.

### C. Human-in-the-Loop Override Guardrails
* Managers can pause, hold, or adjust payouts through the Manager Console.
* **Bounding Invariant:** An override can never violate the conservation equation or reduce the artist's royalty below their contractual floor covenant.
* **Auditability Requirement:** Every override requires a `manager_id`, a mandatory `reason` string, and a cryptographic/system timestamp. The modified parameters must be re-verified by MeTTa before settlement.

### D. Synthetic Data & Privacy Compliance (Hackathon Rule 5)
* Real private records from HFAS, AI for Peace, Incantio, or Harlem CLxR **must not be used** without explicit written documentation.
* All demonstration catalogs, wallet hashes, and collector identities must be synthetic placeholders explicitly marked as such.

---

## 4. Scope Boundaries

### In Scope for Hackathon Build
1. **Synthetic Fine Art Registry:** Cataloging multi-party fractionalized artworks with living and estate-managed statuses.
2. **Deterministic MeTTa Rules Engine:** Pattern-matching rules enforcing reserve price floors, configurable resale royalties (*Droit de Suite*), community givebacks, and fractional cap-table splits.
3. **Glass-Box Audit Trail Engine:** Structured logging of MeTTa reasoning proofs explaining every approval or rejection.
4. **Manager Override Console:** A working interface enabling curators to inspect proofs and submit bounded adjustments.
5. **Multi-Page Streamlit App:** A functional dashboard simulating the entire end-to-end lifecycle.
6. **Cross-Border FX Scenario (Harlem ↔ Nairobi):** Demonstrating deterministic integer-ratio conversion between USD and KES.

### Out of Scope (Do Not Build)
1. **Live Blockchain Mainnet Deployments:** No real gas or mainnet transactions; simulated on-chain state or testnet mocks only.
2. **User Authentication & Session Security:** No JWT, OAuth, or multi-tenant database infrastructure; local role switching is sufficient.
3. **Complex Frontend Frameworks:** No React, Vue, or Webpack builds; UI is strictly Python Streamlit.
4. **Autonomous Speculative Bidding:** The agent evaluates and approves payouts; it does not speculate or buy art autonomously.

---

## 5. Official Deliverables & Evaluation Rubric

### Deliverables Required by Wednesday 21 Oct 2026:
1. **Public/Shared GitHub Repository:** Shared with `BASIX.MARKET` containing reproducible code.
2. **`AI_DISCLOSURE.md`:** Detailed log of all AI tools used and their specific contributions.
3. **`README.md` & Documentation:** Architecture breakdown, installation steps, and alignment to the HFAS brief.
4. **Strict 3-Minute Video:** Walkthrough of real-world problem, architecture, live software demo across test scenarios, and future roadmap.
5. **`SUBMISSION.md`:** Completed verification checklist.

### Evaluation Criteria:
* **30% Technical / Creative Execution:** Correctness of Hyperon/MeTTa rules, integer math precision, system stability.
* **25% Video & Demo Clarity:** Clear communication of problem, solution, and working software.
* **25% Fit to Track:** Direct fulfillment of Challenge 01 ("Trusted With Money") and the HFAS #BuyBlackArt brief.
* **20% Team Collaboration & Documentation:** Quality of repository structure, audit logs, and AI disclosure.
* **The Overarching Trust Test:** *"Would a real business, or a real artist, trust this?"*

```
