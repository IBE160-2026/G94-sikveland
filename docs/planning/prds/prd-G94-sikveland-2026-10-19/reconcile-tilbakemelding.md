# Reconcile: tilbakemelding-product-brief.md vs PRD

- **Input:** `docs/planning/tilbakemelding-product-brief.md`. Course teacher feedback on the product brief, 2026-10-06, with IBE160 Del 1 grading criteria.
- **Checked against:** `prd.md` (updated 2026-11-02), `addendum.md`, `.memlog.md`. `epics-and-stories.md` was also checked for traceability drift.
- **Date:** 2026-11-02
- **Status key:** addressed / partial / missing. "Deliberate" means `.memlog.md` records a user decision that covers the item.

## Summary of gaps (by severity)

| # | Gap | Severity |
|---|---|---|
| G1 | §6 Success Metrics still relies only on real-user metrics (SM-1 "Yes" share, SM-C1 email count). The feedback says these cannot be measured during the course. The testable criteria are in NFR4, but §6 does not mention them. | High |
| G2 | There is no evaluation procedure for NFR4. NFR3 says tests never call the real API, so it is unclear how answer quality on the test set is measured: which run, when, and how often after prompt or source changes. The test-set size (20–30) is not set, and refer-onward and no-answer questions (FR4, FR13) are not in its coverage list. | High |
| G3 | Examiner runnability is only partly covered. Demo-mode behaviour for unprepared questions is open (§9 Q2). There are no example questions with Norwegian or English translation for an examiner who does not read Thai. `.env.example` is not mentioned. | High |
| G4 | No language model is chosen and there is no cost plan. NFR6 only says "measured and reported", with no budget or estimate and no requirement that the model handles Thai well. | Medium |
| G5 | Traceability drift. FR3 and FR5 changed meaning, but they keep the IDs used in `epics-and-stories.md`, and the stories still describe the old behaviour (referral, and asking after every answer). FR12 and FR13 have no stories. Several FRs have no "Realizes" link and no brief or feedback source. | Medium |
| G6 | §2 Target User has only §2.3. There is no user profile (2.1/2.2), and "limited digital skills" from the brief is not stated as a design driver. | Medium |
| G7 | The MVP has no core-flow priority. The feedback asks to make ask → answer with source / referral stable first. §8.1 lists everything flat. | Medium |

## Item-by-item

### Samlet vurdering — what is good

| # | Quote (gloss) | Status | Where in PRD | Severity | Suggested fix |
|---|---|---|---|---|---|
| 1 | "Dere kjenner domenet fra eget arbeid, og det gjør det mulig å kontrollere om chatboten svarer riktig." (Your domain knowledge lets you check whether the chatbot answers correctly.) | partial | Implicit. UJ-1/UJ-2 come from the user's own experience. | Low | Say in NFR4 who writes and approves the expected answers in the test set: the group, using their domain knowledge. |
| 2 | "bare generell informasjon … svar med kildehenvisning, og ingen vurdering av individuelle saker. Spørsmål som krever skjønn, skal sendes videre til rådgiver eller myndighet." (General information only, answers with sources, no individual assessment; judgement questions referred to adviser or authority.) | addressed (deliberate change) | FR2, FR3, FR4, FR13, §7 Non-Goals | Low | The memlog records a deliberate decision: individual-assessment questions get "the embassy decides" rather than a referral. Consider adding a link to the embassy or UDI in the FR3 answer, so it still "refers onward" as the feedback praised. |

### Samlet vurdering — main changes

| # | Quote (gloss) | Status | Where in PRD | Severity | Suggested fix |
|---|---|---|---|---|---|
| 3 | "Suksesskriteriene (andel «Ja» … og redusert manuell arbeidsmengde) kan ikke måles i løpet av emnet. Legg til funksjonelle kriterier som kan bli testtilfeller" (Success criteria cannot be measured within the course; add functional criteria that can become test cases.) | partial | NFR4 has the functional criteria. §6 keeps SM-1 ("Yes" share) and SM-C1 (manual email count), and both need real users over time. The memlog records a deliberate decision: "share of Yes … is enough (user)". | High | In §6, add a primary metric for the course period, e.g. SM-0 "Test-set pass rate per NFR4", or cross-reference NFR4. Label SM-1 and SM-C1 as post-launch metrics that cannot be measured during the course. |
| 4 | "Briefen sier ikke hva chatboten skal bygge svarene på: hvilke offisielle kilder … hvor mange dokumenter, og hvordan de holdes oppdatert." (Describe the knowledge base: which sources, how many, how updated.) | addressed | FR11 (10–20 sources, URL/publisher/date, script update, topic coverage). §3 Glossary "Source" names UDI, VFS Global and the embassy. | Low | Optional: say the sources are stored in the repo with their retrieval date, so each answer can be traced to a source version (see #24). |
| 5 | "Det står ikke hvilken språkmodell som skal brukes, hva den koster, eller hvordan sensor kan kjøre appen uten deres nøkkel. Sensor leser trolig ikke thai" (No LLM chosen, no cost, no plan for the examiner to run without your key; examiner likely doesn't read Thai.) | partial | FR10 demo mode, NFR2 own key, NFR6 cost measured, FR7 English translation. No model, no budget. Demo mode for unprepared questions is open in §9 Q2. | High | Add an addendum "For architecture" note with the model choice criteria (good Thai, cheap) and an expected cost per question and for the semester. Resolve §9 Q2. Add a requirement for translated example questions (see #19). |

### Vanskelighetsgrad (difficulty factors)

| # | Quote (gloss) | Status | Where in PRD | Severity | Suggested fix |
|---|---|---|---|---|---|
| 6 | "Chatboten må kjenne grensen for hva den kan svare på." (The chatbot must know the limits of what it can answer.) | addressed | §4.2 FR3, FR4, FR13 | — | — |
| 7 | "Kildedokumenter, tekstbiter for søk, samtaler og tilbakemeldinger." (Data model: sources, chunks, conversations, feedback.) | addressed (deliberate) | NFR5: conversations are not stored, only Yes/No plus time. | Low | — |
| 8 | "Ingen innlogging i v1. En enkel administratorside … kan vurderes." (No login; an admin page could be considered.) | addressed (deliberate) | §8.2: the admin page is out of scope and sources are updated by script. | — | — |
| 9 | "Gjenfinning (retrieval) i kildene, svar på thai med kildehenvisning, og pålitelig avvisning og henvisning når informasjonen mangler." (Retrieval, Thai answers with sources, reliable refusal/referral when info is missing.) | addressed | FR1, FR2, FR4 | Low | The retrieval approach belongs in architecture; see #23. |
| 10 | "Språkmodell-API (og eventuelt embeddings)." (LLM API and possibly embeddings.) | missing | — | Low | Add an addendum note naming the external dependencies (LLM API, embeddings) for the architecture step. |
| 11 | "Gjør dette som et fast forarbeid i stedet for en funksjon i appen." (Fetch and split sources as an offline preprocessing step, not an in-app feature.) | addressed | FR11 ("updated by a script"), §8.2 (no admin page) | — | — |
| 12 | "Brukere kan skrive inn personlige opplysninger (pass, familie, økonomi) … Beskriv hva som lagres, og be brukerne la være å oppgi slike opplysninger." (Users may type personal data such as passport, family or finances; describe what's stored and ask them not to.) | partial | FR9 (warning, defined list), NFR5 (what is stored) | Medium | FR9 lists only passport number, ID number, phone number and full address. The memlog shows the user confirmed this list, but family and financial details from the feedback are left out. The PRD also does not say that the conversation text is sent to a third-party LLM API. State this in NFR5 or in the FR9 notice. |
| 13 | "Pass på at kjerneflyten blir ferdig og stabil før dere legger til mer … still et spørsmål på thai → få et riktig svar med kilde, eller en tydelig henvisning videre." (Finish the core flow first: Thai question → correct sourced answer or clear referral.) | partial | §8.1 lists all features with no priority. §9 Q1 (deadline) is open. | Medium | Split §8.1 into "Core flow (must be stable first)": FR1, FR2, FR3, FR4, FR13 and NFR4. Put "Then" items after it: FR6, FR5, FR7, FR8, FR9. |

### Gjennomførbarhet (feasibility)

| # | Quote (gloss) | Status | Where in PRD | Severity | Suggested fix |
|---|---|---|---|---|---|
| 14 | "Tid og omfang – OK … Pass på at det blir nok å vise" (Scope OK; make sure there is enough to show.) | addressed | FR6 checklist, FR12 steps, FR5 feedback loop | — | — |
| 15 | "Kunnskapsbase, henvisning til rådgiver og brukergrensesnitt må konkretiseres før PRD." (KB, adviser referral and UI must be concrete before the PRD.) | partial | KB in FR11, referral in FR4 and FR13, UI only through the UJs and NFR1 | Low | The UI detail will come from the bmad-ux step. Note this hand-off in §0 or the addendum. |
| 16 | "Kontroll på KI-ens arbeid – OK" (You can verify the AI's work.) | addressed | — | — | See #1. |
| 17 | "Lag et testsett med 20–30 spørsmål med forventet svar og kilde, pluss spørsmål som chatboten skal avvise eller henvise videre." (Make a 20–30 question test set with expected answer and source, plus questions to refuse or refer.) | partial | NFR4 defines targets and topic coverage. | High | Set the test-set size to 20–30. Add FR4 no-answer and FR13 "reach a person" cases to its coverage with a target (e.g. 100% give the adviser contact). State where the test set is stored. |
| 18 | "Planlegg oppskrift for egen nøkkel i README eller en demomodus, og eksempelspørsmål med norsk/engelsk oversettelse så sensor kan følge med." (README recipe for own key or a demo mode, plus example questions with Norwegian/English translation.) | partial | NFR2, FR10 | High | Extend FR10 or NFR2 so the README lists the example questions with English or Norwegian translation and the expected demo answers. Decide §9 Q2, e.g. demo mode answers unprepared questions with the FR4 no-answer response. |
| 19 | "Ingen plan for modell eller kostnad. Velg en modell som håndterer thai godt, og bruk mock-svar i automatiske tester." (No model/cost plan; choose a Thai-capable model; mock answers in automated tests.) | partial | NFR3 (tests never call the real API, which implies mocks), NFR6 (cost measured) | Medium | Add the model criteria and a cost estimate to the addendum. Optionally add a cost ceiling to NFR6, e.g. "total semester spend below X". |

### Forslag til justering (suggested adjustments)

| # | Quote (gloss) | Status | Where in PRD | Severity | Suggested fix |
|---|---|---|---|---|---|
| 20 | "10–20 utvalgte sider og dokumenter … lagret i repoet med dato, slik at svarene kan spores til en bestemt kildeversjon." (10–20 sources stored in the repo with date, so answers trace to a source version.) | partial | FR11 has the count and date. Storage in the repo and tracing answers to a version are not stated. | Low | Add to FR11: "stored in the repository; each answer's source link identifies the stored version." |
| 21 | "Vurder én eller to utvidelser … administratorside … eller en sjekkliste over dokumenter" (Consider one or two extensions: admin page or document checklist.) | addressed (deliberate) | FR6 is the chosen extension. The admin page is out of scope (§8.2). | — | — |

### Hvorfor product brief er viktig (traceability)

| # | Quote (gloss) | Status | Where in PRD | Severity | Suggested fix |
|---|---|---|---|---|---|
| 22 | "om sensor kan følge en sporbar vei fra plan til ferdig app" (Can the examiner follow a traceable path from plan to app?) | partial | §0 and the §4 note keep the FR IDs. Some FRs say "Realizes UJ-x". SM-1 says "Validates FR…". The memlog says IDs were kept for criterion 1. | Medium | FR3 changed from "referred to adviser/authority" to "embassy decides". FR5 changed from "after an answer" to "on done signal". Both keep their old IDs, so `epics-and-stories.md` (stories 4.1/4.2, 5.1/5.2) now describes different behaviour. FR12 and FR13 have no stories. Fix: add a short change note per changed FR in the PRD and flag that the stories need updating. Add "Realizes" or source links for FR3, FR4, FR7, FR9, FR10 and FR11, e.g. "From brief §Scope / feedback #17". |

### Gjennomgang av briefens deler (brief sections)

| # | Quote (gloss) | Status | Where in PRD | Severity | Suggested fix |
|---|---|---|---|---|---|
| 23 | "Legg til et eksempel på en samtale (spørsmål, svar med kilde, og en henvisning videre), og beskriv hvor brukeren møter chatboten." (Add a sample conversation with a sourced answer and a referral; say where users meet the chatbot.) | addressed (with caveat) | UJ-2 plus the addendum dialogue; the Facebook entry is in §1 and UJ-1 | Low | In the addendum dialogue, the answers about relationship proof and the €90 fee have no source links, which conflicts with FR2. Add a note that the real answers will show sources. Also, the dialogue's "house registration document" is less complete than the PRD's (own plus parent's). |
| 24 | "Nevn også alternativene søkerne har i dag, som UDIs og VFS Globals egne sider og generelle KI-chatboter, og hvorfor … bedre." (Name current alternatives such as UDI/VFS sites and general AI chatbots, and why this is better.) | missing | Only touched on: §7 says it does not replace the official sites, and UJ-1 mentions Google Translate or AI for UDI pages. | Low | Add a short "Alternatives today" paragraph to §1 or §2: official sites (mostly not in Thai), general AI chatbots (no curated sources, may hallucinate), and the adviser by email (slow). |
| 25 | "Tydelig primærbruker … inkludert begrensede digitale ferdigheter – viktig for designet." (Clear primary user, including limited digital skills, which matters for design.) | partial | §2 has only §2.3. NFR1 has large touch targets and simple language. | Medium | Add §2.1 Primary user (Thai, often reads only Thai, limited digital skills, phone via Facebook) and §2.2 Secondary user (the adviser). Reference them from NFR1. |
| 26 | "«chatboten svarer riktig med kilde på minst 90 % av testspørsmålene», «spørsmål om individuell vurdering blir alltid henvist videre», «svaret kommer på thai også når spørsmålet har skrivefeil»" (Example testable criteria.) | addressed | NFR4 has all three. The second was deliberately reworded to "embassy decides". | Low | The typo/mixed-language criterion has no numeric target. Add one, e.g. "100% of typo/mixed cases answered in Thai". |
| 27 | "Legg til hva v1 konkret består av (chatside, kunnskapsbase, tilbakemeldingsknapp, henvisning) og hva som er utenfor (kontoer, betaling, andre visumtyper)." (State what v1 contains and what is out.) | addressed | §8.1 and §8.2 | — | — |
| 28 | Vision — "Henger sammen med v1" (Vision is consistent.) | addressed | §1 | — | — |

### Del 1 grading criteria

| # | Quote (gloss) | Status | Where in PRD | Severity | Suggested fix |
|---|---|---|---|---|---|
| 29 | **1. Prosess og KI-styring (30 %)**: "krav kan spores fra brief til kode … Lagre gjerne promptene som styrer chatbotens svar" (Requirements traceable brief→code; save the prompts.) | partial | NFR7 versioned prompts; FR/NFR IDs kept | Medium | See #22 for traceability drift. |
| 30 | **2. Funksjonalitet og omfang (20 %)**: "Vurder én utvidelse" (Consider one extension.) | addressed | FR6 checklist | — | — |
| 31 | **3. Kvalitetssikring og testing (15 %)**: "Lag et testsett … og bruk det systematisk når dere endrer prompts eller kilder." (Use the test set systematically whenever prompts or sources change.) | partial | NFR4 (targets), NFR3 (mocked CI tests) | High | Add an NFR, e.g. NFR8 "Evaluation run": the NFR4 test set is run against the real model whenever a prompt version (NFR7) or the knowledge base (FR11) changes. The results, with prompt version and cost (NFR6), are saved in the repo. This resolves the conflict with NFR3, and `epics-and-stories.md` stories 8.x already assume it. |
| 32 | **4. Design og brukeropplevelse (10 %)**: "store knapper og tydelige kilder. Skisser chatskjermen og henvisningen til rådgiver." (Big buttons, clear sources; sketch the chat screen and adviser referral.) | partial | NFR1; the addendum "For UX" has only the dialogue | Low | Sketches belong to the bmad-ux step. Add an addendum "For UX" note: chat screen, source-link display, adviser-contact screen and checklist screen to be sketched. |
| 33 | **5. Kodekvalitet og arkitektur (10 %)**: "Velg en enkel løsning for retrieval (f.eks. en lokal vektorindeks)" (Choose simple retrieval, e.g. a local vector index.) | missing | — | Low | Add an addendum "For architecture" note: prefer a local vector index or simple file-based retrieval, with no external database. |
| 34 | **6. README og kjørbarhet (10 %)**: "Planlegg `.env.example`, oppskrift for egen API-nøkkel, demomodus og eksempelspørsmål med oversettelse." (Plan `.env.example`, own-key recipe, demo mode, translated example questions.) | partial | NFR2, FR10 | Medium | See #18. Also mention `.env.example` in NFR2. |
| 35 | **7. Ryddighet i repoet (5 %)**: "API-nøkkel i `.env`, kildedokumenter og testspørsmål i egne mapper, og ingen ekte søkerhenvendelser i repoet. Briefen … kan flyttes" (Key in .env, sources and test questions in their own folders, no real enquiries; move the brief.) | partial | NFR5 (no secrets or real enquiries in the repo). The brief has already moved to `docs/planning/` (commit 631e723). | Low | Add a folder layout note to the addendum for architecture: `.env`, sources and test-set folders. |

### Neste steg (next steps)

| # | Quote (gloss) | Status | Where in PRD | Severity | Suggested fix |
|---|---|---|---|---|---|
| 36 | "Beskriv kunnskapsbasen" (Describe the KB.) | addressed | FR11 | — | — |
| 37 | "Skriv funksjonelle suksesskriterier og lag et første testsett … inkludert spørsmål som skal henvises videre." (Write functional success criteria and a first test set, including refer-onward questions.) | partial | NFR4. There is no test set yet, and refer-onward questions are not in its coverage. | High | See #3 and #17. |
| 38 | "Velg språkmodell, og beskriv kostnad, demomodus og hvordan sensor kan kjøre og forstå appen." (Choose the LLM; describe cost, demo mode, and how the examiner runs and understands the app.) | partial | FR10, NFR2, NFR6, FR7 | High | See #5, #18 and #19. |
| 39 | "Gå videre til PRD med en konkret beskrivelse av kjerneflyten og eventuelle utvidelser." (Proceed to the PRD with a concrete core flow and extensions.) | addressed | §4, §8 | Low | See #13 for core-flow priority. |
| 40 | "Oppdater product brief i repoet … slik at historikken viser hvordan planen utviklet seg." (Update the brief in the repo so history shows how the plan evolved.) | addressed (outside PRD) | Commit 7e84deb "Revider product brief etter tilbakemelding" | — | — |
