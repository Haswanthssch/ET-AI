# ETAI — Manual Testing Guide

A step-by-step walkthrough of **every feature in every role**, what to click, and what you
should see. Follow it top to bottom the first time; after that, use the checklist at the end.

> **Important — this is DEMO mode.** All AI endpoints return canned/fake data (no GROQ key
> needed). Some values are **randomised on every call** (noted below), others are **fixed**.
> So "the numbers changed when I refreshed" is expected behaviour, not a bug.

---

## 0. Before you start

### 0.1 Start both servers

**Terminal 1 — Backend** (run from the project root, with the venv):
```powershell
cd "C:\Users\haswa.HASWANTH\Downloads\ET-AI-master"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8000
```
Wait ~15 seconds (it loads TensorFlow). You want to see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 — Frontend** (separate terminal):
```powershell
cd "C:\Users\haswa.HASWANTH\Downloads\ET-AI-master\frontend"
npm run dev
```
You want to see `✓ Ready` and `Local: http://localhost:3000`.

> Tip: don't edit `next.config.mjs` while the dev server is running — it can crash on the
> auto-restart. If port 3000 says "already in use", a server is already running — just open it.

### 0.2 Sanity checks (optional but recommended)

- Backend health → open http://localhost:8000/health → should show `{"status":"ok", ...}`
- API playground → open http://localhost:8000/docs → interactive Swagger UI for every endpoint
- Frontend → open http://localhost:3000 → the landing page loads

### 0.3 Demo accounts (password is `etai123` for all)

| Email | Roles | What happens at login |
|---|---|---|
| `admin@etai.com` | executive, procurement, engineer, qa_qc, admin | Shows a **role picker** — you choose one |
| `exec@etai.com` | executive | Straight into Executive dashboard |
| `procure@etai.com` | procurement | Straight into Procurement dashboard |
| `engineer@etai.com` | engineer | Straight into Engineer dashboard |
| `qa@etai.com` | qa_qc | Straight into QA/QC dashboard |

> **Good to know:** once you're logged in (with **any** account), the left sidebar shows **all
> four** dashboards and you can click into any of them. There is no per-role lockout in the UI —
> the role only decides which dashboard you land on first. So the fastest way to test everything
> is to log in as `admin@etai.com`, pick any role, then use the sidebar to visit all four.

---

## 1. Landing page — http://localhost:3000

**What to do:**
1. Read the hero / role cards.
2. Click the link to **Sign in** → should go to `/login`.
3. Click the **API docs** link (if present) → should open http://localhost:8000/docs.

**Expected:** Marketing-style page describing the 4 personas. Everything is navigational only.

---

## 2. Login flow — http://localhost:3000/login

The form is pre-filled with `admin@etai.com` / `etai123`.

### 2.1 Multi-role login (admin)
1. Leave the pre-filled `admin@etai.com` / `etai123`.
2. Click **Sign in**.
3. **Expected:** a "Choose a role to continue" grid appears with 5 buttons
   (Executive, Procurement, Engineer, QA/QC, Admin). The Sign-in button now says **Continue**
   and is disabled until you pick a role.
4. Click a role (e.g. **Executive**) → it highlights in that role's colour → click **Continue**.
5. **Expected:** you land on that role's dashboard.

### 2.2 Single-role login (auto-redirect)
1. Change the email to `engineer@etai.com`, password `etai123`.
2. Click **Sign in**.
3. **Expected:** no role picker — you go straight to the Engineer dashboard.
4. Repeat with `exec@`, `procure@`, `qa@` to confirm each lands on its own dashboard.

### 2.3 Error cases (these SHOULD fail — that's the test)
- **Wrong password:** email `admin@etai.com`, password `wrong` → **Sign in** →
  expect a red error box ("Incorrect username or password").
- **Unknown user:** email `nobody@etai.com` → expect the same red error.
- **Backend stopped:** stop Terminal 1, then try to log in → expect an error mentioning
  "Is the backend running on :8000?". Restart the backend afterwards.

### 2.4 Auth guard
1. While **logged out**, type a dashboard URL directly, e.g. http://localhost:3000/executive.
2. **Expected:** you're bounced back to `/login` (you can't view a dashboard without a session).

---

## 3. Shared UI (present on every dashboard)

- **Left sidebar:** logo (click → landing page), 4 dashboard links (Executive, Procurement,
  Engineer, QA/QC), your email + current role at the bottom, and a **Sign out** button.
- **Test navigation:** click each of the 4 sidebar links → the main area and the coloured hero
  banner change per role (rose/amber = Executive, amber = Procurement, orange = Engineer,
  teal = QA/QC). The active link is highlighted.
- **Test sign out:** click **Sign out** → you return to `/login` and can no longer open a
  dashboard URL directly (see 2.4).

---

## 4. Executive dashboard — `/executive`

**Purpose:** program-level health, live risk alerts, and critical-path impact.
**Data source:** `GET /v1/executive-summary` (fixed) + `POST /v1/predict-risk` for GEN-CAT-01
(**randomised each load**).

**What to look at / test:**
1. **Project line** at top → "Hyperscale Data Centre — Phase 1 (24 MW)".
2. **KPI tiles (4):** Schedule Health (82%), Projected Slip (18 days, hint "Driven by
   GEN-CAT-01"), Critical NCRs (3), Commissioning (64%). These are fixed.
3. **Live Risk Alerts (large card):** 3 alerts with severity badges —
   - Critical: *GEN-CAT-01 on Customs Hold* (Source: Risk Engine)
   - Major: *Voltage tolerance non-conformance* (Source: Compliance Agent)
   - Info: *Tier III commissioning on track* (Source: Commissioning QA)
   Each shows an equipment tag chip and a "Source:" line.
4. **Risk Health Trend:** a small sparkline (7 points) ending at **82%**.
5. **RFI SLA card:** avg response `6.4h` vs target `24h`, and `91%` on-time.
6. **Phase Progress:** 5 bars — Civil 100, Structural 96, MEP 74, Electrical 58,
   Commissioning 22.
7. **Critical Path Cascade card:** 3 stat boxes — **slip days**, **tasks hit**, **delay prob %**
   — plus a "Top mitigation" sentence.
   - **Test the randomness:** press **F5** / reload the page a few times → the three numbers in
     this card (and the mitigation wording) **change every time**, because they come from the
     random risk engine. The rest of the page stays the same. This proves the risk endpoint is
     being called live.

**Pass criteria:** page loads without the red "backend running?" banner; all cards render;
the cascade numbers change on reload.

---

## 5. Procurement dashboard — `/procurement`

**Purpose:** supply-chain visibility + vendor spec compliance.
**Data source:** `GET /v1/supply-chain` (fixed) + `POST /v1/compliance` (fixed).

**What to look at / test:**
1. **Supply KPI tiles (4):** Tracked Items (5), At Risk (2), On Critical Path (3),
   Customs Holds (1).
2. **Supply Chain Visibility table (5 rows).** Check the columns Tag / Equipment / Vendor /
   Status / Delay / ETA / Risk. Things to verify:
   - `GEN-CAT-01` (Caterpillar) → **Customs Hold**, **+18d**, **CRITICAL** risk, has a **CP**
     (critical-path) chip next to the tag.
   - `SWGR-M1` (Schneider) → **Delivered**, "on time" in teal.
   - Status pills are colour-coded (Customs Hold = red, In Transit = amber, Manufacturing =
     blue, Delivered = teal). Risk badges are colour-coded by severity.
3. **Spec Compliance Checker (interactive):**
   - It's pre-filled with a tag (`GEN-CAT-01`) and a submittal paragraph.
   - Click **Run compliance check** → button shows "Analysing…" → then the **Findings** card
     on the right fills in.
   - **Expected findings (fixed):** verdict badge **NON-COMPLIANT** (red) + a "✓ critic
     self-heal" note; a summary sentence; then 3 findings:
     - Critical — voltage tolerance ±8% exceeds TIA-942-B §7.3.4 (±5%)
     - Major — UPS battery room ventilation below 15-min exhaust
     - Minor — missing efficiency curve at 25% load
     Each finding has a severity badge + a mono spec reference on the right.
   - **Try editing** the tag and submittal text and re-running → the verdict/findings stay the
     same (demo returns fixed content) but the **equipment tag echoes your input** (upper-cased)
     at the top of the response object. This confirms your input is sent to the backend.

**Pass criteria:** table shows 5 rows with correct badges; running the checker produces the
NON-COMPLIANT findings card.

---

## 6. Engineer dashboard — `/engineer`

**Purpose:** RFI copilot (cited Q&A) + drawing/blueprint deviation analysis.
**Data source:** `POST /v1/rfi-copilot` (keyword-based) + `POST /v1/vision-parse` (file upload).

### 6.1 RFI Copilot (chat)
1. On first load you see 4 suggestion chips.
2. **Click a suggestion**, e.g. *"How was the MEP coordination conflict in IT Hall A resolved?"*
   - **Expected:** your question appears as a right-aligned bubble; a "Retrieving & reasoning…"
     loader shows briefly; then an assistant answer appears with **citation chips**
     (e.g. `RFI-1087`, `TIA-942-B §7.3.2`).
3. **The answer depends on keywords** — try these to see different responses:
   | Type something containing… | You should get… |
   |---|---|
   | "MEP" or "coordination" | chilled-water re-route answer, cites RFI-1087 / TIA-942-B §7.3.2 |
   | "TIA" or "cable tray" | 4-inch separation rule, cites §7.3.2 / §7.3.4 |
   | "critical" or "RFI" | list of 6 grounding RFIs |
   | "seismic" or "bracing" | lateral bracing answer, cites IBC-2021 §13.3 |
   | anything else (e.g. "hello") | generic 3-document answer |
4. **Type your own** question in the box at the bottom and press **Send** / Enter → confirm it
   responds and every answer carries at least one citation chip.

### 6.2 Vision Parser (file upload)
1. Click the dashed **"Upload drawing to analyse"** box.
2. Pick **any** image or PDF from your machine (content doesn't matter — it's demo mode).
3. **Expected:** button shows "Parsing drawing…", then a result panel appears:
   - System type (e.g. "Electrical SLD"), drawing number / revision / scale, confidence %.
   - A **Deviations** list (2–5 items) with severity badges (Critical/Major/Minor) and spec
     references (TIA-942-B §7.3.2, ASHRAE-90.4, etc.) and a location line each.
4. **Randomness check:** upload again → the system type, drawing number, and deviation count
   change (random demo data). The filename you uploaded is echoed back.

**Pass criteria:** suggestions and typed questions both return cited answers; uploading a file
produces a deviation report.

---

## 7. QA / QC dashboard — `/qa-qc`

**Purpose:** validate a commissioning test log against Uptime Institute Tier requirements and
auto-generate a certificate.
**Data source:** `POST /v1/commissioning` (fixed — always PASS/CERTIFIED in demo).

**What to do / test:**
1. **Target Tier selector:** four buttons — Tier I / II / III / IV. Click one (default is III) →
   it highlights teal.
2. **Test log textarea:** pre-filled with a sample log (generator, UPS, cooling, grounding,
   availability). You can edit it freely.
3. Click **Validate & generate certificate** → button shows "Validating…", then:
   - **Validation Result card:** a big **CERTIFIED** status (teal), and counts of
     passed / failed / critical checks (9 passed, 0 failed, 0 critical in demo).
   - **Checks grid:** ~9 green-tick items (Generator Transfer, UPS Runtime, Cooling Temp, PUE,
     Grounding, Concurrent Maintainability, Availability, etc.).
   - **Tier Compliance Certificate (full-width card):** a formatted certificate text block that
     includes the **Tier you selected**, a random certificate ID, and the test-results summary.
4. **Test the tier reflection:** pick **Tier IV**, click validate again → the certificate text
   now says "TIER IV" (your selection flows through), even though demo always certifies.

**Pass criteria:** validating produces a CERTIFIED result, a checks grid, and a certificate that
reflects the chosen tier.

---

## 8. Optional — test the API directly (no UI)

Open http://localhost:8000/docs and use **"Try it out"** on each endpoint, or use PowerShell:

```powershell
# Login (get a token)
$body = @{ username='admin@etai.com'; password='etai123'; role='executive' } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/auth/token -Method Post -Body $body -ContentType 'application/json'

# Executive summary
Invoke-RestMethod http://localhost:8000/v1/executive-summary

# Supply chain
Invoke-RestMethod http://localhost:8000/v1/supply-chain

# Risk (random each call)
Invoke-RestMethod http://localhost:8000/v1/predict-risk -Method Post -ContentType 'application/json' -Body (@{ equipment_tag='GEN-CAT-01' } | ConvertTo-Json)

# RFI copilot
Invoke-RestMethod http://localhost:8000/v1/rfi-copilot -Method Post -ContentType 'application/json' -Body (@{ query='TIA cable tray separation' } | ConvertTo-Json)

# Compliance
Invoke-RestMethod http://localhost:8000/v1/compliance -Method Post -ContentType 'application/json' -Body (@{ submittal_text='test'; equipment_tag='GEN-CAT-01' } | ConvertTo-Json)

# Commissioning
Invoke-RestMethod http://localhost:8000/v1/commissioning -Method Post -ContentType 'application/json' -Body (@{ target_tier='IV'; test_log_text='sample' } | ConvertTo-Json)
```

---

## 9. Quick test checklist

Copy this and tick as you go:

**Setup**
- [ ] Backend `/health` returns ok
- [ ] Frontend landing page loads
- [ ] `/docs` opens

**Login**
- [ ] admin → role picker appears → pick role → Continue → dashboard
- [ ] exec@ / procure@ / engineer@ / qa@ each auto-land on correct dashboard
- [ ] wrong password shows red error
- [ ] backend-down shows "backend running?" error
- [ ] visiting a dashboard while logged out redirects to /login

**Shared**
- [ ] Sidebar navigates between all 4 dashboards
- [ ] Sign out returns to /login

**Executive**
- [ ] 4 KPI tiles render
- [ ] 3 live alerts with severity + source
- [ ] sparkline + RFI SLA + phase progress render
- [ ] Critical Path Cascade numbers change on reload (random)

**Procurement**
- [ ] 4 supply KPI tiles
- [ ] 5-row supply table; GEN-CAT-01 = Customs Hold + CRITICAL + CP chip
- [ ] Run compliance check → NON-COMPLIANT + 3 findings

**Engineer**
- [ ] Suggestion chip returns a cited answer
- [ ] Typed question returns a cited answer (try MEP / TIA / seismic keywords)
- [ ] Upload a file → deviation report appears

**QA/QC**
- [ ] Pick a tier, edit log, Validate → CERTIFIED result + checks grid
- [ ] Certificate text reflects the selected tier

---

## 10. Things that are *expected*, not bugs

- Random numbers changing on reload (risk cascade, vision parser, certificate ID).
- Compliance always returns **NON-COMPLIANT**; commissioning always returns **CERTIFIED** —
  the demo endpoints return fixed verdicts.
- Any logged-in user can open any of the 4 dashboards (no per-role UI lockout yet).
- A harmless backend log line "error reading bcrypt version" may appear — hashing still works.
- Backend takes ~15s to start (it imports TensorFlow).
