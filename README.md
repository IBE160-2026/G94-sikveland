# G94 — Norway Visa Guide For Thai

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng).

**Norway Visa Guide For Thai** er en chatbot på thai for søkere av visum for kortvarig besøk i Norge (turist- og besøksvisum). Søkeren åpner en mobil nettside, stiller et spørsmål på thai og får et svar som strømmes inn bit for bit, med lenker til de offisielle kildene svaret bygger på (UDI, Norges ambassade i Bangkok, EU). Chatboten svarer bare ut fra en fast kunnskapsbase med disse kildene, og gir kontakten til rådgiveren når den ikke har svar.

Bakgrunnen er at én rådgiver i dag svarer på de samme spørsmålene fra mange søkere på e-post, ofte om kvelden og i helgene. Se [product brief](docs/planning/product-brief.md) og [PRD](docs/planning/prds/prd-G94-sikveland-2026-10-19/prd.md).

## Medlemmer

- Wannapa Sikveland

## Status (2026-11-16)

Alle stories i planen er laget. De har automatiske tester og venter på de manuelle testene i [testplanen](docs/implementation/manual-test-plan.md) (med ekte nøkkel og på mobil) før de regnes som helt ferdige.

Laget og testet automatisk:

- Chatside på thai, laget for mobil, med personvernmerknad og eksempelspørsmål man kan trykke på (Story 1.2)
- Kunnskapsbase med 15 offisielle kilder lagret som Markdown (Story 1.3)
- Filter som fjerner passnummer og thailandsk ID-nummer før spørsmålet sendes til KI-tjenesten (Story 1.4)
- Svar fra Claude, strømmet med kildelenker (Story 1.5, 1.6)
- Oppfølgingsspørsmål i samme samtale (Story 1.7)
- Tidligere samtaler lagres på søkerens egen enhet (de siste 20) og kan åpnes og fortsettes; knapp for ny samtale, og sletting av én eller alle
- Logg over kostnad, tokens og cache per spørsmål (Story 1.8)
- Spørsmål om søkerens egne sjanser («Får jeg visum?») får et fast svar om at bare ambassaden avgjør, uten at svarmodellen kalles (Story 2.1)
- Spørsmål om andre visumtyper eller andre temaer, og ønske om å snakke med et menneske, får faste svar med rådgiverens kontakt (Story 2.2)
- Når søkeren takker eller sier «ok», spør chatboten om søkeren har fått all informasjonen de trenger, med knappene Ja og Nei; svaret lagres som eneste data på serveren (Story 2.3)
- Dokumentsjekkliste per besøksformål (turisme, besøke familie, besøke venner) bak knappen «Sjekkliste» øverst. Søkeren krysser av dokumentene hen har, kan merke punkter som «gjelder ikke meg», og finner avkrysningene igjen senere på samme enhet; de sendes aldri til serveren (Story 3.1, 3.2). Under svar som viser til en kilde som en sjekkliste bygger på, kommer knappen «Åpne sjekkliste», også når samtalen åpnes igjen senere (Story 3.3)
- **Demomodus** som virker uten API-nøkkel (Story 4.2)
- Knappen «Show English» under hvert ferdig svar og i sjekklisten, så sensor som ikke leser thai, kan følge med (Story 4.1)
- Valgfritt: svar fra en lokal modell via [Ollama](https://ollama.com) i stedet for Claude, så appen ikke er avhengig av én bestemt KI-tjeneste ([spesifikasjon](docs/implementation/spec-ollama-provider.md))
- Denne README-en, slik at appen kan kjøres og følges uten hjelp fra gruppa (Story 4.3)
- Testsett med 29 oppdiktede thai spørsmål og forventede svar, godkjent som rådgivergjennomgang (Story 5.1, se [Testsett](#testsett))
- Evalueringsskript som kjører testsettet mot den ekte modellen og skriver en rapport rådgiveren vurderer (Story 5.2, se [Evaluering](#evaluering)); første kjøring med Ollama ligger i [`eval/reports/`](eval/reports/)
- Statistikk over andelen samtaler der det første svaret er «Ja» (Story 5.3, se [Tilbakemelding på slutten av samtalen](#tilbakemelding-på-slutten-av-samtalen))

Hele planen står i [epics.md](docs/planning/epics.md), og status per story står i [sprint-status.yaml](docs/implementation/sprint-status.yaml).

## Kom i gang

### Det du trenger

- [uv](https://docs.astral.sh/uv/getting-started/installation/), som installerer riktig Python (3.12) og alle pakker
- Git

### Installer

```sh
git clone https://github.com/IBE160-2026/G94-sikveland.git
cd G94-sikveland
uv sync
```

### Kjør i demomodus (uten API-nøkkel)

Demomodus bruker lagrede svar i stedet for Claude, så appen kan prøves uten nøkkel og uten kostnad.

PowerShell (Windows):

```powershell
$env:MOCK_LLM = "true"
uv run uvicorn app.main:app
```

Bash (macOS/Linux):

```sh
MOCK_LLM=true uv run uvicorn app.main:app
```

Åpne <http://127.0.0.1:8000>. Siden viser merket «โหมดสาธิต» (demomodus). Trykk på et av de fire eksempelspørsmålene:

| Eksempelspørsmål (thai) | In English | På norsk |
|---|---|---|
| ขอวีซ่าท่องเที่ยวนอร์เวย์ต้องใช้เอกสารอะไรบ้าง | What documents do I need for a Norway tourist visa? | Hvilke dokumenter trenger jeg til turistvisum til Norge? |
| ถ้าจะขอวีซ่าไปนอร์เวย์ ต้องเริ่มต้นอย่างไร | How do I start applying for a Norway visa? | Hvordan begynner jeg å søke visum til Norge? |
| ค่าธรรมเนียมวีซ่านอร์เวย์ราคาเท่าไร | How much is the Norway visa fee? | Hva koster visum til Norge? |
| การพิจารณาวีซ่าใช้เวลานานเท่าไร | How long does the visa processing take? | Hvor lang er behandlingstiden? |

Knappen «แปลเป็นภาษาอังกฤษ (English)» under hvert svar viser svaret på engelsk (se [Vis på engelsk](#vis-på-engelsk-show-english)).

Hvert av dem gir et lagret thai svar med kildelenker. Andre spørsmål gir en fast tekst om at demoen bare svarer på eksempelspørsmålene. Svarene står i [`content/demo-answers.yaml`](content/demo-answers.yaml), med engelsk oversettelse.

### Åpne siden fra en mobil på samme Wi-Fi

Appen er laget for mobil. For å prøve den på en telefon som er på samme Wi-Fi som maskinen:

1. Start appen slik at den tar imot forespørsler fra andre maskiner. I demomodus, PowerShell (etter `$env:MOCK_LLM = "true"` som over):

   ```powershell
   uv run uvicorn app.main:app --host 0.0.0.0
   ```

   I demomodus, Bash:

   ```sh
   MOCK_LLM=true uv run uvicorn app.main:app --host 0.0.0.0
   ```

   Med `.env` (Claude eller Ollama, se under) er kommandoen den samme som den første, i begge skall.

2. Finn maskinens IP-adresse på nettverket: i PowerShell `ipconfig` (linja «IPv4 Address» under Wi-Fi-kortet), på macOS `ipconfig getifaddr en0` (gir den ingenting, prøv `en1`), på Linux `hostname -I`. Velg adressen som begynner på `192.168.` eller `10.`, f.eks. `192.168.1.23`.
3. Åpne `http://<IP-adressen>:8000` i nettleseren på mobilen, f.eks. `http://192.168.1.23:8000`.

Spør Windows om Python får bruke nettverket, svar ja for private nettverk; macOS kan på samme måte spørre om innkommende tilkoblinger skal tillates. Laster ikke siden på mobilen, sjekk at begge er på samme Wi-Fi (ikke gjestenettet), at Wi-Fi-nettet er satt som privat nettverk i Windows, og at Python er tillatt i «Windows-sikkerhet → Brannmur og nettverksbeskyttelse → Tillat en app gjennom brannmuren» (Windows spør ikke på nytt hvis du har sagt nei før). Uten `--host 0.0.0.0` svarer appen bare på maskinen selv.

### Kjør med Claude (ekte svar)

1. Kopier [`.env.example`](.env.example) til `.env`: `Copy-Item .env.example .env` i PowerShell, `cp .env.example .env` i Bash. Har du satt `$env:MOCK_LLM` i samme PowerShell-vindu for demomodus, fjern den først med `Remove-Item Env:MOCK_LLM` (en miljøvariabel går foran `.env`).
2. Åpne `.env`, sett `ANTHROPIC_API_KEY` til nøkkelen din, og la `MOCK_LLM=false` stå.
3. Start med `uv run uvicorn app.main:app` og åpne <http://127.0.0.1:8000>. Merket «โหมดสาธิต» skal ikke vises.

Uten nøkkel starter appen likevel, men hvert spørsmål gir en fast feiltekst. `.env` er git-ignorert og skal aldri committes.

### Kjør med Ollama (lokal modell, uten nøkkel)

Svarene kan også komme fra en modell som kjører på din egen maskin. Det koster ingenting og trenger ingen nøkkel, men krever et grafikkort med nok minne (testet med `qwen3.5:9b` på et kort med 16 GB) og gir svakere svar enn Claude.

1. Installer [Ollama](https://ollama.com) og hent modellen: `ollama pull qwen3.5:9b`. Modellen må støtte tenking (thinking), for appen slår den alltid på.
2. Sett `LLM_PROVIDER=ollama` i `.env` (og la `MOCK_LLM=false` stå). `OLLAMA_BASE_URL`, `OLLAMA_MODEL` og `OLLAMA_NUM_CTX` har standardverdier som passer for en vanlig Ollama-installasjon.
3. Start Ollama, og så appen med `uv run uvicorn app.main:app`.

Appen sender med `num_ctx` (standard 32768 tokens) i hver forespørsel. Kunnskapsbasen er rundt 24 600 tokens, og Ollamas egen standard på 4096 ville kuttet den uten å si fra. Det første svaret etter at Ollama har startet tar ekstra tid, fordi modellen må lese hele kunnskapsbasen (rundt 7 sekunder på et grafikkort med 16 GB, mye lenger uten grafikkort); deretter gjenbruker Ollama den. Fordi modellen tenker før den svarer, tok et svar i testene fra 6 sekunder til over ett minutt.

Uten Claudes innebygde kildehenvisninger skriver modellen kildene som `[[kilde-id]]` i teksten. Appen gjør dem om til kildelenker og fjerner dem fra teksten, så søkeren ser det samme som med Claude. Staver modellen en kilde-ID nesten riktig (f.eks. `udi-sponsor-for-visators`), brukes den kjente kilden som ligner mest, når likheten (`difflib`-forholdet) er minst 0,85 etter at mellomrom i endene er fjernet og store bokstaver, mellomrom og understrek er rettet; ligner to kilder like mye, får ingen av dem lenken. En slik ID telles ikke lenger som ukjent i forespørselsloggen, men står som en linje i applikasjonsloggen. Andre ukjente ID-er får ingen lenke. Reglene for dette, og en regel om å bare skrive thai skrift, står i [`prompts/answer-citing-markers.md`](prompts/answer-citing-markers.md), som bare brukes med Ollama. En liten modell blander av og til inn ord eller tegn fra andre skriftsystemer, mest kinesisk. I en test med 36 svar før og 36 svar etter regelen gjaldt det 5 og 2 svar: færre, men ikke null, og for få svar til å bevise at regelen virker. Ollama-svar bør derfor leses av en som kan thai før de brukes overfor søkere.

Kjører ikke Ollama, eller er modellen ikke hentet, starter appen likevel, men hvert spørsmål gir den faste feilteksten. Demomodus (`MOCK_LLM=true`) går foran `LLM_PROVIDER`.

### Innstillinger

Alle innstillinger står med forklaring i [`.env.example`](.env.example). Et feilstavet navn i `.env` stopper oppstarten, slik at det ikke blir ignorert i det stille.

| Innstilling | Standard | Betydning |
|---|---|---|
| `ANTHROPIC_API_KEY` | tom | Nøkkel til Claude API; ikke nødvendig i demomodus |
| `MOCK_LLM` | `false` | `true` = demomodus med lagrede svar |
| `LLM_PROVIDER` | `anthropic` | Hvem som svarer utenom demomodus: `anthropic` (Claude) eller `ollama` (lokal modell) |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | `http://localhost:11434`, `qwen3.5:9b` | Ollama-serveren og modellen; brukes bare med `LLM_PROVIDER=ollama` |
| `OLLAMA_NUM_CTX` | `32768` | Kontekstvindu i tokens som sendes til Ollama; minst 32768 |
| `MODEL_ANSWER`, `EFFORT_ANSWER` | `claude-opus-5-5`, `medium` | Modellen som skriver svarene |
| `MODEL_SMALL`, `EFFORT_SMALL` | `claude-haiku-5-5`, `low` | Liten modell til enkle oppgaver: sortere spørsmålene og oversette svar til engelsk (se under) |
| `ADVISER_CONTACT` | rådgiverens e-post | Vises når chatboten ikke kan hjelpe |
| `REQUEST_LOG_PATH` | `data/requests.jsonl` | Forespørselsloggen (se under) |
| `DATABASE_PATH` | `data/feedback.sqlite3` | SQLite-fila med tilbakemeldingene (se under); en relativ sti regnes fra prosjektmappa |
| `PRICE_ANSWER_INPUT` | `4.00` | USD per million vanlige input-tokens til svarmodellen (`MODEL_ANSWER`) |
| `PRICE_ANSWER_OUTPUT` | `20.00` | USD per million output-tokens fra svarmodellen, tenking medregnet |
| `PRICE_ANSWER_CACHE_READ` | `0.20` | USD per million tokens svarmodellen leser fra prompt-cachen (kunnskapsbasen etter første spørsmål) |
| `PRICE_ANSWER_CACHE_WRITE` | `5.00` | USD per million tokens svarmodellen skriver til prompt-cachen (1,25 × input) |
| `PRICE_SMALL_INPUT` | `0.10` | USD per million input-tokens til den lille modellen (`MODEL_SMALL`: sortering og oversettelse) |
| `PRICE_SMALL_OUTPUT` | `0.50` | USD per million output-tokens fra den lille modellen |
| `PRICE_SMALL_CACHE_READ` | `0.01` | USD per million cache-leste tokens for den lille modellen (brukes ikke i dag) |
| `PRICE_SMALL_CACHE_WRITE` | `0.125` | USD per million cache-skrevne tokens for den lille modellen (brukes ikke i dag) |

Prisene brukes bare til kostnadsloggen og evalueringsrapporten; de endrer ikke hva appen gjør. Sjekk dem mot Anthropics prisside hvis den endres.

## Tester

```sh
uv run pytest
```

Testene bruker en falsk KI-klient og kaller aldri Claude API eller Ollama, så de trenger ingen nøkkel og koster ingenting.

Koden sjekkes med [ruff](https://docs.astral.sh/ruff/) (linter og formatterer, oppsett i `pyproject.toml`):

```sh
uv run ruff check           # feil og dårlig praksis
uv run ruff format --check  # formatering; uten --check rettes den
```

[GitHub Actions](.github/workflows/ci.yml) kjører ruff og testene ved hver push.

Det de automatiske testene ikke dekker (siden i en nettleser, ekte Claude-svar, ekte mobil og Facebooks innebygde nettleser), står i den [manuelle testplanen](docs/implementation/manual-test-plan.md) sammen med resultatene.

## Slik virker det

```text
Nettleser (app/static)  →  POST /api/chat  →  personvernfilter  →  sortering (liten modell)
                                                                     ├─ general  →  Claude med kunnskapsbasen i prompten
                                                                     ├─ individual_assessment  →  fast tekst «bare ambassaden avgjør»
                                                                     ├─ out_of_scope  →  fast tekst «bare kortvarige visum til Norge» + rådgiverens kontakt
                                                                     ├─ reach_person  →  fast tekst med rådgiverens kontakt
                                                                     └─ done  →  tilbakemeldingsspørsmålet, med Ja/Nei-knapper på siden
                        ←  strøm av JSON-linjer: tekstbiter, kilder, ferdig
```

- Hele kunnskapsbasen (`knowledge-base/*.md`) sendes med i systemprompten og caches hos Anthropic, så gjentatte spørsmål blir billigere. Appen henter ingenting fra nettet mens den kjører.
- Med `LLM_PROVIDER=ollama` går spørsmålet til en lokal Ollama-server i stedet for Claude (se over); resten av flyten er den samme.
- Svaret må oppgi hvilke kilder det bygger på. Kildelenkene hentes fra [`knowledge-base/sources.yaml`](knowledge-base/sources.yaml). Viser svaret til en kilde som ikke står der, får den kilden ingen lenke, resten av svaret vises, og antallet telles i forespørselsloggen. Viser svaret ikke til noen kjent kilde, får søkeren den faste «vi har ikke svar»-teksten. Det samme skjer når første linje i svaret er en setning om at informasjonen ikke finnes («ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ», «ไม่พบข้อมูล…», «ไม่พบคำตอบ…») uten at den går over til et svar med แต่ («men») eller อย่างไรก็ตาม («likevel»), selv om resten av svaret viser til kilder; appen venter da med å vise noe til første linje er ferdig, og et svar som allerede vises, byttes aldri ut.
- Serveren lagrer ingen samtaler, bare svaret på tilbakemeldingsspørsmålet (se under). Tidligere samtaler lagres bare i nettleseren på søkerens egen enhet (`localStorage`), og bare den åpne samtalens siste 10 utvekslinger sendes med et spørsmål. Personvernmerknaden sier at alle som bruker enheten, kan lese dem.
- Koden er delt i lag (porter og adaptere): `pipeline` kjenner ikke til FastAPI eller Anthropic, og `tests/test_layering.py` sjekker at det holder.

Mer i [arkitekturoversikten](docs/planning/architecture/architecture-overview.md), skrevet for sensor, og i de bindende reglene i [ARCHITECTURE-SPINE.md](docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md).

### Spørsmål om egne sjanser, andre temaer og ønske om et menneske

Før et spørsmål besvares, sorterer et eget, lite modellkall det rensede spørsmålet (sammen med de to siste spørsmålene og svarene i samtalen, der hvert svar kortes ned til de første 600 tegnene) som `general`, `individual_assessment`, `out_of_scope` eller `reach_person`. Prompten står i [`prompts/classifier-system.md`](prompts/classifier-system.md). Spørsmål som bare handler om søkerens egne sjanser («จะได้วีซ่าไหม», «Will I get the visa?») får den faste teksten `reply-embassy-decides` (bare ambassaden avgjør), uten kildelenker, og svarmodellen kalles ikke. Et spørsmål som også spør om noe kildene svarer på, f.eks. «จะได้วีซ่าไหม แล้วต้องใช้เอกสารอะไรบ้าง», er `general` og besvares med kilder; svarprompten sier allerede at ambassaden avgjør. Med Claude sorterer `MODEL_SMALL`, med Ollama samme modell som svarer (`OLLAMA_MODEL`), og i demomodus de lagrede kategoriene. Feiler sorteringen, vises den faste feilteksten og ingenting besvares.

Sorteringen kjenner også to andre kategorier (Story 2.2). `out_of_scope` er alt annet enn kortvarige turist- og besøksvisum til Norge, f.eks. arbeidsvisum, studier, visum til en reise uten Norge eller været (en reise til Norge og andre Schengen-land er med); det får den faste teksten `reply-out-of-scope` med rådgiverens kontakt. Et spørsmål om kortvarige visum som kildene ikke svarer på, får fortsatt «vi har ikke svar»-teksten. `reach_person` er ønske om å snakke med et menneske eller få hjelp med hele søknaden; det får `reply-reach-person` med rådgiverens kontakt, også når samme melding spør om noe annet. Ingen av dem har kildelenker, og svarmodellen kalles ikke.

### Tilbakemelding på slutten av samtalen

Takker søkeren eller skriver «ok» (f.eks. «ขอบคุณค่ะ 🙏», «Thanks!», «ok.»), sorteres meldingen som `done` og får den faste teksten `feedback-question` («Har du fått all informasjonen du trenger?») med knappene Ja og Nei under. En melding som takker og samtidig spør om noe, f.eks. «thanks, and the fee?», sorteres etter spørsmålet. I demomodus gjelder dette frasene under `done_phrases` i [`content/demo-answers.yaml`](content/demo-answers.yaml), også med tegnsetting og emoji rundt.

- **Nei:** siden viser `feedback-follow-up` («Hva mer vil du vite?»), og samtalen fortsetter. Neste takk gir spørsmålet og knappene på nytt.
- **Ja:** siden viser `feedback-thanks`. Samtalen blir stående på skjermen og blant de lagrede samtalene, og neste spørsmål starter en ny, tom samtale.

Et trykk sender `POST /api/feedback` med `{conversation_id, answer}`, der `answer` er `yes` eller `no`. Serveren lagrer bare `conversation_id`, svaret og tidspunktet (UTC) i tabellen `feedback` i `data/feedback.sqlite3`, aldri spørsmål eller svartekst. Fila, mappa og tabellen lages ved første svar; demomodus lagrer også. `conversation_id` er en tilfeldig UUID som siden lager ved første spørsmål i en samtale og holder i fanens `sessionStorage`. Den sendes bare med tilbakemeldingen og lagres ikke sammen med de lagrede samtalene. «Ny samtale», å åpne en lagret samtale og «Ja» gir en ny ved neste spørsmål.

Hovedmålet (SM-1) er andelen samtaler der det første svaret er «Ja» (mål: minst 80 %). Skriptet `feedback_stats.py` regner det ut fra prosjektmappa:

```sh
uv run python scripts/feedback_stats.py
uv run python scripts/feedback_stats.py --from 2026-11-01 --to 2026-11-30
```

Det skriver antall samtaler med tilbakemelding, hvor mange og hvor stor andel som svarte «Ja» først, og om målet på 80 % er nådd. Bare det første svaret i hver samtale (`conversation_id`) teller, så «Nei» og så «Ja» teller som «Nei». `--from` og `--to` (begge valgfrie, begge dagene tas med) teller samtalene der det første svaret kom i perioden, regnet i UTC slik tidspunktene er lagret. Skriptet leser fila i `DATABASE_PATH` uten å endre den. Finnes ikke fila eller tabellen ennå, eller er det ingen svar i perioden, skriver det at det ikke finnes tilbakemeldinger ennå. En ugyldig dato, `--from` etter `--to` eller en fil som ikke er en SQLite-database, gir en feilmelding (utgangskode 2). Eksempel på utskrift:

```text
Feedback statistics (SM-1), 2026-11-01 to 2026-11-30 (UTC)
Conversations with feedback: 20
First answer "yes": 17 (85.0%)
Target: at least 80% - met
```

### Sjekklister for dokumenter

Hvert besøksformål har én fast dokumentsjekkliste i [`content/checklists.yaml`](content/checklists.yaml): `tourism` (turisme), `family` (besøke familie) og `friends` (besøke venner). Listene er skrevet på forhånd ut fra ambassadens sjekkliste og UDIs sider, og lages aldri av KI-en. Hvert punkt har en fast `id`, tekst på thai og engelsk, og en kilde fra `knowledge-base/sources.yaml`. Punkter som bare gjelder noen søkere (teksten begynner med vilkåret, «Hvis du er ansatt: …»), har `conditional: true`. Familie- og vennelista har med sponsorskjemaet og invitasjonsbrevet, som personen i Norge fyller ut eller skriver, med lenke til UDI, og familielista sier at ambassaden har en egen sjekkliste når familiemedlemmet er borger av et EU/EØS-land. Det er UDIs krav som gjelder (FR6). For søkere i Thailand kommer de som ambassadens offisielle sjekkliste, som søkeren skriver ut, krysser av, signerer og leverer hos VFS. Appens sjekkliste leder søkeren dit gjennom et eget punkt (`signed-embassy-checklist`) med lenke til den. De thai tekstene er godkjent av brukeren (NFR8).

`GET /api/checklists/{purpose}` gir `{purpose, items: [{id, text, en, conditional, source: {title, url}}]}` med thai tekst (`text`) og den lagrede engelske teksten (`en`, som «Show English» viser), i samme rekkefølge som i fila, uten noe KI-kall (også i demomodus). Ukjent formål gir 404 med `{"error": {"code": "unknown_purpose", ...}}`. Appen starter ikke hvis fila mangler et formål, har et ukjent formål eller felt, et punkt uten thai eller engelsk tekst, en `id` som ikke er kebab-case eller som står to ganger i samme liste, en `conditional` som ikke er `true` eller `false`, eller en kilde som ikke finnes. En `id` brukes aldri om igjen til annet innhold, fordi avkrysningene på søkerens telefon lagres per `id`.

På siden er knappen «Sjekkliste» (`checklist-button`) alltid synlig øverst, også mens et svar strømmer. Den åpner sjekklisten i fullskjerm over chatten: først valg av besøksformål, så lista med en stor avkrysningsboks og kildelenke (ny fane) per punkt. Punkter med `conditional: true` har i tillegg et mindre valg, «gjelder ikke meg». En linje viser hvor mange av punktene som gjelder søkeren, som er krysset av («3 av 17 klare»), og en egen tekst vises når alt er klart. «Tilbake» eller Escape lukker sjekklisten, og chatten er uendret, også et svar som var på vei. Alle tekstene kommer fra `/api/texts` (nøklene `checklist-*`); de thai tekstene er godkjent av brukeren (NFR8).

Viser et svar til en kilde som minst ett punkt i en sjekkliste bygger på, får `sources`-hendelsen `checklist: true` og `checklist_purposes` med besøksformålene til disse sjekklistene, i rekkefølgen `tourism`, `family`, `friends` og hvert bare én gang. Serveren regner dette ut fra `content/checklists.yaml`, aldri med KI-en, og likt for Claude, Ollama og demomodus; faste svar, «vi har ikke svar»-teksten og feil gir aldri noen. Siden viser da knappen «Åpne sjekkliste» (`checklist-open`) under svaret. Med ett formål viser knappen formålet og åpner den sjekklisten direkte, med flere først valget av formål; ellers virker den som knappen øverst (fokus, «Tilbake», Escape), også mens et svar strømmer, og fokus går tilbake til knappen under svaret. Formålene lagres sammen med utvekslingen i de lagrede samtalene (`checklistPurposes`), så knappen kommer tilbake når siden lastes på nytt eller samtalen åpnes igjen. Bare kjente formål brukes; samtaler lagret før dette får ingen knapp. Formålene sendes aldri til serveren.

### Vis på engelsk («Show English»)

Sensor leser ikke thai (FR7). Hvert svar som endte med `done` (modellsvar, faste svar og tilbakemeldingsspørsmålet, både nye og i samtaler som åpnes igjen) får derfor knappen `translate-button` («แปลเป็นภาษาอังกฤษ (English)»; ordet «English» står med, så den finnes uten å kunne thai). Den står etter kildene og «Åpne sjekkliste» og før Ja/Nei-knappene. Svar som endte med feil, får ingen. Et trykk sender bare svarteksten, ikke påminnelsen eller kildene, til `POST /api/translate` med `{text}` (1–10 000 tegn) og får `{translation}`. Knappen er avslått mens forespørselen pågår. Går det bra, byttes knappen ut med den engelske teksten (`lang="en"`) under svaret; den thai teksten, kildene og de andre knappene står urørt. Feiler det, vises den faste feilteksten (`error`), og knappen kommer tilbake. Den engelske teksten holdes bare på siden og lagres aldri sammen med samtalen. Kommer svaret etter at samtalen er byttet, ignoreres det. Den thai knappeteksten er godkjent av brukeren (NFR8).

Serveren kjører personvernfilteret først. Er den filtrerte teksten (etter Unicode NFC, sammenslåtte mellomrom og trimming) lik den thai teksten i en fast tekst eller et eksempelspørsmål, får siden den lagrede engelske teksten uten noe KI-kall og uten logglinje. Ellers oversetter KI-en teksten med prompten [`prompts/translate-system.md`](prompts/translate-system.md): med Claude `MODEL_SMALL` (`thinking` sendes ikke, så den lille modellen bestemmer selv, og `EFFORT_SMALL` holder det kort, som ved sorteringen), med Ollama `OLLAMA_MODEL` (uten tenking), og i demomodus de lagrede engelske demosvarene (andre tekster får den engelske `reply-demo-only`). Hver slik oversettelse gir én linje i forespørselsloggen (`endpoint: "translate"`, se under). Feil gir 502 med `{"error": {"code": "translation_failed", ...}}`, en ugyldig body 422 og en body som ikke er `application/json`, 415. Teksten logges aldri. `/api/chat` er uendret.

I sjekklisten viser den samme knappen den lagrede engelske teksten under hvert punkt, uten noen forespørsel. Den står til sjekklisten lukkes eller formålet byttes.

Avkrysningene lagres bare i nettleseren på søkerens enhet (`localStorage`) og sendes aldri til serveren: avkryssede punkt-id-er under `checklist:{purpose}` og «gjelder ikke meg» under `checklist-na:{purpose}`, begge som JSON-lister. Et punkt er aldri begge deler. Når lista lastes, beholdes bare id-er som fortsatt finnes: fjernede punkter ignoreres, og nye punkter starter uavkrysset. Uleselige data regnes som tomme, og er lagringen blokkert eller full, virker avkrysningen mens siden er åpen, men huskes ikke. Logikken står i [`app/static/checklist.js`](app/static/checklist.js) og testes i Node (`tests/test_checklist_js.py`).

### Oppdatere kunnskapsbasen

```sh
uv run python scripts/ingest.py
```

Skriptet henter hver kilde i `sources.yaml` på nytt og skriver om de som har endret seg. Endringene gjennomgås (med rådgiveren) før de committes.

### Testsett

[`eval/testset.yaml`](eval/testset.yaml) er et fast sett med 29 oppdiktede thai spørsmål som måler svarkvaliteten (NFR4, SM-2). Evalueringsskriptet kjører hvert spørsmål gjennom samme flyt som chatsiden og sammenligner med det som er forventet (se «Evaluering» under). Settet dekker søknadsstegene, sjekklisten, sponsorskjemaet, invitasjonsbrevet, bevis på forholdet og gebyret, spørsmål med skrivefeil og med thai og engelsk om hverandre, oppfølgingsspørsmål med en kort historikk, spørsmål om egne sjanser, spørsmål utenfor temaet, grensetilfeller for sorteringen (takk sammen med et spørsmål, egne sjanser sammen med et dokumentspørsmål, et oppfølgingsspørsmål som går over til studietillatelse), fire spørsmål kildene ikke svarer på, fire ulike måter å be om et menneske på, og spørsmål med personopplysninger (thai ID-nummer, passnummer og telefonnummer). Alle tall og personer er oppdiktet: ID-numrene har feil kontrollsiffer.

Hvert spørsmål har disse feltene:

| Felt | Innhold |
|---|---|
| `id` | Fast navn i kebab-case |
| `question`, `en` | Spørsmålet slik en søker skriver det, og en engelsk oversettelse |
| `category` | Kategorien sorteringen skal velge (`general`, `individual_assessment`, `out_of_scope`, `reach_person`, `done`) |
| `outcome` | Hva flyten skal ende i, som i forespørselsloggen: `answered` (svar med kilder), `no_answer` («vi har ikke svar») eller `fixed_reply` (fast tekst for kategorien) |
| `facts`, `sources` | Bare for `answered`: faktaene et riktig svar inneholder (på engelsk), og kildene i `sources.yaml` som sier dem |
| `tags` | Hva spørsmålet dekker, f.eks. `fee`, `typo`, `follow-up` |
| `history` | Bare for oppfølgingsspørsmål: 1–2 tidligere spørsmål og svar |
| `personal_info` | Personopplysninger i spørsmålet (`thai_id`, `passport`, `phone`). Filteret fjerner ID- og passnummer, men beholder telefonnummer |

`scripts/testset.py` leser fila og stopper med en feil som nevner spørsmålet hvis et felt mangler eller er ukjent, en kilde eller kategori ikke finnes, eller utfallet ikke passer til kategorien. `tests/test_testset.py` sjekker i tillegg at alt over er dekket, at filteret fjerner og beholder det det skal, og at hvert tall skrevet med sifre i de forventede faktaene står i en av kildene. De thai tekstene og faktaene er godkjent av brukeren som rådgiver (NFR8).

### Evaluering

Evalueringen kjører hele testsettet mot de ekte modellene og skriver en rapport, slik at man ser om chatboten når kvalitetsmålene (NFR4, SM-2). Kjør den for hånd **etter hver endring i en prompt eller i kunnskapsbasen**, og behold rapportene. Den kjøres ikke i CI.

```sh
uv run python scripts/run_eval.py
```

- Skriptet bruker innstillingene i `.env` og bygger appen akkurat som serveren gjør. Hvert spørsmål går gjennom samme inngang som `POST /api/chat`: filteret, sorteringen og så et svar eller et fast svar. Spørsmålene kjøres ett og ett; feiler ett, står det som `error` i rapporten, og resten kjøres likevel.
- Demomodus (`MOCK_LLM=true`) og Claude uten `ANTHROPIC_API_KEY` avvises med en melding og exit-kode 2, før noe kalles.
- Feiler alle spørsmålene (for eksempel feil nøkkel, feil `LLM_PROVIDER`, eller Ollama som ikke kjører eller mangler modellen), skrives ingen rapport. Skriptet sier hva som er sannsynlige årsaker og avslutter med exit-kode 1. Ellers er exit-koden 0, også når noen sjekker feiler.
- Med `LLM_PROVIDER=ollama` kjøres evalueringen mot den lokale modellen, uten nøkkel og uten kostnad. Rapporten oppgir da `OLLAMA_MODEL` som begge modellene og tar med versjonen av `answer-citing-markers.md` som `citing`.
- **Kostnad:** med Claude koster én kjøring rundt 1 USD (anslag: 18 av de 29 spørsmålene går til svarmodellen, rundt 0,15–0,20 USD for det første og 0,05 USD for hvert av de neste; sorteringen koster nesten ingenting). Den faktiske kostnaden står øverst i rapporten. Med Ollama koster den ingenting.
- Evalueringen skriver ikke til forespørselsloggen. Spørsmålene og svarene står bare i rapporten; i terminalen vises bare navnet på hvert spørsmål og utfallet.

Rapporten havner i `eval/reports/<dato>-<promptversjoner>.md`, for eksempel `2026-11-16-answer-1-classifier-4.md` (med Ollama `...-citing-3.md`). En rapport skrives aldri over: kjøres evalueringen to ganger samme dag, får den neste `-2`, så `-3`. Øverst står dato, leverandør, modellene, promptversjonene, kunnskapsbasen (antall kilder og nyeste `retrieved`-dato), antall spørsmål, tokens og total kostnad. Så kommer totalene mot de fire målene, og deretter én del per spørsmål med det thai spørsmålet, den engelske oversettelsen, forventet og faktisk kategori og utfall, de automatiske sjekkene (bestått/feilet), kildene svaret viste til, selve svaret, de forventede faktaene og en tom linje `Adviser: ` til slutt. Endte et spørsmål i «vi har ikke svar»-teksten, sier linjen `No-answer reason` hvorfor: svaret viste ikke til noen kilde (`no source cited`), det viste bare til ukjente kilde-ID-er (`only unknown source ids cited`), eller det åpnet med setningen om at informasjonen ikke finnes (`opened with the not-available sentence`, vakten i svarflyten). Årsaken står bare i rapporten, ikke i forespørselsloggen.

De automatiske sjekkene per spørsmål:

| Sjekk | Bestått når |
|---|---|
| Kategori | Sorteringen valgte den forventede kategorien |
| Utfall | Flyten endte i det forventede utfallet: `answered`, `no_answer` eller `fixed_reply` (`error` hvis spørsmålet feilet) |
| Kilde | For `answered`: svaret viser til minst én av de forventede kildene. Ellers: svaret viser ikke til noen kilde |
| Personopplysninger | Filteret fjernet noe hvis og bare hvis spørsmålet har et thai ID-nummer eller et passnummer |
| Thai | Svaret inneholder thai skrift |

Et spørsmål som feiler, feiler alle sjekkene. Målene og hvordan de telles:

| Mål | Krav | Telles som riktig når |
|---|---|---|
| Generelle spørsmål riktig besvart med riktig kilde | minst 90 % | Kategori, utfall og kilde er bestått, **og** rådgiveren har skrevet `yes` |
| Spørsmål om egne sjanser får «ambassaden avgjør» | 100 % | Kategori, utfall og kilde er bestått |
| Spørsmål kildene ikke svarer på får «vi har ikke svar» | 100 % | Kategori, utfall og kilde er bestått |
| Ønske om et menneske får rådgiverens kontakt | 100 % | Kategori, utfall og kilde er bestått |

Før rådgiveren har vurdert svarene, står målet for generelle spørsmål som «awaiting adviser», med hvor mange som består de automatiske sjekkene.

**Rådgiverens vurdering.** Rådgiveren leser svaret og de forventede faktaene for hvert spørsmål og skriver `yes` (svaret har faktaene og riktig kilde, og ingenting oppdiktet) eller `no` etter `Adviser:`, for eksempel `Adviser: yes`. Bare det første ordet teller (store eller små bokstaver), så en kommentar kan stå etter, for eksempel `Adviser: no – mangler gebyret`. En tom linje betyr «ikke vurdert ennå». Deretter regnes totalene ut på nytt:

```sh
uv run python scripts/run_eval.py --score eval/reports/2026-11-16-answer-1-classifier-4.md
```

`--score` kaller ingen modell og trenger ingen innstillinger. Den skriver bare om totalblokken (mellom `<!-- totals:start -->` og `<!-- totals:end -->`) i samme fil og lar resten stå, og den lister spørsmålene som fortsatt er tomme. Den kan kjøres så ofte man vil, også før alle linjene er fylt ut. En linje som ikke begynner med `yes` eller `no`, regnes som tom og listes.

**Svarene varierer mellom kjøringer.** Modellene har ingen innstilling for å gi nøyaktig samme svar hver gang, så to kjøringer med samme prompt kan gi litt ulike svar og resultater. Hver rapport vurderes derfor for seg, og rådgiverens vurderinger gjelder bare svarene i den rapporten.

## Mappestruktur

| Mappe | Innhold |
|---|---|
| `app/` | Appen: `main.py` (oppstart), `web/` (API-endepunkter), `pipeline/` (filter, svarflyt, kostnad), `ports/` og `adapters/` (Claude, Ollama, demo, filer), `static/` (chatsiden) |
| `content/` | Faste tekster på thai og engelsk, dokumentsjekklistene og demosvarene. Alle thai tekster godkjennes av rådgiveren (NFR8) |
| `knowledge-base/` | De offisielle kildene som Markdown, og kildelista `sources.yaml` |
| `prompts/` | Systemprompten for svar, prompten som sorterer spørsmålene, og tillegget om kildemerker og thai skrift som bare brukes med Ollama |
| `scripts/` | `ingest.py`, som oppdaterer kunnskapsbasen, `testset.py`, som leser og sjekker testsettet, `run_eval.py`, som kjører evalueringen og regner ut totalene (se «Evaluering»), og `feedback_stats.py`, som regner ut andelen «Ja» (se «Tilbakemelding») |
| `tests/` | Pytest-tester og en falsk KI-klient (`tests/fakes/`) |
| `data/` | Lokale kjøredata (forespørselslogg og tilbakemeldinger i `feedback.sqlite3`); git-ignorert |
| `eval/` | Testsettet `testset.yaml`: oppdiktede thai spørsmål med forventet kategori, fakta og kilder (se «Testsett»), og evalueringsrapportene i `reports/`, som committes (se «Evaluering») |
| `docs/planning/` | Product brief, PRD, arkitektur, epics, sensorveiledning |
| `docs/implementation/` | Spesifikasjon per story, sprintstatus, utsatt arbeid |
| `.logs/` | Sesjonslogger fra hver arbeidsøkt med KI, og lista over åpne punkter |
| `.claude/skills/`, `_bmad/` | BMAD-skillene og oppsettet som ble brukt til å styre KI-arbeidet |

## Prosess og KI-bruk

Appen er utviklet med Claude Code og BMAD-metoden: hvert steg har et eget dokument som det neste bygger på, og hver story har en spesifikasjon, KI-implementering, gjennomgang med flere uavhengige KI-reviewere og en triage der funnene er rettet, utsatt eller avvist med begrunnelse.

| Steg | Dokument |
|---|---|
| Idé | [Product brief](docs/planning/product-brief.md) og [tilbakemelding](docs/planning/tilbakemelding-product-brief.md) |
| Krav | [PRD](docs/planning/prds/prd-G94-sikveland-2026-10-19/prd.md), [tillegg](docs/planning/prds/prd-G94-sikveland-2026-10-19/addendum.md) og [tilbakemelding](docs/planning/prds/prd-G94-sikveland-2026-10-19/tilbakemelding-prd.md) |
| Arkitektur | [Oversikt](docs/planning/architecture/architecture-overview.md), [spine](docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md) og [KI-gjennomganger](docs/planning/architecture/architecture-G94-sikveland-2026-11-02/reviews/) |
| Plan | [Epics og stories](docs/planning/epics.md), [sprintstatus](docs/implementation/sprint-status.yaml) |
| Bygging | Én spesifikasjon per story i [`docs/implementation/`](docs/implementation/), med review-funn og hva som ble gjort med dem |
| Utsatt | [Utsatt arbeid](docs/implementation/deferred-work.md) med begrunnelse |
| Økter | [Sesjonslogger](.logs/wannapas/) og [åpne punkter](.logs/wannapas/issues.md) |

[Implementeringsplanen](docs/planning/implementation-plan.md) er den første arbeidsplanen fra før PRD og arkitektur. Den er beholdt som historikk; der den avviker, gjelder PRD, arkitektur og epics.

Vurderingskriteriene for del 1 står i [sensorveiledningen](docs/planning/sensorveiledning-ibe160-del-1.pdf).

## Forespørselslogg (kostnad og cache)

Appen skriver én JSON-linje per spørsmål og per oversettelse fra KI-en («Show English») til `data/requests.jsonl` (innstillingen `REQUEST_LOG_PATH`; en relativ sti regnes fra prosjektroten). Linja for et spørsmål skrives når svaret er ferdig strømmet, også ved feil eller når brukeren lukker siden. Ugyldige forespørsler (415, 422) og oversettelser fra lagret engelsk tekst logges ikke. Loggen inneholder aldri spørsmålet, svaret, samtalehistorikken, kildene eller teksten som ble oversatt, bare tall og etiketter:

| Felt | Betydning |
|------|-----------|
| `timestamp` | Tidspunkt i UTC (ISO 8601, slutter på `Z`) |
| `endpoint` | `chat` (et spørsmål, `POST /api/chat`) eller `translate` (en oversettelse, `POST /api/translate`) |
| `outcome` | `answered` (svar med kilder), `no_answer` (fast «vi har ikke svar»-tekst), `fixed_reply` (fast tekst for kategorien, f.eks. «bare ambassaden avgjør», uten svarkall), `translated` (oversatt av KI-en), `error` (feil) eller `incomplete` (brukeren gikk før svaret var ferdig) |
| `category` | Spørsmålskategori: `general`, `individual_assessment`, `out_of_scope` eller `reach_person`; `null` hvis forespørselen feilet før den ble kategorisert, og alltid `null` for `translate` |
| `prompt_versions` | Versjonen av promptene som ble brukt, f.eks. `{"answer": "1", "classifier": "4"}`; med Ollama også tillegget, f.eks. `{"answer": "1", "classifier": "4", "citing": "3"}`; for `translate` bare `{"translate": "1"}` |
| `model` | Modellen som svarte eller oversatte (`mock_llm` i demomodus, `OLLAMA_MODEL` med Ollama, `MODEL_SMALL` for `translate` med Claude) |
| `input_tokens`, `output_tokens` | Tokens inn og ut i svarkallet eller oversettelseskallet (ut inkluderer tenking); `null` når modellen ikke ble kalt eller kallet feilet |
| `cache_read_tokens`, `cache_write_tokens` | Tokens lest fra og skrevet til prompt-cachen i svarkallet (alltid 0 med Ollama, som ikke rapporterer det) |
| `classify_input_tokens`, `classify_output_tokens` | Tokens inn og ut i sorteringskallet; `null` når sorteringen feilet, og alltid `null` for `translate` |
| `cost_usd` | Kostnad i USD med seks desimaler: svarkallet regnet med `PRICE_ANSWER_*` pluss sorteringskallet regnet med `PRICE_SMALL_*`; for `translate` oversettelseskallet regnet med `PRICE_SMALL_*` (0 i demomodus og med Ollama) |
| `unknown_source_ids` | Hvor mange kilde-id-er i svaret som ikke finnes i `sources.yaml` og derfor ble droppet (0 når alle var kjente); `null` hvis svaret stoppet før kildene kom, og alltid `null` for `translate` |

Token-feltene er `null` når kallet ikke rapporterte forbruk (typisk ved feil), og `cost_usd` er `null` når ingen av kallene gjorde det.

**Kostnad per spørsmål (anslag).** Med standardprisene og Claude koster det første spørsmålet etter en pause rundt 0,15–0,20 USD, fordi hele kunnskapsbasen skrives til cachen. Spørsmål innen fem minutter etter leser den fra cachen og koster rundt 0,05 USD hver. (Tokentallet «rundt 24 600» i Ollama-delen er Ollamas telling; Claude teller thai tekst annerledes, så tallene her er grove.) Et trykk på «Show English» under et modellsvar kommer i tillegg, men går til den lille modellen og koster lite. Faste svar («bare ambassaden avgjør», andre temaer, ønske om et menneske, tilbakemeldingsspørsmålet) koster bare sorteringskallet med den lille modellen, vanligvis godt under 0,01 USD. Dette er anslag ut fra prisene og tokenmengden, ikke målt. Det faktiske tallet står i `cost_usd` i loggen og i evalueringsrapporten etter en kjøring med Claude. Demomodus og Ollama koster ingenting.

**Virker cachen?** Still to spørsmål innen fem minutter. Den første linja har `cache_write_tokens` > 0, den andre skal ha `cache_read_tokens` > 0 og lavere `cost_usd`. Dette gjelder Claude. Med Ollama er cache-feltene alltid 0, så cachen kan ikke sjekkes i loggen.

**Total kostnad:**

```sh
uv run python -c "import json; print(round(sum(json.loads(l)['cost_usd'] or 0 for l in open('data/requests.jsonl', encoding='utf-8') if l.strip()), 6))"
```

Linjer med `cost_usd: null` (feil, avvisninger, svar som ble brutt av, brukere som gikk) telles ikke med, så summen er en nedre grense for hva spørsmålene faktisk kostet.

Summen tar med oversettelsene. Kostnaden for «Show English» alene (bare linjene med `endpoint: "translate"`; eldre linjer uten `endpoint` er spørsmål):

```sh
uv run python -c "import json; print(round(sum(d['cost_usd'] or 0 for d in map(json.loads, open('data/requests.jsonl', encoding='utf-8')) if d.get('endpoint') == 'translate'), 6))"
```

En oversettelse koster bare det lille modellkallet (`MODEL_SMALL`, priset med `PRICE_SMALL_*`); faste tekster og eksempelspørsmål oversettes fra lagret tekst og koster ingenting.
