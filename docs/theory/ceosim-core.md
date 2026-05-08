# CEOSim Theory v1.0 - "Business-in-a-Box" Core Design Document
# Repository: /docs/theory/ceosim-core.md
# License: CC-BY-SA 4.0 | Status: DRAFT
# Maintainer: Jonathan Davis | Last Updated: 2026-05-08

## 1. Core Thesis
CEOSim is a business simulation game where virtual decisions can graduate into real-world UK legal entities. The player begins as a fictional CEO managing simulated operations. Upon meeting in-game milestones, the "Promote" system enables filing of a real Companies House incorporation via API bridge. This unites gameplay, education, and genuine entrepreneurship.

The novelty claim: No existing title connects gameplay loops directly to UK company formation. Adjacent products exist for formation agents, but none are game-native.【3175665064420639992†L90-L92】

## 2. Technical Architecture Philosophy
### 2.1 Backend: FOSS Business-in-a-Box
All simulated business functions map 1:1 to real FOSS services running in Docker. This ensures parity between game state and real ops.

| Game Function | FOSS Container | Real-World Parallel |
| --- | --- | --- |
| Email Server | Mailu / Postal | Company email domain |
| Identity / SSO | Keycloak / Authentik | Director/staff login |
| Document/Printing | Paperless-ngx / CUPS | Contracts, invoices |
| Accounting | Akaunting / InvoiceNinja | Ledgers, tax records |
| CRM | SuiteCRM / EspoCRM | Customer database |
| HR | OrangeHRM | Staff, PAYE basics |
| File Storage | Nextcloud | Company documents |

Gameplay = container orchestration. "Hire staff" spins up Keycloak user. "Send invoice" creates InvoiceNinja record.

### 2.2 The Promote Mechanism
"Promote" is the legal bridge. Trigger conditions:
1. In-game company reaches £1 virtual revenue, has SIC code, registered office, director
2. Player completes KYC tutorial and accepts legal disclaimers
3. Player is 16+ and provides real identity data

On trigger, game pauses. Backend calls incorporation API. Success returns real CRN and certificate.

## 3. UK Legal API Stack
### 3.1 Primary: Companies House API
Companies House is the UK executive agency for incorporating all forms of companies.【3175665064420639992†L7-L8】 It provides a public API for search and software filing.

Key endpoints for CEOSim:
1. GET /search/companies - Validate name availability
2. POST /transactions - Open incorporation filing session
3. POST /incorporation - Submit XML filing package
4. GET /company/{number} - Post-creation sync to game state

Requirements to file directly:
- Presenter account with Companies House
- Software filing credentials
- XML gateway compliance
- Director ID verification under ECCTA 2023

Alternative: Use formation agent API. Providers like Tide, 1st Formations, Kuberno handle KYC, registered address, HMRC reg. Creator Mia McGrath documented Tide incorporation at £14.99 vs £50 direct.【post-184320898886748045035】

### 3.2 Secondary: HMRC APIs
Post-incorporation requirements:
1. Corporation Tax registration - HMRC API
2. VAT registration if threshold met - HMRC MTD API
3. PAYE if staff hired - HMRC RTI API

Note: HMRC APIs require separate application and are stricter than Companies House.

### 3.3 Supporting Services
1. Registered Office: Required by law. Use partner API for virtual address
2. Banking: Tide/Wise/Monzo Business APIs for company account
3. Accounting: Sync game ledger to FreeAgent/Xero via API post-incorporation

## 4. Data Model: Game to Real Mapping
### 4.1 Minimum Viable Company Object
Escaped JSON example for reference only:
{\"company_name\": \"string, must pass Companies House checks\", \"registered_office\": \"UK_address_object\", \"sic_codes\": [\"array_of_strings\"], \"directors\": [{\"title\": \"MR\", \"forename\": \"string\", \"surname\": \"string\", \"dob\": \"YYYY-MM-DD\", \"nationality\": \"string\", \"occupation\": \"string\", \"address\": \"service_address_object\"}], \"share_capital\": {\"currency\": \"GBP\", \"total_shares\": \"int\", \"shareholders\": [{\"name\": \"string\", \"shares\": \"int\"}]}, \"articles\": \"model_articles|bespoke\", \"psc_register\": [\"person_with_significant_control_objects\"]}

Game stores this as entity state. On "Promote", serialize to Companies House XML schema 1.0.

### 4.2 Compliance Gates
CEOSim must not file without:
1. Player explicit consent checkbox: "I understand I am forming a real legal entity"
2. Age check: DOB confirms 16+
3. ID verification: Passport/driving licence via third-party KYC
4. Address verification: Proof of service address
5. Name screening: Reject sensitive words, existing trademarks

## 5. Liability and Disclaimers
CEOSim is entertainment with an optional legal utility. It is not legal, financial, or tax advice.
1. Forming a company creates real director duties under Companies Act 2006【3175665064420639992†L19-L20】
2. Directors are liable for filings, records, and taxes
3. CEOSim Ltd is not a formation agent unless registered. Using partner APIs places compliance on partner
4. Player pays Companies House £50 fee or partner fee. CEOSim takes no custody of funds

All "Promote" screens require disclaimer ack before API call.

## 6. Kickstarter Positioning
### 6.1 Unique Selling Proposition
"The only game where you can quit your job and become a real CEO. Start in simulation, end with Companies House certificate."

### 6.2 Funding Use
1. Legal: Presenter account, solicitor review, AML compliance
2. API: Formation agent partnership or XML gateway build
3. FOSS Integration: Container orchestration, game-to-API middleware
4. Art/Music: Already onboarded
5. Testing: Closed beta with accountants

### 6.3 Risks to Disclose
1. Regulatory: May require FCA review if handling payments
2. Liability: Directors sue if game UX causes filing error
3. Dependency: Companies House API downtime blocks feature
4. Abuse: Users incorporating joke companies, fraud

## 7. Development Roadmap
### Phase 1: Simulation Only
Full game with fake Companies House. All FOSS containers working. No real API.

### Phase 2: Sandbox Filing
Connect to Companies House test environment. File test companies. No legal effect.

### Phase 3: Partner Integration
Use formation agent API for production. They handle KYC. CEOSim passes data only.

### Phase 4: Direct Filing
Apply for presenter account. Build XML gateway. Full compliance stack.

## 8. Escaped Code Notes
Any code in repo must be escaped in docs. Example Dockerfile snippet:
# FROM mailu/admin:latest
# ENV DOMAIN=ceosim.local
# RUN echo "Mail server for game email sim" > /notice.txt

Never commit live API keys. Use.env.example:
# COMPANIES_HOUSE_API_KEY=your_key_here
# PRESENTER_ID=
# PRESENTER_AUTH_CODE=

## 9. Next Actions for Repo
1. Create /docs/theory/ceosim-core.md and paste this block
2. Create /docs/legal/disclaimers.md from section 5
3. Create /backend/api/companies_house/ with stub client
4. Open GitHub issue: "Investigate formation agent APIs vs direct XML"
5. Add artist/musician credits to /CREDITS.md

End of CEOSim Theory v1.0