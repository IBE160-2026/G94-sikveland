# Tilbakemelding på product brief

| | |
|---|---|
| **Gruppe** | G94 – G94-sikveland |
| **Product brief** | `product-brief.md` (commit 0d1eb2e) |
| **Tilbakemelding fra** | Faglærer i IBE160 (utarbeidet med KI-støtte) |
| **Dato** | 2026-10-06 |

## Samlet vurdering

- **Godt utgangspunkt med justeringer.** Gruppen kan gå videre og innarbeide punktene under.

**Det som er bra:**

1. Problemet er ekte og konkret: thailandske søkere til korttidsvisum for Norge har begrenset kjennskap til prosessen og stiller de samme spørsmålene til én rådgiver døgnet rundt. Dere kjenner domenet fra eget arbeid, og det gjør det mulig å kontrollere om chatboten svarer riktig.
2. Avgrensningen er fornuftig og ansvarlig: bare generell informasjon om turist- og besøksvisum, svar med kildehenvisning, og ingen vurdering av individuelle saker. Spørsmål som krever skjønn, skal sendes videre til rådgiver eller myndighet.

**De viktigste endringene:**

1. Suksesskriteriene (andel «Ja» etter samtalen og redusert manuell arbeidsmengde) kan ikke måles i løpet av emnet. Legg til funksjonelle kriterier som kan bli testtilfeller, f.eks. at chatboten svarer riktig med kilde på et fast sett testspørsmål.
2. Briefen sier ikke hva chatboten skal bygge svarene på: hvilke offisielle kilder (UDI, VFS Global, ambassaden), hvor mange dokumenter, og hvordan de holdes oppdatert. Beskriv kunnskapsbasen.
3. Det står ikke hvilken språkmodell som skal brukes, hva den koster, eller hvordan sensor kan kjøre appen uten deres nøkkel. Sensor leser trolig ikke thai – planlegg derfor også hvordan sensor kan forstå og teste svarene.

## Vanskelighetsgrad og gjennomførbarhet

### Vurdert vanskelighetsgrad

- **Middels**

**Sammenlignbart med:** 7) Kurs-FAQ-chatbot (middels) – en chatbot som svarer på spørsmål ut fra en kunnskapsbase med kildehenvisning, og som må håndtere usikkerhet og henvise videre.

**Begrunnelse:**

| Faktor | Nivå (lav / middels / høy) | Kommentar |
|---|---|---|
| Domenelogikk – hvor mange og hvor kompliserte regler og beregninger må stemme? | Middels | Ingen beregninger, men visumregler er fagregler der feil svar kan få konsekvenser for søkeren. Chatboten må kjenne grensen for hva den kan svare på. |
| Datamodell – antall entiteter og relasjoner mellom dem | Lav | Kildedokumenter, tekstbiter for søk, samtaler og tilbakemeldinger. Enkel modell. |
| Brukere, roller og innlogging | Lav | Ingen innlogging i v1. En enkel administratorside for å oppdatere kilder kan vurderes. |
| KI-funksjonalitet i appen, f.eks. kall til språkmodell, prompts i koden og håndtering av usikre svar | Høy | Gjenfinning (retrieval) i kildene, svar på thai med kildehenvisning, og pålitelig avvisning og henvisning når informasjonen mangler. Dette er hele kjernen i appen. |
| Integrasjoner og eksterne tjenester, f.eks. API-er, betaling og e-post | Middels | Språkmodell-API (og eventuelt embeddings). Ingen betaling eller e-post i v1. |
| Sanntid, samtidighet eller flere brukere som påvirker hverandre | Lav | Hver samtale er uavhengig. |
| Filhåndtering, f.eks. opplasting, PDF-lesing og eksport | Middels | Kildene er trolig nettsider og PDF-er som må hentes og deles opp. Gjør dette som et fast forarbeid i stedet for en funksjon i appen. |
| Sikkerhet og personvern | Middels | Brukere kan skrive inn personlige opplysninger (pass, familie, økonomi) i chatten. Beskriv hva som lagres, og be brukerne la være å oppgi slike opplysninger. |

**Hva vanskelighetsgraden betyr for dere:**

- _Middels:_ Et godt balansert valg. Pass på at kjerneflyten blir ferdig og stabil før dere legger til mer. For dere betyr det: still et spørsmål på thai → få et riktig svar med kilde, eller en tydelig henvisning videre. Få dette til å virke godt på et fast sett spørsmål før dere legger til flere visumtyper eller funksjoner.

### Gjennomførbarhet med BMAD og Claude Code

Dere skal planlegge med BMAD (product brief → PRD → arkitektur → epics og stories) og implementere med Claude Code. Vurderingen under tar hensyn til at det må være tid til hele denne flyten, og til testing, retting og README til slutt.

| Spørsmål | Vurdering (OK / risiko / stor risiko) | Kommentar |
|---|---|---|
| **Tid og omfang** – kan v1 realistisk bli ferdig og stabil i løpet av semesteret, med tid til flere iterasjoner? | OK | Omfanget er avgrenset og realistisk for én person. Pass på at det blir nok å vise; se forslagene under. |
| **BMAD-flyten** – er briefen konkret nok til at PRD, arkitektur og stories kan lages uten store hull, og blir det overkommelig mange stories? | Risiko | Problem og brukere er tydelige, men løsningen beskrives bare overordnet. Kunnskapsbase, henvisning til rådgiver og brukergrensesnitt må konkretiseres før PRD. |
| **Egnet for Claude Code** – bruker løsningen en vanlig, godt dokumentert teknologistakk som Claude Code håndterer godt, eller krever den nisjeteknologi, spesialmaskinvare eller mye manuell konfigurasjon? | OK | En enkel webchat med retrieval mot en liten dokumentsamling er godt dokumentert og passer Claude Code. |
| **Kontroll på KI-ens arbeid** – kan gruppen selv avgjøre om koden gjør det riktige? Krever domenet kunnskap gruppen ikke har, f.eks. avanserte beregninger eller fagregler, så er det vanskelig å kvalitetssikre. | OK | Dere har domenekunnskapen og kan selv vurdere om svarene er riktige og godt formulert på thai. Det er en klar styrke. |
| **Testbarhet** – finnes det tydelige regler og forventede resultater som tester kan skrives mot? | Risiko | Ikke beskrevet ennå. Lag et testsett med 20–30 spørsmål med forventet svar og kilde, pluss spørsmål som chatboten skal avvise eller henvise videre. |
| **Kjørbar for sensor** – kan appen kjøres lokalt etter README, uten gruppens nøkler, betalte kontoer eller egen infrastruktur? | Risiko | Krever trolig en API-nøkkel. Planlegg oppskrift for egen nøkkel i README eller en demomodus, og eksempelspørsmål med norsk/engelsk oversettelse så sensor kan følge med. |
| **Avhengigheter og kostnader** – krever løsningen betalte API-er, f.eks. språkmodeller, og finnes det en plan for kostnad, testmodus eller mock-data? | Risiko | Ingen plan for modell eller kostnad. Velg en modell som håndterer thai godt, og bruk mock-svar i automatiske tester. |

**Konklusjon om gjennomførbarhet:**

- **Gjennomførbart som beskrevet.**

**Forslag til justering av omfang eller vanskelighetsgrad:**

1. Definer kunnskapsbasen konkret: f.eks. 10–20 utvalgte sider og dokumenter fra UDI, VFS Global og ambassaden, lagret i repoet med dato, slik at svarene kan spores til en bestemt kildeversjon.
2. Vurder én eller to utvidelser som gir mer å vise i funksjonalitet og testing, f.eks. en enkel administratorside der rådgiveren kan legge til eller oppdatere kilder, eller en sjekkliste over dokumenter som chatboten kan sette sammen ut fra besøkstype.

## Hvorfor product brief er viktig for mappen

Product brief er utgangspunktet for PRD, arkitektur, stories og til slutt koden. Del 1 av mappen vurderes blant annet på om sensor kan følge en sporbar vei fra plan til ferdig app. Den vurderes også på om appen gjør det dere har beskrevet, om den er testet, om den er godt designet, og om den kan kjøres etter README. Et uklart, for stort eller for lite brief gjør alt dette vanskeligere senere. Det er mye enklere å rette nå enn sent i semesteret.

## 1. Gjennomgang av briefens deler

| Del av brief | Status | Kommentar |
|---|---|---|
| Executive Summary – er det klart hva appen er, og hvilket problem den løser? | OK | Klart: en thaispråklig chatbot med generell informasjon om korttidsvisum til Norge, døgnet rundt. |
| The Problem – er problemet konkret, med reelle situasjoner og brukere? | OK | Konkret og basert på egen erfaring, med tydelige konsekvenser for både søkere og rådgiver. |
| The Solution – beskriver løsningen brukeropplevelsen, ikke bare teknologi? | Juster | Beskriver opplevelsen overordnet. Legg til et eksempel på en samtale (spørsmål, svar med kilde, og en henvisning videre), og beskriv hvor brukeren møter chatboten. |
| What Makes This Different – er vurderingen ærlig og realistisk? | Juster | Sammenligner bare med dagens manuelle svar. Nevn også alternativene søkerne har i dag, som UDIs og VFS Globals egne sider og generelle KI-chatboter, og hvorfor en thaispråklig chatbot med utvalgte kilder er bedre. |
| Who This Serves – er primærbrukerne tydelige, og vet vi hva de trenger? | OK | Tydelig primærbruker med konkrete behov, inkludert begrensede digitale ferdigheter – viktig for designet. |
| Success Criteria – kan kriteriene faktisk sjekkes eller testes? | Endre | Begge kriteriene krever ekte brukere over tid. Legg til f.eks. «chatboten svarer riktig med kilde på minst 90 % av testspørsmålene», «spørsmål om individuell vurdering blir alltid henvist videre», «svaret kommer på thai også når spørsmålet har skrivefeil». |
| Scope – er det klart hva som er med i første versjon, og hva som ikke er det? | Juster | Tydelig hva chatboten ikke skal gjøre. Legg til hva v1 konkret består av (chatside, kunnskapsbase, tilbakemeldingsknapp, henvisning) og hva som er utenfor (kontoer, betaling, andre visumtyper). |
| Vision – henger visjonen sammen med resten uten å blåse opp omfanget? | OK | Henger sammen med v1 og holder kontoer og betaling utenfor første versjon. |

## 2. Utgangspunkt for del 1 av mappen

Punktene følger kriteriene i sensorveiledningen for del 1. Vektene i parentes viser hvor mye hvert kriterium teller i del 1.

| Kriterium i del 1 | Hva briefen bør legge til rette for | Status | Kommentar |
|---|---|---|---|
| **1. Prosess og KI-styring** (30 %) | Brief som er presis nok til at PRD og stories kan bygges direkte på den, slik at krav kan spores fra brief til kode. | Juster | Briefen er god på problem og brukere, men løsningen må konkretiseres før PRD. Lagre gjerne promptene som styrer chatbotens svar, så sensor ser hvordan dere har justert dem. |
| **2. Funksjonalitet og omfang** (20 %) | Realistisk omfang for gruppen og semesteret: en tydelig kjerneflyt som kan bli ferdig og stabil, og nok innhold til å vise reell funksjonalitet. | Juster | Realistisk kjerneflyt. Vurder én utvidelse (administratorside eller dokumentsjekkliste) for å vise mer funksjonalitet. |
| **3. Kvalitetssikring og testing** (15 %) | Suksesskriterier og funksjoner som er konkrete nok til å bli testtilfeller. | Endre | Lag et testsett med spørsmål, forventede svar og kilder, og bruk det systematisk når dere endrer prompts eller kilder. |
| **4. Design og brukeropplevelse** (10 %) | Tydelige brukere og brukssituasjoner som designet kan bygges rundt, gjerne med de viktigste skjermbildene eller flytene skissert. | Juster | Brukere med begrensede digitale ferdigheter og trolig mobilbruk stiller krav til enkelhet, store knapper og tydelige kilder. Skisser chatskjermen og henvisningen til rådgiver. |
| **5. Kodekvalitet og arkitektur** (10 %) | Teknologivalg som er begrunnet og ikke mer komplekse enn appen trenger. | OK | Ingen teknologivalg ennå, og det er greit. Velg en enkel løsning for retrieval (f.eks. en lokal vektorindeks) i stedet for eksterne databaser. |
| **6. README og kjørbarhet** (10 %) | Løsning som andre kan kjøre lokalt uten betalte kontoer, og uten tilgang til gruppens egne tjenester og nøkler. | Juster | Planlegg `.env.example`, oppskrift for egen API-nøkkel, demomodus og eksempelspørsmål med oversettelse. |
| **7. Ryddighet i repoet** (5 %) | En plan for hvor hemmeligheter, testdata og dokumentasjon skal ligge. | Juster | API-nøkkel i `.env`, kildedokumenter og testspørsmål i egne mapper, og ingen ekte søkerhenvendelser i repoet. Briefen ligger i roten og kan flyttes til en mappe for planleggingsdokumenter. |

## 3. Neste steg for gruppen

1. Beskriv kunnskapsbasen: hvilke kilder, hvor mange dokumenter, og hvordan de lagres og oppdateres.
2. Skriv funksjonelle suksesskriterier og lag et første testsett med spørsmål og forventede svar, inkludert spørsmål som skal henvises videre.
3. Velg språkmodell, og beskriv kostnad, demomodus og hvordan sensor kan kjøre og forstå appen.
4. Gå videre til PRD med en konkret beskrivelse av kjerneflyten og eventuelle utvidelser.

Oppdater product brief i repoet når dere har gjort endringene, slik at historikken viser hvordan planen utviklet seg. Det er en del av prosessen sensor ser etter.
