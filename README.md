# G94 — Norway Visa Guide For Thai

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng).

**Norway Visa Guide For Thai** er en chatbot på thai for søkere av visum for kortvarig besøk i Norge (turist- og besøksvisum). Søkeren åpner en mobil nettside, stiller et spørsmål på thai og får et svar som strømmes inn bit for bit, med lenker til de offisielle kildene svaret bygger på (UDI, Norges ambassade i Bangkok, EU). Chatboten svarer bare ut fra en fast kunnskapsbase med disse kildene, og gir kontakten til rådgiveren når den ikke har svar.

Bakgrunnen er at én rådgiver i dag svarer på de samme spørsmålene fra mange søkere på e-post, ofte om kvelden og i helgene. Se [product brief](docs/planning/product-brief.md) og [PRD](docs/planning/prds/prd-G94-sikveland-2026-10-19/prd.md).

## Medlemmer

- Wannapa Sikveland

## Status (del 1, 2026-11-15)

Ferdig og testet:

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
- Valgfritt: svar fra en lokal modell via [Ollama](https://ollama.com) i stedet for Claude, så appen ikke er avhengig av én bestemt KI-tjeneste ([spesifikasjon](docs/implementation/spec-ollama-provider.md))

Ikke laget ennå: knappen «Show English» (Story 4.1). Hele planen står i [epics.md](docs/planning/epics.md), og status per story står i [sprint-status.yaml](docs/implementation/sprint-status.yaml).

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

| Eksempelspørsmål (thai) | På norsk |
|---|---|
| ขอวีซ่าท่องเที่ยวนอร์เวย์ต้องใช้เอกสารอะไรบ้าง | Hvilke dokumenter trenger jeg til turistvisum til Norge? |
| ถ้าจะขอวีซ่าไปนอร์เวย์ ต้องเริ่มต้นอย่างไร | Hvordan begynner jeg å søke visum til Norge? |
| ค่าธรรมเนียมวีซ่านอร์เวย์ราคาเท่าไร | Hva koster visum til Norge? |
| การพิจารณาวีซ่าใช้เวลานานเท่าไร | Hvor lang er behandlingstiden? |

Hvert av dem gir et lagret thai svar med kildelenker. Andre spørsmål gir en fast tekst om at demoen bare svarer på eksempelspørsmålene. Svarene står i [`content/demo-answers.yaml`](content/demo-answers.yaml), med engelsk oversettelse.

Vil du teste på en mobil på samme nettverk, start med `--host 0.0.0.0` og åpne `http://<maskinens-IP>:8000` på mobilen.

### Kjør med Claude (ekte svar)

1. Kopier [`.env.example`](.env.example) til `.env`.
2. Sett `ANTHROPIC_API_KEY` til nøkkelen din, og la `MOCK_LLM=false` stå.
3. Start med `uv run uvicorn app.main:app`.

Uten nøkkel starter appen likevel, men hvert spørsmål gir en fast feiltekst. `.env` er git-ignorert og skal aldri committes.

### Kjør med Ollama (lokal modell, uten nøkkel)

Svarene kan også komme fra en modell som kjører på din egen maskin. Det koster ingenting og trenger ingen nøkkel, men krever et grafikkort med nok minne (testet med `qwen3.5:9b` på et kort med 16 GB) og gir svakere svar enn Claude.

1. Installer [Ollama](https://ollama.com) og hent modellen: `ollama pull qwen3.5:9b`. Modellen må støtte tenking (thinking), for appen slår den alltid på.
2. Sett `LLM_PROVIDER=ollama` i `.env` (og la `MOCK_LLM=false` stå). `OLLAMA_BASE_URL`, `OLLAMA_MODEL` og `OLLAMA_NUM_CTX` har standardverdier som passer for en vanlig Ollama-installasjon.
3. Start Ollama, og så appen med `uv run uvicorn app.main:app`.

Appen sender med `num_ctx` (standard 32768 tokens) i hver forespørsel. Kunnskapsbasen er rundt 24 600 tokens, og Ollamas egen standard på 4096 ville kuttet den uten å si fra. Det første svaret etter at Ollama har startet tar ekstra tid, fordi modellen må lese hele kunnskapsbasen (rundt 7 sekunder på et grafikkort med 16 GB, mye lenger uten grafikkort); deretter gjenbruker Ollama den. Fordi modellen tenker før den svarer, tok et svar i testene fra 6 sekunder til over ett minutt.

Uten Claudes innebygde kildehenvisninger skriver modellen kildene som `[[kilde-id]]` i teksten. Appen gjør dem om til kildelenker og fjerner dem fra teksten, så søkeren ser det samme som med Claude. Reglene for dette, og en regel om å bare skrive thai skrift, står i [`prompts/answer-citing-markers.md`](prompts/answer-citing-markers.md), som bare brukes med Ollama. En liten modell blander av og til inn ord eller tegn fra andre skriftsystemer, mest kinesisk. I en test med 36 svar før og 36 svar etter regelen gjaldt det 5 og 2 svar: færre, men ikke null, og for få svar til å bevise at regelen virker. Ollama-svar bør derfor leses av en som kan thai før de brukes overfor søkere.

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
| `MODEL_SMALL`, `EFFORT_SMALL` | `claude-haiku-5-5`, `low` | Liten modell til enkle oppgaver, som å sortere spørsmålene (se under) |
| `ADVISER_CONTACT` | rådgiverens e-post | Vises når chatboten ikke kan hjelpe |
| `REQUEST_LOG_PATH` | `data/requests.jsonl` | Forespørselsloggen (se under) |
| `DATABASE_PATH` | `data/feedback.sqlite3` | SQLite-fila med tilbakemeldingene (se under); en relativ sti regnes fra prosjektmappa |
| `PRICE_*` | Anthropics priser | USD per million tokens, brukt til kostnadsloggen |

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
- Svaret må oppgi hvilke kilder det bygger på. Kildelenkene hentes fra [`knowledge-base/sources.yaml`](knowledge-base/sources.yaml). Viser svaret til en kilde som ikke står der, får den kilden ingen lenke, resten av svaret vises, og antallet telles i forespørselsloggen. Viser svaret ikke til noen kjent kilde, får søkeren den faste «vi har ikke svar»-teksten.
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

Hovedmålet (SM-1) er andelen samtaler der det første svaret er «Ja» (mål: minst 80 %). Til skriptet `feedback_stats.py` er laget (Epic 5), kan det telles med Python fra prosjektmappa (virker i både PowerShell og Bash, uten flere programmer):

```sh
uv run python -c "import sqlite3; q='SELECT ROUND(100.0 * SUM(answer = ?) / COUNT(*), 1), COUNT(*) FROM (SELECT f.answer FROM feedback f WHERE f.rowid = (SELECT MIN(rowid) FROM feedback WHERE conversation_id = f.conversation_id))'; print(sqlite3.connect('data/feedback.sqlite3').execute(q, ('yes',)).fetchone())"
```

Det skriver `(prosent Ja, antall samtaler)`, f.eks. `(85.0, 20)`. Uten svar i tabellen finnes det ingen andel: da står det `(None, 0)`, og før det første svaret er lagret, finnes ikke tabellen (`no such table: feedback`). Har du kommandolinjeverktøyet `sqlite3` (det følger sjelden med Windows), gir dette det samme:

```sh
sqlite3 data/feedback.sqlite3 "SELECT ROUND(100.0 * SUM(answer = 'yes') / COUNT(*), 1) AS prosent_ja, COUNT(*) AS samtaler FROM (SELECT f.answer FROM feedback f WHERE f.rowid = (SELECT MIN(rowid) FROM feedback WHERE conversation_id = f.conversation_id))"
```

### Sjekklister for dokumenter

Hvert besøksformål har én fast dokumentsjekkliste i [`content/checklists.yaml`](content/checklists.yaml): `tourism` (turisme), `family` (besøke familie) og `friends` (besøke venner). Listene er skrevet på forhånd ut fra ambassadens sjekkliste og UDIs sider, og lages aldri av KI-en. Hvert punkt har en fast `id`, tekst på thai og engelsk, og en kilde fra `knowledge-base/sources.yaml`. Punkter som bare gjelder noen søkere (teksten begynner med vilkåret, «Hvis du er ansatt: …»), har `conditional: true`. Familie- og vennelista har med sponsorskjemaet og invitasjonsbrevet, som personen i Norge fyller ut eller skriver, med lenke til UDI, og familielista sier at ambassaden har en egen sjekkliste når familiemedlemmet er borger av et EU/EØS-land. Det er UDIs krav som gjelder (FR6). For søkere i Thailand kommer de som ambassadens offisielle sjekkliste, som søkeren skriver ut, krysser av, signerer og leverer hos VFS. Appens sjekkliste leder søkeren dit gjennom et eget punkt (`signed-embassy-checklist`) med lenke til den. De thai tekstene er godkjent av brukeren (NFR8).

`GET /api/checklists/{purpose}` gir `{purpose, items: [{id, text, conditional, source: {title, url}}]}` med thai tekst, i samme rekkefølge som i fila, uten noe KI-kall (også i demomodus). Ukjent formål gir 404 med `{"error": {"code": "unknown_purpose", ...}}`. Appen starter ikke hvis fila mangler et formål, har et ukjent formål eller felt, et punkt uten thai eller engelsk tekst, en `id` som ikke er kebab-case eller som står to ganger i samme liste, en `conditional` som ikke er `true` eller `false`, eller en kilde som ikke finnes. En `id` brukes aldri om igjen til annet innhold, fordi avkrysningene på søkerens telefon lagres per `id`.

På siden er knappen «Sjekkliste» (`checklist-button`) alltid synlig øverst, også mens et svar strømmer. Den åpner sjekklisten i fullskjerm over chatten: først valg av besøksformål, så lista med en stor avkrysningsboks og kildelenke (ny fane) per punkt. Punkter med `conditional: true` har i tillegg et mindre valg, «gjelder ikke meg». En linje viser hvor mange av punktene som gjelder søkeren, som er krysset av («3 av 17 klare»), og en egen tekst vises når alt er klart. «Tilbake» eller Escape lukker sjekklisten, og chatten er uendret, også et svar som var på vei. Alle tekstene kommer fra `/api/texts` (nøklene `checklist-*`); de thai tekstene er godkjent av brukeren (NFR8).

Viser et svar til en kilde som minst ett punkt i en sjekkliste bygger på, får `sources`-hendelsen `checklist: true` og `checklist_purposes` med besøksformålene til disse sjekklistene, i rekkefølgen `tourism`, `family`, `friends` og hvert bare én gang. Serveren regner dette ut fra `content/checklists.yaml`, aldri med KI-en, og likt for Claude, Ollama og demomodus; faste svar, «vi har ikke svar»-teksten og feil gir aldri noen. Siden viser da knappen «Åpne sjekkliste» (`checklist-open`) under svaret. Med ett formål viser knappen formålet og åpner den sjekklisten direkte, med flere først valget av formål; ellers virker den som knappen øverst (fokus, «Tilbake», Escape), også mens et svar strømmer, og fokus går tilbake til knappen under svaret. Formålene lagres sammen med utvekslingen i de lagrede samtalene (`checklistPurposes`), så knappen kommer tilbake når siden lastes på nytt eller samtalen åpnes igjen. Bare kjente formål brukes; samtaler lagret før dette får ingen knapp. Formålene sendes aldri til serveren.

Avkrysningene lagres bare i nettleseren på søkerens enhet (`localStorage`) og sendes aldri til serveren: avkryssede punkt-id-er under `checklist:{purpose}` og «gjelder ikke meg» under `checklist-na:{purpose}`, begge som JSON-lister. Et punkt er aldri begge deler. Når lista lastes, beholdes bare id-er som fortsatt finnes: fjernede punkter ignoreres, og nye punkter starter uavkrysset. Uleselige data regnes som tomme, og er lagringen blokkert eller full, virker avkrysningen mens siden er åpen, men huskes ikke. Logikken står i [`app/static/checklist.js`](app/static/checklist.js) og testes i Node (`tests/test_checklist_js.py`).

### Oppdatere kunnskapsbasen

```sh
uv run python scripts/ingest.py
```

Skriptet henter hver kilde i `sources.yaml` på nytt og skriver om de som har endret seg. Endringene gjennomgås (med rådgiveren) før de committes.

## Mappestruktur

| Mappe | Innhold |
|---|---|
| `app/` | Appen: `main.py` (oppstart), `web/` (API-endepunkter), `pipeline/` (filter, svarflyt, kostnad), `ports/` og `adapters/` (Claude, Ollama, demo, filer), `static/` (chatsiden) |
| `content/` | Faste tekster på thai og engelsk, dokumentsjekklistene og demosvarene. Alle thai tekster godkjennes av rådgiveren (NFR8) |
| `knowledge-base/` | De offisielle kildene som Markdown, og kildelista `sources.yaml` |
| `prompts/` | Systemprompten for svar, prompten som sorterer spørsmålene, og tillegget om kildemerker og thai skrift som bare brukes med Ollama |
| `scripts/` | `ingest.py`, som oppdaterer kunnskapsbasen |
| `tests/` | Pytest-tester og en falsk KI-klient (`tests/fakes/`) |
| `data/` | Lokale kjøredata (forespørselslogg og tilbakemeldinger i `feedback.sqlite3`); git-ignorert |
| `eval/` | Plass til evalueringssettet (ikke laget ennå) |
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

Appen skriver én JSON-linje per spørsmål til `data/requests.jsonl` (innstillingen `REQUEST_LOG_PATH`; en relativ sti regnes fra prosjektroten). Linja skrives når svaret er ferdig strømmet, også ved feil eller når brukeren lukker siden. Ugyldige forespørsler (422) logges ikke. Loggen inneholder aldri spørsmålet, svaret, samtalehistorikken eller kildene, bare tall og etiketter:

| Felt | Betydning |
|------|-----------|
| `timestamp` | Tidspunkt i UTC (ISO 8601, slutter på `Z`) |
| `outcome` | `answered` (svar med kilder), `no_answer` (fast «vi har ikke svar»-tekst), `fixed_reply` (fast tekst for kategorien, f.eks. «bare ambassaden avgjør», uten svarkall), `error` (feil) eller `incomplete` (brukeren gikk før svaret var ferdig) |
| `category` | Spørsmålskategori: `general`, `individual_assessment`, `out_of_scope` eller `reach_person`; `null` hvis forespørselen feilet før den ble kategorisert |
| `prompt_versions` | Versjonen av promptene som ble brukt, f.eks. `{"answer": "1", "classifier": "2"}`; med Ollama også tillegget, f.eks. `{"answer": "1", "classifier": "2", "citing": "2"}` |
| `model` | Modellen som svarte (`mock_llm` i demomodus, `OLLAMA_MODEL` med Ollama) |
| `input_tokens`, `output_tokens` | Tokens inn og ut i svarkallet (ut inkluderer tenking); `null` når svarmodellen ikke ble kalt |
| `cache_read_tokens`, `cache_write_tokens` | Tokens lest fra og skrevet til prompt-cachen i svarkallet (alltid 0 med Ollama, som ikke rapporterer det) |
| `classify_input_tokens`, `classify_output_tokens` | Tokens inn og ut i sorteringskallet; `null` når sorteringen feilet |
| `cost_usd` | Kostnad i USD med seks desimaler: svarkallet regnet med `PRICE_ANSWER_*` pluss sorteringskallet regnet med `PRICE_SMALL_*` (0 i demomodus og med Ollama) |
| `unknown_source_ids` | Hvor mange kilde-id-er i svaret som ikke finnes i `sources.yaml` og derfor ble droppet (0 når alle var kjente); `null` hvis svaret stoppet før kildene kom |

Token-feltene er `null` når kallet ikke rapporterte forbruk (typisk ved feil), og `cost_usd` er `null` når ingen av kallene gjorde det.

**Virker cachen?** Still to spørsmål innen fem minutter. Den første linja har `cache_write_tokens` > 0, den andre skal ha `cache_read_tokens` > 0 og lavere `cost_usd`. Dette gjelder Claude. Med Ollama er cache-feltene alltid 0, så cachen kan ikke sjekkes i loggen.

**Total kostnad:**

```sh
uv run python -c "import json; print(round(sum(json.loads(l)['cost_usd'] or 0 for l in open('data/requests.jsonl', encoding='utf-8') if l.strip()), 6))"
```

Linjer med `cost_usd: null` (feil, avvisninger, svar som ble brutt av, brukere som gikk) telles ikke med, så summen er en nedre grense for hva spørsmålene faktisk kostet.
