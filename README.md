# BrandShield AI
> **"Detect impersonation before it harms your brand."**

Digital Risk Protection platform designed and engineered for the **Kampus.VC / ByteXL Hackathon**.
Focused specifically on **Social Media Monitoring** and **App Store Monitoring** to detect brand impersonation, rogue apps, fake customer support channels, and coordinated phishing campaigns.

---

## 🛡️ Core Capabilities & Challenge Alignment

| Hackathon Requirement | BrandShield AI Implementation |
|---|---|
| **1. Brand Profile & Official Registry** | Full brand management, logo ingestion for perceptual hashing, official social handles, official app packages, official domains, and multi-step onboarding wizard. |
| **2. Social Media Monitoring** | Real-time monitoring across Instagram, Facebook, X, LinkedIn, YouTube, and TikTok. Look-alike detection, logo matching, bio intent extraction, and triage queues. |
| **3. App Store Monitoring** | Google Play and Apple App Store rogue app detection, unauthorized developer flag, package spoofing identification, and description analysis. |
| **4. Official Asset Exclusion (Rule)** | **Zero False Positives**: Verified official assets are checked first, guaranteed `0 Risk`, and excluded from threat generation. |
| **5. Look-Alike & Homoglyph Detection** | RapidFuzz token/Levenshtein matching, character swaps (e.g. `ABCBnak`), added words (`support`, `care`), spacing/separator changes, and Unicode/Cyrillic homoglyphs. |
| **6. Logo Similarity Engine** | Perceptual difference hashing (`dHash`) using Pillow with Hamming distance calculation (0–100% visual resemblance). |
| **7. Multi-Signal Detection Engine** | Weighted multi-factor evaluation combining Name, Username, Logo, Description, Developer Mismatch, and Registry Mismatch into a transparent 0–100 score. |
| **8. Customer Impact Intelligence** | Distinct from technical threat risk. Identifies customer-targeting phrases (`Send OTP`, `Update KYC`, `Contact customer care`) to quantify consumer fraud exposure. |
| **9. Cross-Platform Threat Campaigns** | Threat correlation engine that clusters multi-channel impersonations (Instagram + Facebook + Play Store) into unified campaigns with an interactive relationship topology graph. |
| **10. AI Threat Investigator & Evidence** | Automated forensic case files, recommended triage actions, and downloadable cryptographically signed Evidence Packages (SHA-256) with ready-to-submit DMCA/Abuse takedown notices. |

---

## ⚡ Technology Stack

- **Frontend**: React (Vite), Tailwind CSS, Lucide React, Recharts, Axios, React Router v7
- **Backend**: Python 3.14, FastAPI, Motor (Async MongoDB), PyMongo, RapidFuzz, Pillow (PIL), Pydantic v2
- **Database**: MongoDB (live connection at `mongodb://localhost:27017`)
- **Architecture**: Microservice-ready REST API with reverse proxying and reactive polling updates

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- MongoDB running locally on `localhost:27017`

### 2. Configure environment files

Environment files are local and must not be committed. The checked-in `.env.example` files are templates:

- For local development, copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env.local`. Set a private `JWT_SECRET_KEY` in `backend/.env`, generated with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. The backend uses a temporary random key if this is blank, so set a value to keep local sessions valid between restarts.
- In PowerShell, create the local files from the templates with `Copy-Item backend\.env.example backend\.env` and `Copy-Item frontend\.env.example frontend\.env.local`. For Docker Compose, use `Copy-Item .env.example .env` from the repository root.
- To enable Google sign-in locally, create an OAuth 2.0 **Web application** client in Google Cloud Console and add `http://localhost:5173` as an authorized JavaScript origin. Copy its client ID to `GOOGLE_CLIENT_ID` in `backend/.env` and `VITE_GOOGLE_CLIENT_ID` in `frontend/.env.local`. Restart both servers after changing these values. The client ID is public; this ID-token flow does not need a Google client secret or redirect URI.
- For Docker Compose, copy the root `.env.example` to `.env`. Set a unique `JWT_SECRET_KEY` and replace `FRONTEND_URL` with the deployment's public HTTPS URL, without a trailing slash. For local Compose only, also set `ENVIRONMENT=development` and `FRONTEND_URL=http://localhost`. Set `GOOGLE_CLIENT_ID` and `VITE_GOOGLE_CLIENT_ID` to the same client ID. The `VITE_*` values are embedded during the Docker image build, so rebuild after changing them with `docker compose up --build -d`.
- For a single-container deployment using the repository's root `Dockerfile`, provide `MONGO_URI` for a reachable MongoDB service, pass `VITE_GOOGLE_CLIENT_ID` as a Docker **build argument**, and provide `JWT_SECRET_KEY`, `FRONTEND_URL`, and `GOOGLE_CLIENT_ID` as runtime environment variables. Set `FRONTEND_URL` to the site's public HTTPS URL. The production backend exits at startup if the MongoDB URL is local, the JWT secret is missing/placeholder, or the public frontend URL is localhost/placeholder.
- The frontend calls `/api` on the same origin by default, so it follows the deployed hostname and HTTPS scheme without a localhost URL. Only when hosting the API on a separate public origin should you set `VITE_API_BASE_URL` to that API's full public URL ending in `/api`. Logo links are also relative and work behind the configured Nginx proxy.
- SMTP variables are only needed to send password reset and email verification messages. Social-platform API tokens are only needed for live integrations; the demo/sandbox modes can be used without them.

For production Google sign-in, add the deployed site's exact HTTPS origin (for example `https://brand.example.com`) to the Google OAuth client's authorized JavaScript origins. Do not add URL paths or a trailing slash there. `FRONTEND_URL` controls email links; the Google authorized origin controls where Google will render the sign-in button. Keep SMTP and third-party API secrets server-side, never in frontend `VITE_*` variables.

#### Fix Google `Error 400: origin_mismatch` on Vercel

1. In the Vercel project, set `VITE_GOOGLE_CLIENT_ID` to the same Web application client ID used by the backend's `GOOGLE_CLIENT_ID`, for **Production** and any Preview environments you use.
2. In Google Cloud Console → Google Auth Platform → Clients → that exact client ID, add each site origin under **Authorized JavaScript origins**, for example `http://localhost:5173` and `https://your-project.vercel.app`. Add a custom domain separately if you use one. Enter only scheme and hostname—no `/login`, path, or trailing slash.
3. Save the OAuth client, trigger a fresh Vercel deployment so Vite rebuilds with the configured client ID, then open the deployed site at the exact authorized hostname. Preview deployment URLs have their own origins and must be added separately if you sign in from them.
4. This app uses Google's popup ID-token flow: click **Continue with Google**, choose a Google account if prompted, and the app submits the verified token to the backend and navigates to the dashboard. It does not ask for the account's Google password in this app. Authorized redirect URIs are not used by this popup flow.

### 3. Backend Setup & Startup
```bash
cd backend
# Install dependencies
python -m pip install fastapi uvicorn pymongo motor rapidfuzz python-multipart pillow httpx

# Start FastAPI server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- API Documentation (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 4. Frontend Setup & Startup
```bash
cd frontend
# Install dependencies
npm install

# Start Vite dev server on port 5173
npm run dev -- --host
```
- Web Application: [http://localhost:5173/](http://localhost:5173/)

---

## 🏆 Hackathon Winning Demo Flow (Step-by-Step)

1. **Open Application**: Navigate to `http://localhost:5173/` in your browser.
2. **One-Click Demo Environment**: Click the **"Load Demo"** button on the top header. This populates **ABC Bank** with verified official assets, realistic threats, active campaigns, and alerts.
3. **Verify Official Asset Exclusion (Rule Proof)**:
   - Click **"Scan Link"** in the top bar.
   - Click the preset: `Official Instagram (Safe Test)` (`https://instagram.com/abcbank`).
   - Click **"Scan Link"**.
   - Notice the result: **SAFE (0/100 Risk)** with the banner: *"Matches official verified asset registry. Excluded from threat monitoring."*
4. **Detect Look-alike Social Threat**:
   - In the Scan modal, click preset: `@abcbank_support (Suspicious Social)`.
   - Click **"Scan Link"**.
   - Watch the animated 5-step detection engine evaluate tokens, homoglyphs, and customer targeting.
   - Result: **94.7/100 CRITICAL THREAT**, **90.0/100 Customer Impact**, **96% Confidence**.
   - View the **Official vs Suspicious side-by-side comparison** and reasons flagged.
5. **Generate Certified Evidence Package**:
   - Click **"Generate Evidence"**.
   - Inspect the tamper-evident SHA-256 digital signature, side-by-side audit, and legal takedown notice template.
   - Click **"Copy Notice"** or **"Export Evidence (JSON)"**.
6. **Detect Rogue Mobile Application**:
   - Click **"Scan Link"** and select the preset: `Fake Google Play App (Dev Mismatch)`.
   - The engine automatically routes to the App Store Engine.
   - Result flags **Developer Mismatch**: Unauthorized developer `Unknown Apps Ltd` publishing fake banking app.
7. **Inspect Cross-Platform Campaign Correlation**:
   - Navigate to **"Campaigns"** in the sidebar.
   - View the **ABC Bank Customer Support Impersonation Campaign** correlating threats across Instagram, Facebook, and Google Play.
   - Explore the **Visual Relationship Graph** connecting the Brand Node to platform conduits and rogue developer entities.
8. **Investigate Threat Dossier**:
   - Navigate to **"Investigations"** and open the active case file.
   - Review the executive threat summary, preserved forensic items, and investigation timeline.
9. **Triage & Status Transitions**:
   - Navigate to **"Threat Center"**.
   - Review, Resolve, or Mark threats as Legitimate (False Positive Protection).
   - Watch the Dashboard and Analytics counters update dynamically.
10. **Add New Brand Wizard**:
    - Click **"+ Add Brand"** to launch the 6-step wizard and register a brand with official assets from scratch.

---

## 📊 BrandShield AI 4-Metric Signature

Every threat evaluated in BrandShield AI is scored across 4 distinct dimensions:

1. **Threat Risk (0–100)**: Multi-signal technical threat score (Name + Logo + Description + Developer mismatch).
2. **Customer Impact (0–100)**: Quantifies danger to consumers (Credential theft, OTP interception, KYC harvesting).
3. **Algorithmic Confidence (0–100%)**: Statistical certainty of the match.
4. **Campaign Risk (0–100)**: Aggregated risk reflecting coordinated multi-platform operations.

---

## 🛡️ False Positive Protection Architecture

- **Official Registry Exclusions**: Verified handles, bundle IDs, and domains are whitelisted with priority 0.
- **Multi-Signal Requirement**: Name similarity alone never creates a critical threat without secondary confirmation (logo theft, developer mismatch, or credential harvesting).
- **Analyst Feedback Loop**: Marking an asset as "Legitimate" logs analyst feedback into the database to tune detection thresholds.

---

## 📸 Instagram Profile Risk Analysis & Impersonation Detection

BrandShield AI includes a specialized module for **Instagram Profile Risk Analysis & Impersonation Detection**. It enables brand protection analysts to evaluate Instagram accounts using **officially supported Meta Graph API telemetry** coupled with an extensible AI risk engine.

### 🌟 Key Architectural Principles

1. **Verification Status Is Not an Absolute Rule**:
   - The engine **never assumes**:
     - *Verified account = Safe* (Compromised or purchased verified accounts can run malicious credential campaigns).
     - *Unverified account = Fake* (Millions of legitimate individual and standard accounts are unverified).
   - Verification status contributes **only 0–5 points** out of the 100-point composite score.
2. **AI-Estimated Risk Categorization**:
   - **LOW RISK (0–29)**: Standard organic account or benign unrelated handle.
   - **MEDIUM RISK (30–59)**: Look-alike username or brand resemblance without active phishing payloads.
   - **HIGH RISK (60–79)**: Unauthorized brand representation, follower asymmetry, and deceptive bio links.
   - **CRITICAL RISK (80–100)**: Look-alike account actively soliciting OTPs, passwords, or redirecting to credential harvest portals.
3. **Official Asset Registry Exclusion (0 Risk)**:
   - When an analyzed username matches an official asset registered in the Brand Profile, the engine automatically flags it as **Verified Official Brand Asset**, assigning a **0/100 Risk Score** and excluding it from threat generation.
4. **Official Meta Graph API Integration (v21.0 / v22.0)**:
   - Uses the official `business_discovery.username()` endpoint:
     ```http
     GET https://graph.facebook.com/v21.0/{instagram_business_account_id}?fields=business_discovery.username({target_username}){username,website,name,profile_picture_url,biography,follows_count,followers_count,media_count}&access_token={token}
     ```
   - **Zero Scraping**: Complies strictly with Meta Platform Terms. Access tokens are secured server-side and never exposed to the frontend.
   - **Resilient Demo Mode**: If Meta API tokens or permissions (`instagram_basic`, `pages_show_list`, `business_management`) are not configured, the service falls back gracefully to authentic demo telemetry.

### 🔬 Multi-Signal Risk Engine Weights (100-Point Model)

| Signal Category | Maximum Weight | Forensic Indicators Evaluated |
|---|---|---|
| **1. Verification Status** | 5 pts | Meta verified badge (+0 pts verified, +2.5 pts unverified). |
| **2. Profile Completeness** | 10 pts | Presence of profile photo, biography, account type, display name. |
| **3. Username Look-alike Similarity** | 20 pts | Levenshtein distance, character swaps, added keywords (`support`, `help`, `care`). |
| **4. Brand Identity & Alias Resemblance** | 25 pts | Brand name matching, official registry distance, homoglyph substitutions. |
| **5. Follower/Following Anomalies** | 15 pts | Mass-following automation, follower asymmetry (following thousands with few followers). |
| **6. Profile Consistency & Bio Link** | 10 pts | External URL comparison against official brand portal, URL shortener detection (`bit.ly`, `wa.me`). |
| **7. Customer Phishing Intent** | 15 pts | Urgency triggers in bio (`Send OTP`, `Update KYC`, `Urgent DM`, `Unblock account`). |

### 🧪 Pre-Configured Evaluation Presets

Analysts can instantly test three scenarios with one click in the UI:
- **`@abcbank_official`** (Low Risk / 0 pts): Verified official brand asset registered in ABC Bank directory.
- **`@abc_bank_help`** (Medium Risk / ~42 pts): Unverified look-alike account providing unofficial support.
- **`@abc_bank_support_official`** (High/Critical Risk / ~78 pts): Fake customer care soliciting OTPs with a shortened link.

### 🔌 API Endpoints

- `POST /api/instagram/analyze`: Analyze an Instagram handle or profile URL against a brand.
- `GET /api/instagram/history`: Retrieve recent persisted Instagram audits.
- `POST /api/instagram/investigate`: Seamlessly escalate an Instagram threat into a formal BrandShield AI Investigation case file.

---

## ⚖️ License
Built for the **Kampus.VC / ByteXL Hackathon**. All rights reserved.
#   b y t e x l  
 