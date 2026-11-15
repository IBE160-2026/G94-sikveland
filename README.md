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
- Logg over kostnad, tokens og cache per spørsmål (Story 1.8)
- **Demomodus** som virker uten API-nøkkel (Story 4.2)

Ikke laget ennå: «embassy decides»-svar for spørsmål om egen sak og andre visumtyper (Epic 2), sjekklister for dokumenter (Epic 3) og knappen «Show English» (Story 4.1). Hele planen står i [epics.md](docs/planning/epics.md), og status per story står i [sprint-status.yaml](docs/implementation/sprint-status.yaml).

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

### Innstillinger

Alle innstillinger står med forklaring i [`.env.example`](.env.example). Et feilstavet navn i `.env` stopper oppstarten, slik at det ikke blir ignorert i det stille.

| Innstilling | Standard | Betydning |
|---|---|---|
| `ANTHROPIC_API_KEY` | tom | Nøkkel til Claude API; ikke nødvendig i demomodus |
| `MOCK_LLM` | `false` | `true` = demomodus med lagrede svar |
| `MODEL_ANSWER`, `EFFORT_ANSWER` | `claude-opus-5-5`, `medium` | Modellen som skriver svarene |
| `MODEL_SMALL`, `EFFORT_SMALL` | `claude-haiku-5-5`, `low` | Liten modell til enkle oppgaver |
| `ADVISER_CONTACT` | rådgiverens e-post | Vises når chatboten ikke kan hjelpe |
| `REQUEST_LOG_PATH` | `data/requests.jsonl` | Forespørselsloggen (se under) |
| `PRICE_*` | Anthropics priser | USD per million tokens, brukt til kostnadsloggen |

## Tester

```sh
uv run pytest
```

Testene bruker en falsk KI-klient og kaller aldri Claude API, så de trenger ingen nøkkel og koster ingenting. De samme testene kjøres av [GitHub Actions](.github/workflows/ci.yml) ved hver push.

## Slik virker det

```text
Nettleser (app/static)  →  POST /api/chat  →  personvernfilter  →  Claude med kunnskapsbasen i prompten
                        ←  strøm av JSON-linjer: tekstbiter, kilder, ferdig
```

- Hele kunnskapsbasen (`knowledge-base/*.md`) sendes med i systemprompten og caches hos Anthropic, så gjentatte spørsmål blir billigere. Appen henter ingenting fra nettet mens den kjører.
- Svaret må oppgi hvilke kilder det bygger på. Kildelenkene hentes fra [`knowledge-base/sources.yaml`](knowledge-base/sources.yaml); viser svaret til en kilde som ikke står der, stoppes det med feiltekst.
- Koden er delt i lag (porter og adaptere): `pipeline` kjenner ikke til FastAPI eller Anthropic, og `tests/test_layering.py` sjekker at det holder.

Mer i [arkitekturoversikten](docs/planning/architecture/architecture-overview.md), skrevet for sensor, og i de bindende reglene i [ARCHITECTURE-SPINE.md](docs/planning/architecture/architecture-G94-sikveland-2026-11-02/ARCHITECTURE-SPINE.md).

### Oppdatere kunnskapsbasen

```sh
uv run python scripts/ingest.py
```

Skriptet henter hver kilde i `sources.yaml` på nytt og skriver om de som har endret seg. Endringene gjennomgås (med rådgiveren) før de committes.

## Mappestruktur

| Mappe | Innhold |
|---|---|
| `app/` | Appen: `main.py` (oppstart), `web/` (API-endepunkter), `pipeline/` (filter, svarflyt, kostnad), `ports/` og `adapters/` (Claude, demo, filer), `static/` (chatsiden) |
| `content/` | Faste tekster på thai og engelsk, og demosvarene. Alle thai tekster godkjennes av rådgiveren (NFR8) |
| `knowledge-base/` | De offisielle kildene som Markdown, og kildelista `sources.yaml` |
| `prompts/` | Systemprompten for svar |
| `scripts/` | `ingest.py`, som oppdaterer kunnskapsbasen |
| `tests/` | Pytest-tester og en falsk KI-klient (`tests/fakes/`) |
| `data/` | Lokale kjøredata (forespørselslogg); git-ignorert |
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
| `outcome` | `answered` (svar med kilder), `no_answer` (fast «vi har ikke svar»-tekst), `error` (feil) eller `incomplete` (brukeren gikk før svaret var ferdig) |
| `category` | Spørsmålskategori (foreløpig alltid `general`); `null` hvis forespørselen feilet før den ble kategorisert |
| `prompt_versions` | Versjonen av prompten som ble brukt, f.eks. `{"answer": "1"}` |
| `model` | Modellen som svarte (`mock_llm` i demomodus) |
| `input_tokens`, `output_tokens` | Tokens inn og ut (ut inkluderer tenking) |
| `cache_read_tokens`, `cache_write_tokens` | Tokens lest fra og skrevet til prompt-cachen |
| `cost_usd` | Kostnad i USD med seks desimaler, regnet med `PRICE_ANSWER_*`-prisene (0 i demomodus) |

Token-feltene og `cost_usd` er `null` når modellen ikke rapporterte forbruk (typisk ved feil).

**Virker cachen?** Still to spørsmål innen fem minutter. Den første linja har `cache_write_tokens` > 0, den andre skal ha `cache_read_tokens` > 0 og lavere `cost_usd`.

**Total kostnad:**

```sh
uv run python -c "import json; print(round(sum(json.loads(l)['cost_usd'] or 0 for l in open('data/requests.jsonl', encoding='utf-8') if l.strip()), 6))"
```

Linjer med `cost_usd: null` (feil, avvisninger, svar som ble brutt av, brukere som gikk) telles ikke med, så summen er en nedre grense for hva spørsmålene faktisk kostet.
