# Tilbakemelding på PRD

| | |
|---|---|
| **Gruppe** | G94 – G94-sikveland |
| **PRD vurdert** | `docs/planning/prds/prd-G94-sikveland-2026-10-19/prd.md` (status `final`, sist endret 2026-11-02, commit 5e750ff) |
| **Dato** | 2026-11-12 |
| **Type** | Formativ tilbakemelding, ikke karakter |

## 1. Samlet inntrykk

Dette er en gjennomarbeidet PRD med egen tese: en thaispråklig chatbot som holder seg til offisielle kilder og er tydelig på hva den ikke kan svare på. PRD-en er ærlig om scope (hosting, Facebook-lenke og målinger med ekte brukere er skilt ut) og har et glossar som brukes konsekvent. Risikoen ligger i testbarheten: enkelte FR-er har ingen sjekkbare konsekvenser, og scopet er ikke prioritert selv om PRD-en står som `final`.

## 2. Dette fungerer godt

1. **Grensene er en del av produktet.** FR3, FR4, FR13 og FR14 gjør «vet når den ikke skal svare» til egne krav, og Non-Goals (§7) sier tydelig at «Only the embassy decides». Det er det som skiller dere fra en vanlig KI-chatbot (§2.2).
2. **Målbare kvalitetskrav og ærlig skille mellom nå og senere.** NFR4 definerer «correct», har mål (90 % og 100 %), krav til testsettet og to testlag (mock i CI, ekte modell separat). §6 deler suksessmålene i «During the course» og «After launch» og har en motmåling (SM-C1).
3. **Brukerreisene er konkrete og forankret i dialogen.** UJ-1 (Fah) har inngangstilstand, kantsak (sponsor-skjema) og «Today»-beskrivelsen. UJ-2 er knyttet til brukerens egen eksempeldialog i `addendum.md`. Teknologivalg ligger i addendumet, ikke i kravene.

## 3. Oversikt per dimensjon

| Dimensjon | Vurdering | Kort begrunnelse |
|---|---|---|
| Beslutningsklarhet | god | Valg som sjekkliste på telefonen, ingen konto, og script fremfor adminside er begrunnet. Åpne spørsmål 1–2 er fakta dere kan avklare selv. |
| Substans | sterk | Persona, NFR-er og avgrensninger er produktspesifikke. Ingen boilerplate. |
| Strategisk sammenheng | sterk | Tesen (pålitelige svar med kilde og ærlige grenser) går igjen i funksjoner, NFR4 og SM-2. |
| Testbarhet | god | Sterk for FR3, FR6, FR10 og NFR4, men FR4, FR7, FR8, FR13 og NFR1/NFR6 mangler sjekkbare konsekvenser. |
| Scope og avgrensning | god | Out of Scope er tydelig, men det mangler prioritering innenfor §8.1. |
| Brukbarhet for neste fase | god | Alle FR1–FR14 finnes, ID-ene er unike og krysshenvisningene stemmer. Noen FR-er (FR7, FR9–FR11) peker ikke til en UJ. |
| Formtilpasning | sterk | Forbrukerprodukt med UJ-er, KI-spesifikke krav og lett «enterprise»-pynt. Passer. |

## 4. Viktigste forbedringer

### 4.1 «Ikke i kunnskapsbasen» kan ikke testes slik FR4 er skrevet
- **Alvorlighet:** høy
- **Hvor:** §4.2 FR4: «When the knowledge base does not contain the answer, the chatbot says so and gives the adviser contact»; NFR4-listen over hva testsettet dekker.
- **Problem og hvorfor det betyr noe:** Det står ikke hva som regnes som «ikke i kunnskapsbasen», og NFR4 lister ikke spørsmål som skal gi no-answer. SM-2 sier at FR4 valideres, men ingen måling dekker det. Dette er den vanligste feilen i en kildebasert chatbot (den gjetter), og stories og tester kommer til å mangle et fasitsvar.
- **Forslag:** Legg til testbare konsekvenser, for eksempel: «Et spørsmål om en visumtype eller et land utenfor kunnskapsbasen gir no-answer-meldingen og adviser contact, uten påstander om krav.» Legg «spørsmål som ikke dekkes av kildene» (minst 3–4) og «spørsmål om å snakke med en person» (FR13) til listen over testsettets dekning i NFR4, med eget mål, f.eks. 100 % gir no-answer og ingen oppdiktede fakta.

### 4.2 Scopet er ikke prioritert, og avgjørende opplysninger er åpne
- **Alvorlighet:** høy
- **Hvor:** §9 punkt 1–2: «Project deadline and group size … affects how much of §8.1 fits»; §8.1.
- **Problem og hvorfor det betyr noe:** §8.1 har 14 FR-er, 8 NFR-er, kildeoppdatering med script og faglig gjennomgang av alle thaitekster (NFR8). Frist og gruppestørrelse er kjent for dere, så spørsmålene er ikke egentlig åpne. Uten rekkefølge vet ikke epics og stories hva som kuttes først når tiden blir knapp.
- **Forslag:** Svar på spørsmål 1 og skriv inn en kjerne og en «hvis tiden tillater»-liste, f.eks.: Kjerne = FR1, FR2, FR3, FR4, FR12, FR10, FR9. Deretter FR6, FR5, FR13, FR14. Til slutt FR7, FR8 og scriptet i FR11. Marker det i §8.1.

### 4.3 Flere krav har ingen sjekkbare konsekvenser
- **Alvorlighet:** medium
- **Hvor:** FR7 («can show an English translation»), FR8, FR13 («asks for help with the whole process»), NFR1 («works well … simple language»), NFR6 («measured and reported»).
- **Problem og hvorfor det betyr noe:** En story-forfatter kan ikke skrive akseptkriterier ut fra disse formuleringene. Åpent spørsmål 3 erkjenner NFR1, men løsningen står ikke i PRD-en.
- **Forslag:** For eksempel: «FR7: Hvert svar har en knapp som viser en engelsk oversettelse under svaret; oversettelsen har samme kildelenker.» «FR8: Siden viser 3–5 eksempelspørsmål; trykk sender spørsmålet uten å skrive.» «FR13: Meldinger som ber om en person eller om hjelp med hele søknaden (minst tre formuleringer i testsettet) gir adviser contact.» «NFR1: Fungerer fra 360 px bredde, knapper minst 44×44 px, testet i Facebooks nettleser.» «NFR6: Kostnad per spørsmål rapporteres i README, mål under X USD; si fra om dere overskrider det.»

### 4.4 Personvernet i FR9 mangler testbare grenser
- **Alvorlighet:** medium
- **Hvor:** FR9: «Personal information in a question is deleted before the question is sent to the AI service»; §3 «Personal information».
- **Problem og hvorfor det betyr noe:** Definisjonen dekker bare passnummer, ID-nummer og telefonnummer (addendumet sier mønsterfilter). Navn, adresser og fritekst som «min søster Anna bor på …» fanges ikke. Dette er grunnen til at filteret må testes, og at brukeren får vite hva det ikke dekker.
- **Forslag:** Legg til konsekvenser som: «Et 13-sifret thailandsk ID-nummer, et passnummer og et telefonnummer (08x-xxx-xxxx og +66) fjernes før kallet; testsettet har minst ett eksempel på hver. Gebyret (90 euro) og datoer fjernes ikke.» Skriv også i FR9 eller §7 at navn og adresser ikke oppdages automatisk, og at personvernmeldingen sier det.

### 4.5 Små presiseringer
- **Alvorlighet:** lav
- **Hvor:** FR7 / UJ-1; §3 «Adviser contact»; §3 «Conversation».
- **Problem og hvorfor det betyr noe:** (a) Fah leser ikke engelsk, så det er uklart hvem FR7 er til for (sensor? rådgiver?). (b) Glossaret har en konkret e-postadresse, mens addendumet sier at kontakten leses fra konfigurasjon. (c) Samtalen «lagres ikke», men oppfølgingsspørsmål (FR1) bruker tidligere spørsmål; det står ikke hvor konteksten holdes.
- **Forslag:** (a) Si hvem FR7 er til for, eller knytt den til en UJ. (b) Skriv «verdien i `ADVISER_CONTACT`» i glossaret. (c) Legg til en setning: «Konteksten holdes bare mens siden er åpen og lagres ikke.»

## 5. Mekaniske funn

- FR1–FR14 og NFR1–NFR8 finnes, uten duplikater; SM-1, SM-2 og SM-C1 refererer til eksisterende FR-er. FR-ene står ikke i tallrekkefølge i §4 (f.eks. FR12 før FR7), noe som er greit så lenge dere beholder ID-ene.
- To `[ASSUMPTION]` i teksten, begge i indeksen (§10). Roundtrip stemmer.
- FR7, FR9, FR10 og FR11 har ikke «Realizes UJ-x». Glossaret brukes ellers konsekvent («Applicant», «Adviser contact», «Checklist»).
- En e-postadresse står i klartekst i glossaret og addendumet (§3, «Sample dialogue»). Vurder om den skal stå i et offentlig repo.

## 6. Før dere går videre

**Må avklares før UX, arkitektur og epics:**
- Frist og gruppestørrelse, og en prioritert kjerne (4.2).
- Hva som utløser no-answer (4.1), og hvordan FR4 og FR13 testes.
- Hvem FR7 er til for (4.5a), fordi det påvirker UX.

**Kan vente:**
- Konkrete tall for NFR1 og NFR6 (4.3), så lenge de er på plass før teststrategien.
- SM-1-målet på 80 % og SM-C1 (krever ekte brukere etter hosting).
- Tilleggsmåling for om sjekklisten erstatter rådgiverens dokumentkontroll (åpent spørsmål 4).

**Oppfølging av tilbakemeldingen på product brief:** ja. Kunnskapsbase (FR11, 10–20 kilder med dato), testsett og funksjonelle suksesskriterier (NFR4, SM-2), modell/kostnad/demomodus (addendum, NFR6, FR10), sjekkliste som utvidelse (FR6) og alternativene søkeren har i dag (§2.2) er tatt inn. Adminside ble byttet mot script (§8.2), som er et ryddig valg.

## 7. Refleksjonsspørsmål

1. Klassifisereren (`individual_assessment` / `out_of_scope` / `general`) skal gjøre FR3 og FR14 pålitelige. Hvordan vil dere finne ut om den tar feil, og hva skal skje når den er usikker: svare, avvise eller sende videre til rådgiver?
2. Hvilke deler av PRD-en ble foreslått av KI, og hvilke valg tok dere selv, for eksempel kravene til sjekkliste på telefonen og feedback-spørsmålet fra eksempeldialogen? Hvordan sjekket dere at kravene stemmer med det rådgiveren faktisk møter i hverdagen?

_Vurdert mot kvalitetsrubrikken i bmad-prd. Dette er veiledning, ikke sensur._
