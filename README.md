# G94 — JaJa Number 4

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng).

Repoet inneholder gruppens applikasjon og dokumentasjon av utvikling, testing og kvalitetssikring med KI.

## Medlemmer

- Wannapa Sikveland

## Dokumentasjon

Planleggingsdokumenter ligger i [`docs/planning/`](docs/planning/):

- [Product brief](docs/planning/product-brief.md)
- [Tilbakemelding på product brief](docs/planning/tilbakemelding-product-brief.md)
- [Implementeringsplan](docs/planning/implementation-plan.md)
- [Epics og user stories](docs/planning/epics-and-stories.md)

## Forespørselslogg (kostnad og cache)

Appen skriver én JSON-linje per spørsmål til `data/requests.jsonl` (innstillingen `REQUEST_LOG_PATH` i `.env`; en relativ sti regnes fra prosjektroten). Linja skrives når svaret er ferdig strømmet, også ved feil eller når brukeren lukker siden. Ugyldige forespørsler (422) logges ikke. Loggen inneholder aldri spørsmålet, svaret, samtalehistorikken eller kildene, bare tall og etiketter:

| Felt | Betydning |
|------|-----------|
| `timestamp` | Tidspunkt i UTC (ISO 8601, slutter på `Z`) |
| `outcome` | `answered` (svar med kilder), `no_answer` (fast «vi har ikke svar»-tekst), `error` (feil) eller `incomplete` (brukeren gikk før svaret var ferdig) |
| `category` | Spørsmålskategori (foreløpig alltid `general`); `null` hvis forespørselen feilet før den ble kategorisert |
| `prompt_versions` | Versjonen av prompten som ble brukt, f.eks. `{"answer": "1"}` |
| `model` | Modellen som svarte |
| `input_tokens`, `output_tokens` | Tokens inn og ut (ut inkluderer tenking) |
| `cache_read_tokens`, `cache_write_tokens` | Tokens lest fra og skrevet til prompt-cachen |
| `cost_usd` | Kostnad i USD med seks desimaler, regnet med `PRICE_ANSWER_*`-prisene |

Token-feltene og `cost_usd` er `null` når modellen ikke rapporterte forbruk (typisk ved feil).

**Virker cachen?** Still to spørsmål innen fem minutter. Den første linja har `cache_write_tokens` > 0, den andre skal ha `cache_read_tokens` > 0 og lavere `cost_usd`.

**Total kostnad:**

```sh
uv run python -c "import json; print(round(sum(json.loads(l)['cost_usd'] or 0 for l in open('data/requests.jsonl', encoding='utf-8') if l.strip()), 6))"
```

Linjer med `cost_usd: null` (feil, avvisninger, svar som ble brutt av, brukere som gikk) telles ikke med, så summen er en nedre grense for hva spørsmålene faktisk kostet.
