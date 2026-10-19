# Product Brief: Norway Visa Guide For Thai By Wannapa

## Executive Summary

This project aims to develop a Thai-language AI chatbot that provides general information about short-stay tourist and visitor visas for Norway. Through my work helping Thai applicants, I have found that many have limited knowledge of visa procedures and find it difficult to locate and understand information online. As the only adviser, I receive questions from dozens of people each day, at different times of the day and night. This creates a heavy workload and leaves applicants waiting when I am unavailable.

The chatbot will answer common questions 24 hours a day, explaining basic application steps, general document requirements, and visa terms in clear Thai. Its answers will be based on selected official sources and include references. The first version will focus on general information, with questions requiring an individual assessment directed to a human adviser or the relevant authority. The volume of enquiries makes this a useful time to introduce a tool that helps applicants receive faster answers and reduces repetitive work.

Success will be measured through users’ feedback on whether they received the information they needed, together with reductions in the number of questions answered manually and the time spent answering them. If the first version is successful, the chatbot will gradually cover more visa types over the next two to three years. The long-term vision is to offer user accounts and a paid service for more personalised guidance, while keeping human support available for complex cases.

## The Problem

I currently help Thai people apply for short-stay visas to visit Norway for tourism or to visit family and friends. Through this work, I have found that many applicants have limited knowledge of visa procedures and lack the digital skills needed to find and understand information online. They therefore rely on personal assistance to understand the application process and prepare their documents.

I receive many questions at different times of the day and night. Answering each person individually takes time, and I cannot provide support 24 hours a day. This means applicants may have to wait for guidance, while handling repeated questions makes it difficult for me to focus on people who need more detailed assistance.

## The Solution

The proposed solution is an interactive chatbot that provides information in Thai about short-stay tourist and visitor visas for Norway. Users will be able to ask questions in everyday language and receive clear explanations of the application process, document requirements, and common visa terms. Answers will be based on selected official sources and include references so users can check the information.

The chatbot will be available 24 hours a day to answer common questions, helping users find basic information without waiting for a personal reply. When a question is too complex or the available information is insufficient, it will explain its limitations and direct the user to human assistance or the relevant authority. This will help reduce repetitive enquiries and allow more time for cases that need individual support.

### Where users meet the chatbot

Users open the chatbot as a web page on their phone, for example from a link I share when people contact me. The page has one chat field, large buttons, and example questions to tap, so users with limited digital skills can start without typing. Each answer shows its sources as links underneath. A "Show English translation" button lets non-Thai readers, such as the course examiner, follow the conversation.

### Example conversation

The example below shows the intended behaviour. The facts in it must be checked against the final knowledge base.

**A general question answered with sources**

> **User:** ต้องใช้เอกสารอะไรบ้างในการขอวีซ่าท่องเที่ยวนอร์เวย์?
> _(What documents do I need to apply for a tourist visa to Norway?)_
>
> **Chatbot:** สำหรับวีซ่าท่องเที่ยวระยะสั้น โดยทั่วไปต้องเตรียมเอกสารดังนี้:
> 1. หนังสือเดินทางที่มีอายุเหลืออย่างน้อย 3 เดือนหลังวันเดินทางออกจากเขตเชงเก้น [1]
> 2. ประกันการเดินทางที่มีวงเงินคุ้มครองอย่างน้อย 30,000 ยูโร [1]
> 3. ...
>
> แหล่งข้อมูล: [1] UDI – รายการเอกสารสำหรับวีซ่าเยี่ยมเยือน (ประเทศไทย)
>
> _(For a short-stay tourist visa you generally need: 1. a passport valid for at least 3 months after you leave the Schengen area [1]; 2. travel insurance with at least €30,000 coverage [1]; 3. … Source: [1] UDI – Visit visa checklist (Thailand))_

**A question that needs an individual assessment**

> **User:** ฉันเคยถูกปฏิเสธวีซ่ามาก่อน ครั้งนี้จะผ่านไหม?
> _(I have been refused a visa before. Will I get it this time?)_
>
> **Chatbot:** ขออภัย คำถามนี้ต้องพิจารณาตามสถานการณ์ส่วนตัวของคุณ ซึ่งแชทบอทไม่สามารถประเมินได้ กรุณาติดต่อที่ปรึกษาด้านวีซ่า หรือ UDI โดยตรง
>
> _(Sorry, this question depends on your personal situation, which the chatbot cannot assess. Please contact a visa adviser or UDI directly.)_

## What Makes This Different

The main strengths of this product are fast responses, 24-hour availability, and less time spent answering repeated questions. Currently, I work alone and respond to questions from dozens of people each day. Providing this support individually creates a heavy workload, and applicants may have to wait until I am available.

Unlike relying entirely on personal replies, the chatbot will answer common questions in Thai at any time. Applicants can receive basic guidance quickly, while I spend less time repeating the same information. This benefits both sides: applicants have shorter waiting times, and I have a more manageable workload and more time to help with complex cases.

Applicants have other options today, but each has gaps:

- **UDI and VFS Global websites** are the authoritative sources, but most content is in Norwegian or English, and the information is spread across many pages. Applicants with limited digital skills struggle to find what applies to them.
- **General AI chatbots** answer in Thai, but they do not limit themselves to official sources, may give outdated or invented requirements, and rarely say when a question needs an individual assessment.

This chatbot combines the strengths of both: it answers in clear Thai, uses only a selected set of official sources, shows where each answer comes from, and refers individual cases onward instead of guessing.

## Who This Serves

The primary users are Thai people who want to apply for a short-stay visa to visit Norway for tourism or to visit family and friends. They need clear information in Thai about the application process and required documents, especially if they have limited visa knowledge or digital skills. Success means they can find answers quickly and understand what they need to prepare.

Secondary users are members of the public who want to learn about these visas, even if they are not currently planning to apply. The chatbot gives them an accessible way to explore basic visa information.

## Knowledge Base

The chatbot will answer only from a fixed collection of 10–20 selected pages and documents from official sources:

- **UDI (Norwegian Directorate of Immigration):** rules for visit visas, document checklists for applicants from Thailand, and common terms.
- **VFS Global (Norway visa application centre in Thailand):** how to book an appointment, submit the application, and pay fees.
- **Royal Norwegian Embassy in Bangkok:** general information for Thai applicants.
- **European Commission Schengen visa pages:** general Schengen terms, where UDI refers to them.

Each source is stored in the repository as a Markdown copy with its URL, publisher, and the date it was retrieved. A list of all sources is kept in one file, so every answer can be traced to a specific version of a source. To update the knowledge base, a script fetches the sources again, and I review the changes before they are used. I will make the final selection of pages and check them against my own experience.

## Success Criteria

These criteria can be tested during the course. They are checked against a fixed test set of 20–30 questions written in Thai, each with an English translation, the expected key facts, the expected source, and whether the chatbot should answer or refer the user onward:

- The chatbot answers correctly with the correct source on at least 90% of the general questions in the test set.
- Every answer to a general question includes at least one source reference.
- Questions that require an individual assessment (personal eligibility, chances of approval, special cases) are always referred to a human adviser or the relevant authority.
- When the knowledge base does not contain the answer, the chatbot says so and refers the user onward instead of guessing.
- The chatbot answers in Thai, also when the question contains typos or mixes Thai and English.
- The feedback question is shown after an answer, and the user's answer is stored.

The test set will be run again every time the prompts or sources change.

The following criteria measure the long-term effect and require real users over time, so they will be followed up after the course:

At the end of each conversation, the chatbot will ask, “Did you receive all the information you needed?” Users who answer “Yes” will indicate that the chatbot has met their information needs. We will measure this by tracking the percentage of “Yes” responses among users who answer the question.

Another success criterion is a reduced workload for the visa adviser. We will compare the number of common questions answered manually and the time spent answering them before and after introducing the chatbot. Success means users receive the information they need while the adviser spends less time answering repeated questions.

## Scope

The first version will answer general questions in Thai about short-stay tourist and visitor visas for Norway, including basic application steps, common document requirements, and visa terminology.

Because visa types and individual circumstances vary, this version will not assess personal eligibility, provide advice tailored to individual cases, or predict application outcomes. Questions requiring an individual assessment will be referred to a human adviser or the relevant authority.

**The first version consists of:**

- A mobile-friendly chat page in Thai, with example questions and source links under each answer.
- The knowledge base of 10–20 official sources described above.
- Referral to a human adviser or the relevant authority when a question needs an individual assessment or the answer is not in the sources.
- The feedback question "Did you receive all the information you needed?" with Yes/No buttons.
- A document checklist: the user selects the purpose of the visit (tourism, or visiting family or friends) and gets a list of documents to prepare.
- An English translation button and a demo mode, so the app can be tested without a Thai reader or an API key.

**Not part of the first version:** user accounts, payment, personalised advice, other visa types, and an admin page for editing sources.

## Technology, Cost and Running the App

- **Stack:** Python with FastAPI, a simple HTML/JavaScript chat page, and SQLite for storing feedback.
- **Language model:** Claude Opus 5.5 from Anthropic, which handles Thai well. The model is set in a configuration file and can be changed without code changes.
- **How answers are built:** The whole knowledge base is sent to the model with each question, using prompt caching so the sources are not paid for in full every time, and Claude's Citations feature so each answer quotes the source text it is based on. The knowledge base is small enough that a separate search database is not needed.
- **Cost:** Opus 5.5 costs $4 per million input tokens and $20 per million output tokens; cached sources cost less. The cost per question will be measured during development and reported in the README.
- **Running without our key:** The README explains how to run the app with your own API key (`.env.example`). A demo mode returns stored answers to the example questions, so the app can be run and tested without any key. Automated tests always use the demo mode.
- **Following the Thai answers:** The README lists the example questions with English and Norwegian translations, and the chat page has a "Show English translation" button.

## Privacy

Users may be tempted to write personal details such as passport numbers, family situations, or finances. The chat page will show a clear notice asking users not to share personal information. The app does not store the conversation text; it only stores the answer to the feedback question and the time it was given. Questions are sent to the language model provider to generate answers, and this will be stated on the page. No real applicant enquiries will be stored in the repository.

## Vision

If the first version is successful, the chatbot will gradually expand over the next two to three years to cover more visa types and provide guidance that is more relevant to each user’s circumstances.

Users will be able to create an account and pay for access to personalised answers based on the information they provide. Complex cases will still require support from a human adviser. The long-term goal is to make visa information easier to access while building a sustainable service that reduces the adviser’s workload.
