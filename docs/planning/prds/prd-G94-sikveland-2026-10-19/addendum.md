# Addendum: PRD Norway Visa Guide For Thai

Detail that belongs in architecture or UX documents rather than the PRD.

## For architecture

- **Checklist content.** Checklists are fixed files per visit purpose, each item with a stable ID so saved ticks still match after content updates.
- **Checklist progress storage.** The user expects ticked checklist items to be kept between visits on the same phone and browser, with no account. They suggested cookies or cache; browser local storage is the likely fit. Nothing about the checklist is stored on the server.
- **Facebook in-app browser.** Users arrive from a link on the adviser's Facebook page, so the chat page must work in Facebook's in-app browser, not only in Chrome or Safari.
- **Stack.** Python with FastAPI, a simple HTML/JavaScript chat page, and SQLite for storing feedback answers (from the product brief).
- **Language model.** Claude Opus 5.5, set in a configuration file so it can be changed without code changes.
- **How answers are built.** The whole knowledge base is sent with each question, using prompt caching so the sources are not paid for in full each time, and Claude's Citations feature so each answer quotes the source text it uses. No separate search database; the knowledge base is small enough.
- **Question classifier.** Before answering, a separate model call sorts the already-cleaned question into `general`, `individual_assessment` or `out_of_scope` with structured output. Only `general` goes on to the answering step. The classifier prompt is a versioned file (NFR7). This is how FR3 and FR14 are made reliable.
- **Personal information deletion (FR9).** Deletion must happen before the question leaves the server for the AI service, so it cannot rely on the model: a pattern-based filter for passport, ID and phone numbers runs first. The cleaned question is then classified and answered as normal, and a reminder not to send personal information is added to the answer. Addresses were dropped from the definition because they cannot be detected reliably by pattern. The exact mechanism is an architecture decision.
- **Adviser contact.** Read from configuration (`ADVISER_CONTACT`), not hard-coded in prompts or texts.
- **Two test layers.** Automated tests in GitHub Actions use a mock model client and never call the real API (NFR3). The test set (NFR4) runs as a separate evaluation against the real model after prompt or source changes, with results recorded.
- **Demo mode.** `MOCK_LLM=true`; stored answers in `eval/demo-answers.yaml` (Thai answer, sources and English translation per example question).
- **Cost.** Opus 5.5 costs $4 per million input tokens and $20 per million output tokens; cached sources cost less. Cost per question is measured during development and reported in the README (NFR6).
- **Running and following it.** The README explains running with your own key (`.env.example`) or in demo mode, and lists the example questions with English and Norwegian translations for the examiner.
- **Knowledge base storage.** Each source is a Markdown copy in the repository with URL, publisher and retrieval date; one file lists all sources so answers trace to a source version (FR11).

## For UX

### Sample dialogue behind UJ-2 (written by the user)

Michael wants to visit his aunt but does not know what to do, so he asks the chatbot for help.

> **Michael:** I want to visit my biological aunt. What should I do first?
>
> **Chatbot:** The first step is to prepare the required documents according to the checklist on the Norwegian Embassy's website (using the checklist translated into Thai). Make sure all documents meet the embassy's requirements. Then register your visa application (link to the UDI application page) and pay the visa fee. Once all your documents are ready, book an appointment with VFS Norway in Thailand (link to VFS).
>
> **Michael:** What documents do I need to prove our family relationship?
>
> **Chatbot:** You can use a house registration document.
>
> **Michael:** Thank you very much. If I cannot manage the application myself and need an agency to help me with the entire process, what should I do?
>
> **Chatbot:** You can contact the agency directly by email at ngan.visaa@gmail.com.
>
> **Michael:** Thank you.
>
> **Chatbot:** You're welcome! Have you received all the information you need? If so, answer "Yes." If you have more questions, press "No."
>
> **Michael:** No.
>
> **Chatbot:** What would you still like to know?
>
> **Michael:** I forgot to ask how much the visa fee is.
>
> **Chatbot:** 90 euros.
>
> **Michael:** Okay.
>
> **Chatbot:** Have you received all the information you need? If so, answer "Yes." If you have more questions, press "No."
>
> **Michael:** Yes.
>
> The conversation ends.
