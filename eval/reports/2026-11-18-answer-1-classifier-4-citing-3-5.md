# Evaluation report 2026-11-18

- Date: 2026-11-18
- Provider: ollama
- Answer model: `qwen3.5:9b`
- Classify model: `qwen3.5:9b`
- Prompt versions: answer 1, classifier 4, citing 3
- Knowledge base: 15 sources, newest retrieved 2026-11-13
- Cases: 29
- Tokens: input 498437, output 31370, cache read 0, cache write 0
- Total cost: 0.000000 USD

Answers vary between runs, so this report is judged on its own. Write `yes` or `no` after
each case's `Adviser:` line (a comment may follow, e.g. `Adviser: no - the fee is missing`),
then run `uv run python scripts/run_eval.py --score <this file>`.

<!-- totals:start -->
## Totals

| Target | Goal | Result | Met |
|---|---|---|---|
| General questions correct, with the correct source | ≥ 90% | awaiting adviser: 11 of 14 pass the automatic checks, 0 judged correct, 11 not judged yet | awaiting adviser |
| Individual assessment gets "the embassy decides" | 100% | 3 of 3 (100%) | yes |
| Not covered by the sources gets the no-answer message | 100% | 3 of 4 (75%) | no |
| Request for a person gets the adviser contact | 100% | 4 of 4 (100%) | yes |

A case counts when its category, outcome and source checks pass; a general question also needs
the adviser's `yes`.

- Reply in Thai: 29 of 29
- Personal information handled as expected: 29 of 29
- Cases that dropped unknown source ids: 4 of 29
- Adviser judgements filled in: 0 of 29
<!-- totals:end -->

## Cases

### 1. `application-steps`

<!-- eval-case {"id": "application-steps", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: อยากไปเยี่ยมเพื่อนที่นอร์เวย์ ต้องทำอะไรบ้างตั้งแต่ต้นจนได้วีซ่าคะ
- English: I want to visit a friend in Norway. What do I have to do, from the start until I get the visa?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-visitor-visa-checklist`, `embassy-online-registration`, `udi-how-to-apply-visitor-visa`, `embassy-visa-faq`, `udi-invitation-for-visitor-visa`, `udi-sponsor-for-visitors`, `embassy-processing-time`, `udi-waiting-time-visitor-visa` (expected: `udi-how-to-apply-visitor-visa`, `embassy-visa-faq`, `embassy-online-registration`)
- Dropped unknown source ids: 1

**Reply:**

> # กระบวนการขอวีซ่าผู้เยี่ยมเยียนเพื่อไปพบเพื่อนในนอร์เวย์
>
> ## ขั้นตอนการสมัคร
>
> 1. **เตรียมเอกสารทั้งหมด** ตามรายการเอกสารบนเว็บไซต์ของ Royal Norwegian Embassy in Bangkok (norway.no)
>    - ใบสมัครแบบพิมพ์แล้วจาก UDI (schengen.pdf)
>    - พาสปอร์ตที่มีอายุเหลืออีกอย่างน้อย 3 เดือนหลังออกจากพื้นที่ชงเกน
>    - รูปถ่ายตามมาตรฐานสากล
>    - หลักประกันการเงินและที่อยู่ระหว่างเดินทาง
>    - ประกันภัยการเดินทางครอบคลุมยุโรปเหนือ
>
> 2. **ลงทะเบียนออนไลน์** ที่เว็บไซต์ UDI (udi.no)
>    - กรอกแบบฟอร์มออนไลน์บนเว็บ UDI
>    - รับรหัสยืนยันหลังจากกรอกเสร็จ
>
> 3. **ชำระค่าธรรมเนียมวีซ่าออนไลน์**
>    - ค่าธรรมเนียมผู้ใหญ่ 90 ยูโร (เด็กอายุต่ำกว่า 6 ปีไม่เสีย)
>    - ชำระก่อนจองนัดหมาย
>
> 4. **จองนัดหมายที่ VFS Global** และนำเอกสารไปยื่น [(vfsglobal.com)](https://visa.vfsglobal.com/tha/en/nor/)
>    - สถานที่: The Shoppes at Belle Grand Rama 9, Bangkok
>
> ## เอกสารที่ต้องเตรียมเพิ่มเติม
>
> - **จดหมายเชิญจากเพื่อนในนอร์เวย์**
> - **แบบฟอร์มการรับรองจากเพื่อน (sponsorship form)** หากไม่มีเงินพอ
> - หลักฐานการเงินและที่อยู่ระหว่างเดินทาง
>
> ## เวลาที่รอผล
>
> ปกติจะได้ผลภายใน 15 วันหลังจากยื่นเอกสาร
>
> แนะนำให้ยื่นล่วงหน้าอย่างน้อย 4 สัปดาห์ และไม่เกิน 6 เดือนก่อนเดินทาง

**Expected facts:**

- Register the application online on the UDI website and pay the application fee online
- Print the Schengen.pdf application form received by email; the applicant signs it
- Book an appointment at VFS Global and hand in the application and the documents there in person

Adviser: 

### 2. `basic-documents-checklist`

<!-- eval-case {"id": "basic-documents-checklist", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: เอกสารพื้นฐานที่ทุกคนต้องเตรียมตามเช็คลิสต์ของสถานทูตมีอะไรบ้างคะ
- English: Which basic documents does everyone have to prepare according to the embassy's checklist?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-visitor-visa-checklist`, `embassy-necessary-documents` (expected: `embassy-visitor-visa-checklist`, `embassy-hand-in-documents`)

**Reply:**

> 1. หนังสือเดินทางฉบับจริง ที่มีอายุอีกอย่างน้อย 3 เดือนหลังกลับและมีหน้าว่างไม่ต่ำกว่า 2 หน้า
> 2. รูปถ่ายสี พื้นขาว ไม่ตัดต่อ อายุไม่เกิน 6 เดือน แสดงหน้าเต็มและบ่าบน
> 3. แบบฟอร์มการสมัคร (Schengen.pdf) ที่พิมพ์จากอีเมล UDI และเซ็นชื่อด้วยตนเอง
> 4. ประกันสุขภาพเดินทาง ครอบคลุมพื้นที่ Schengen ทั้งสิ้นและค่ารักษาอย่างน้อย 30,000 ยูโร
> 5. รายการเช็คลิสต์เอกสาร และเอกสารอื่น ๆ ตามที่ระบุในรายการ
>
> ขออภัย ข้อมูลเพิ่มเติมเกี่ยวกับเอกสารเฉพาะกรณี (เช่น การเดินทางเพื่อเยี่ยมครอบครัว) โปรดดูเช็คลิสต์แยกต่างหาก

**Expected facts:**

- A passport valid for at least three months after the trip, with at least two blank pages
- A signed printout of the application form from the UDI application portal
- Travel medical insurance for the whole trip and the whole Schengen area, covering at least EUR 30,000

Adviser: 

### 3. `sponsor-how-to-fill-in`

<!-- eval-case {"id": "sponsor-how-to-fill-in", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: แฟนที่อยู่นอร์เวย์จะออกค่าใช้จ่ายให้ เขาต้องกรอกแบบฟอร์มสปอนเซอร์ยังไงคะ
- English: My partner in Norway will pay for the trip. How does he fill in the sponsorship form?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `udi-sponsor-for-visitors`, `udi-sponsorship-form` (expected: `udi-sponsor-for-visitors`)

**Reply:**

> การกรอกแบบฟอร์มสปอนเซอร์สำหรับคู่รักหรือครอบครัวในนอร์เวย์ มีขั้นตอนดังนี้ค่ะ
>
> 1. **แบบฟอร์มอิเล็กทรอนิกส์**: คุณพาร์ทเนอร์สามารถกรอกแบบฟอร์มออนไลน์และส่งรหัสคำ 4 คำให้คุณเมื่อสมัครขอวีซ่าครั้งแรกได้ เมื่อเดินทางเข้าประเทศต้องนำกระดาษที่พิมพ์จากโค้ดนี้ไปแสดงด้วย
> 2. **แบบฟอร์มกระดาษ**: สามารถกรอกและลงนามด้วยลายมือของคุณพาร์ทเนอร์ แล้วส่งทางอีเมลหรือไปรษณีย์มาให้คุณ นำแบบฟอร์มมาแสดงเมื่อเดินทางเข้านอร์เวย์ได้
>
> เงื่อนไขผู้เป็นสปอนเซอร์ต้องอาศัยอยู่ในนอร์เวย์, มีเลขประจำตัวประชาชนนอร์เวย์ (*fødselsnummer*), และอายุอย่างน้อย 18 ปี
> แบบฟอร์มมีอายุใช้ได้ 6 เดือนหลังจากกรอกและลงนามแล้ว และใช้ได้ต่อครั้งละ 1 ครั้งเท่านั้น หากขอวีซ่าหลายครั้งต้องกรอกใหม่ทุกครั้ง

**Expected facts:**

- The sponsor fills in an electronic sponsorship form; a paper form is the alternative
- The sponsor sends the four-word sponsor code to the applicant, who gives it in the visa application
- The sponsor must live in Norway, have a Norwegian national identity number and be at least 18

Adviser: 

### 4. `sponsorship-form-validity`

<!-- eval-case {"id": "sponsorship-form-validity", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: sponsorship form ที่ sponsor กรอกให้แล้ว ใช้ได้กี่ครั้ง แล้วมีอายุกี่เดือนคะ
- English: The sponsorship form my sponsor filled in - how many times can it be used, and for how many months is it valid?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `udi-sponsorship-form`, `udi-sponsor-for-visitors` (expected: `udi-sponsor-for-visitors`, `udi-sponsorship-form`)
- Dropped unknown source ids: 1

**Reply:**

> **แบบฟอร์มสปอนเซอร์ใช้ได้เพียง 1 ครั้งต่อการเข้าแต่ละครั้งเท่านั้น และอายุการมีไว้ใช้ 6 เดือนนับจากวันที่กรอกเสร็จและลงนาม**
>
> หากได้รับวีซ้ามultiple-entry (เข้าออกได้หลายครั้ง) จะต้องขอแบบฟอร์มใหม่ทุกครั้งที่จะเดินทางเข้ามา

**Expected facts:**

- A sponsorship form is valid for one entry (one trip) into the Schengen area
- A sponsorship form is valid for 6 months after it was filled in and signed

Adviser: 

### 5. `invitation-letter-content`

<!-- eval-case {"id": "invitation-letter-content", "target": "general", "checks": {"category": true, "outcome": false, "source": false, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: เพื่อนคนนอร์เวย์จะเขียนจดหมายเชิญให้ ในจดหมายต้องมีข้อมูลอะไรบ้างคะ
- English: My Norwegian friend will write an invitation letter for me. What information must the letter contain?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `no_answer`
- Checks: category pass, outcome FAIL, expected source FAIL, personal information pass, Thai pass
- Cited sources: none (expected: `udi-invitation-for-visitor-visa`)
- Dropped unknown source ids: 1
- No-answer reason: only unknown source ids cited

**Reply:**

> ขออภัย ไม่พบคำตอบสำหรับคำถามนี้ในแหล่งข้อมูลทางการที่เรามี กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com

**Expected facts:**

- Why the applicant is invited
- The proposed dates of the visit
- Information about the person who invites, such as their work and home
- The relationship between the applicant and the person who invites

Adviser: 

### 6. `relationship-proof-unmarried-partner`

<!-- eval-case {"id": "relationship-proof-unmarried-partner", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ไปเยี่ยมแฟนหนุ่มที่นอร์เวย์ แต่ยังไม่ได้แต่งงานกัน ต้องใช้อะไรพิสูจน์ว่าเป็นแฟนกันจริงคะ
- English: I am visiting my boyfriend in Norway, but we are not married. What do I use to prove that we really are a couple?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-visitor-visa-checklist`, `embassy-necessary-documents` (expected: `embassy-visitor-visa-checklist`)

**Reply:**

> สำหรับกรณีไปเยี่ยมแฟนชายที่ยังไม่ได้แต่งงาน เอกสารที่ใช้พิสูจน์ความสัมพันธ์คือ:
>
> 1. ใบรับรองความสัมพันธ์แบบไม่ใช่ความสัมพันธ์ทางกฎหมาย เช่น หลักฐานการสื่อสารระหว่างกัน (เช่น อีเมล แชต รูปภาพด้วยกัน)
> 2. สำเนาหน้าข้อมูลสำคัญจากหนังสือเดินทางของแฟน พร้อมประวัติการเดินทาง
>
> หมายเหตุ: เอกสารเหล่านี้ต้องยื่นพร้อมกับการสมัครวีซ่านะคะ หากเอกสารไม่ครบอาจทำให้การพิจารณาดำเนินได้ช้าลง
>
> ขออภัย ไม่มีข้อมูลเพิ่มเติมว่าต้องใช้เอกสารเฉพาะอื่น ๆ เพิ่มเติมค่ะ

**Expected facts:**

- A copy of the bio data page of the sponsor's passport and the sponsor's travel history
- Proof of correspondence between the applicant and the boyfriend

Adviser: 

### 7. `fee-where-to-pay-typo`

<!-- eval-case {"id": "fee-where-to-pay-typo", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ค่าธรรมเนียมวีซ่าจ่ายทีไหนคะ แล้วต้องจ่ายค่าบริการที่ VFS เพิ่มอีกมัย
- English: Where do I pay the visa fee? And do I also have to pay a service fee at VFS?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-online-registration`, `udi-fees`, `embassy-hand-in-documents` (expected: `embassy-online-registration`, `udi-fees`)

**Reply:**

> ค่าธรรมเนียมวีซ่าจ่ายตอนลงทะเบียนออนไลน์ผ่านเว็บไซต์ UDI ก่อนค่ะ ส่วนค่าบริการที่ VFS Global มีเพิ่มอีกตอนยื่นเอกสารด้วยค่ะ

**Expected facts:**

- The visa fee is paid online when the application is registered in the application portal
- VFS Global charges its own service fee, paid directly to VFS when the application is handed in

Adviser: 

### 8. `processing-time-typo`

<!-- eval-case {"id": "processing-time-typo", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ยืนวีซ่าแล้วต้องรอผลกี่วันค่ะ
- English: After I hand in the visa application, how many days do I have to wait for the result?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-processing-time`, `udi-waiting-time-visitor-visa` (expected: `embassy-processing-time`, `udi-waiting-time-visitor-visa`, `embassy-visa-faq`)

**Reply:**

> โดยปกติจะใช้เวลาประมาณ 15 วันหลังจากสถานทูตได้รับเอกสารครบถ้วนแล้ว
> ในบางกรณีอาจส่งต่อให้กรมตรวจคนเข้าเมือง (UDI) ซึ่งอาจใช้เวลาสูงสุด 45 วัน
> ไม่สามารถระบุวันที่แน่นอนได้ค่ะ

**Expected facts:**

- The processing time is normally up to 15 calendar days
- It can take up to 45 days when the application is sent to UDI or needs further examination

Adviser: 

### 9. `when-to-apply-mixed-language`

<!-- eval-case {"id": "when-to-apply-mixed-language", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ควร apply visa ล่วงหน้ากี่ week ก่อน travel คะ แล้ว apply เร็วสุดได้กี่เดือน
- English: How many weeks before travelling should I apply for the visa, and how many months before at the earliest?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-visa-faq`, `embassy-processing-time`, `udi-waiting-time-visitor-visa` (expected: `embassy-processing-time`, `embassy-visa-faq`, `udi-visit-family-how-to-apply`)

**Reply:**

> ## ขอแนะนำระยะเวลาในการยื่นขอวีซ่า
>
> 1. **ควรยื่นล่วงหน้าอย่างน้อย 4 สัปดาห์ (หนึ่งเดือน)** ก่อนวันเดินทาง
>
> 2. **ยื่นได้เร็วสุด 6 เดือน** จากวันที่วางแผนจะเดินทาง
>
> *(หมายเหตุ: สำหรับลูกเรือเรือทะเล สามารถยื่นล่วงหน้าได้สูงสุด 9 เดือน)*

**Expected facts:**

- Applying at least 4 weeks before departure is recommended
- The application can be handed in no earlier than 6 months before the trip

Adviser: 

### 10. `follow-up-young-child-fee`

<!-- eval-case {"id": "follow-up-young-child-fee", "target": "general", "checks": {"category": true, "outcome": false, "source": false, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: แล้วลูกชายอายุ 4 ขวบต้องจ่ายค่าธรรมเนียมด้วยไหมคะ
- English: And does my 4-year-old son also have to pay the fee?
- Earlier question 1: ขั้นตอนยื่นวีซ่าเยี่ยมครอบครัวที่นอร์เวย์มีอะไรบ้างคะ
- Earlier answer 1: มีสองส่วนค่ะ ส่วนแรก ลงทะเบียนคำร้องออนไลน์ที่เว็บไซต์ของ UDI และชำระค่าธรรมเนียม ส่วนที่สอง นัดหมายและไปยื่นคำร้องพร้อมเอกสารด้วยตนเองที่ศูนย์ VFS Global
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `no_answer`
- Checks: category pass, outcome FAIL, expected source FAIL, personal information pass, Thai pass
- Cited sources: none (expected: `udi-fees`, `embassy-online-registration`)
- No-answer reason: no source cited

**Reply:**

> ขออภัย ไม่พบคำตอบสำหรับคำถามนี้ในแหล่งข้อมูลทางการที่เรามี กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com

**Expected facts:**

- Children under six years do not pay a visa fee

Adviser: 

### 11. `thai-id-hand-in-in-person`

<!-- eval-case {"id": "thai-id-hand-in-in-person", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: เลขบัตรประชาชนของฉันคือ 1234567890123 ค่ะ ต้องไปยื่นเอกสารที่ VFS ด้วยตัวเองไหม ให้น้องสาวไปแทนได้หรือเปล่า
- English: (Gives a Thai ID number.) Do I have to hand in the documents at VFS in person, or can my younger sister go instead?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-visa-faq` (expected: `embassy-visa-faq`)

**Reply:**

> 1. ส่วนใหญ่ท่านต้องไปยื่นแบบคำร้องและเอกสารที่ศูนย์ VFS Global ด้วยตัวเองค่ะ
> 2. แต่มีข้อยกเว้น: ถ้าเคยยื่นขอวีเชงเกนก่อนแล้วไม่เกิน 5 ปี (59 เดือน) และข้อมูลทางชีวภาพของท่านยังใช้ได้ ไม่ต้องมาด้วยตัวท่านเอง ผู้แทนสามารถยื่นเอกสารให้ท่านได้ โดยต้องมีหนังสือมอบอำนาจลายมือชื่อจากท่าน
> 3. หากไม่มีข้อยกเว้นข้างต้น คนอื่นเช่นน้องสาวไม่สามารถยื่นแทนท่านได้ค่ะ ต้องไปยื่นแบบคำร้องและชำระค่าภาษีออนไลน์ก่อน แล้วค่อยนัดหมายมาส่งเอกสารที่ VFS Global ค่ะ

**Expected facts:**

- In most cases the applicant must hand in the application in person at VFS
- A representative with a signed power of attorney may hand it in only if the applicant applied for a Schengen visa within the last five years (59 months) and the biometric data is still valid

Adviser: 

### 12. `passport-validity`

<!-- eval-case {"id": "passport-validity", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: พาสปอร์ตเลข AA1234567 จะหมดอายุอีก 2 เดือน ต้องทำเล่มใหม่ก่อนยื่นวีซ่าไหมคะ
- English: (Gives a passport number.) My passport expires in 2 months. Do I need a new one before I apply for the visa?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-necessary-documents` (expected: `embassy-visitor-visa-checklist`, `embassy-hand-in-documents`, `eu-applying-for-schengen-visa`)

**Reply:**

> ขออภัย ไม่มีข้อมูลเรื่องเวลาหมดอายุเป๊ะๆ ค่ะ แต่ตามเอกสาร ต้องมีพาสปอร์ตที่ถูกต้องอย่างน้อย 3 เดือนหลังจากวันที่จะออกจากเขตเชงเกน
>
> ดังนั้น ถ้าพาสปอร์ตหมดอายุในอีก 2 เดือน ไม่ครบเกณฑ์ 3 เดือนหลังจากเดินทาง คุณควรทำเล่มใหม่ก่อนยื่นวีซ่าค่ะ

**Expected facts:**

- The passport must be valid for at least three months after the planned departure from the Schengen area
- The passport must have at least two blank pages

Adviser: 

### 13. `thanks-and-insurance-question`

<!-- eval-case {"id": "thanks-and-insurance-question", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ได้ค่ะ ขอบใจมาก อีกเรื่องนะคะ ประกันการเดินทางต้องมีวงเงินคุ้มครองขั้นต่ำเท่าไร
- English: All right, many thanks. One more thing - what is the minimum cover the travel insurance must have?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-necessary-documents`, `embassy-visitor-visa-checklist` (expected: `embassy-necessary-documents`, `embassy-hand-in-documents`, `embassy-visitor-visa-checklist`)

**Reply:**

> ประกันการเดินทางต้องมีวงเงินคุ้มครองขั้นต่ำ 30,000 ยูโร
>
> ประกันต้องครอบคลุมทั้งระยะเวลาการมาเที่ยวทั้งหมด และครอบคลุมทุกประเทศในเขตเชงเก้น รวมถึงค่าส่งตัวกลับกรณีฉุกเฉินด้วย

**Expected facts:**

- The travel medical insurance must cover at least EUR 30,000
- It must be valid in all Schengen countries for the whole stay

Adviser: 

### 14. `own-chances-and-employment-proof`

<!-- eval-case {"id": "own-chances-and-employment-proof", "target": "general", "checks": {"category": true, "outcome": true, "source": false, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: เพิ่งเปลี่ยนงานมาได้สองเดือน สถานทูตจะอนุมัติให้ฉันหรือเปล่า และต้องใช้หลักฐานการทำงานแบบไหนคะ
- English: I changed jobs only two months ago. Will the embassy approve me, and what kind of proof of employment do I need?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source FAIL, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents` (expected: `embassy-visitor-visa-checklist`)
- Dropped unknown source ids: 1

**Reply:**

> คุณต้องเตรียมเอกสารเพื่อพิสูจน์การจ้างงาน ได้แก่ ใบรับรองบริษัทและหนังสือยืนยันการจ้างงานที่ระบุตำแหน่ง เงินเดือน และวันหยุดพักผ่อน รวมถึงรายการบัญชีธนาคาร 3 เดือนล่าสุด การพิจารณาว่าจะอนุมัติหรือไม่ขึ้นอยู่กับดุลยพินิจของสถานทูต ซึ่งประมวลผลแต่ละกรณีตามขั้นตอน

**Expected facts:**

- An employed applicant hands in a company registration and a statement of employment
- The statement of employment shows the vacation days granted, the position and the monthly salary

Adviser: 

### 15. `no-answer-document-translation`

<!-- eval-case {"id": "no-answer-document-translation", "target": "no_answer", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: สูติบัตรกับทะเบียนบ้านเป็นภาษาไทย ต้องแปลเป็นภาษาอังกฤษก่อนยื่นไหมคะ
- English: My birth certificate and house registration are in Thai. Do they have to be translated into English before I hand them in?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `no_answer`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)
- No-answer reason: no source cited

**Reply:**

> ขออภัย ไม่พบคำตอบสำหรับคำถามนี้ในแหล่งข้อมูลทางการที่เรามี กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com

**Expected facts:**

- none

Adviser: 

### 16. `no-answer-pregnancy`

<!-- eval-case {"id": "no-answer-pregnancy", "target": "no_answer", "checks": {"category": true, "outcome": false, "source": false, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ตอนนี้ตั้งท้องได้หกเดือน ยังยื่นขอวีซ่าท่องเที่ยวนอร์เวย์ได้ไหม มีเงื่อนไขพิเศษสำหรับคนท้องหรือเปล่าคะ
- English: I am six months pregnant. Can I still apply for a Norway tourist visa, and are there special conditions for pregnant women?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `answered`
- Checks: category pass, outcome FAIL, expected source FAIL, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents` (expected: none)

**Reply:**

> ทุกผู้ยื่นต้องปฏิบัติตามข้อกำหนดทั่วไป เช่น มีหนังสือเดินทางอายุใช้งานสามเดือนหลังจากเดินทางออกและประกันสุขภาพครอบคลุมค่ารักษาฉุกเฉินอย่างน้อย 30,000 ยูโร แต่ไม่พบข้อมูลเงื่อนไขพิเศษสำหรับหญิงตั้งครรภ์ค่ะ

**Expected facts:**

- none

Adviser: 

### 17. `no-answer-vaccination-certificate`

<!-- eval-case {"id": "no-answer-vaccination-certificate", "target": "no_answer", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ต้องมีใบรับรองการฉีดวัคซีนไปยื่นพร้อมเอกสารวีซ่าด้วยไหมคะ
- English: Do I need to hand in a vaccination certificate with my visa documents?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `no_answer`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)
- No-answer reason: opened with the not-available sentence

**Reply:**

> ขออภัย ไม่พบคำตอบสำหรับคำถามนี้ในแหล่งข้อมูลทางการที่เรามี กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com

**Expected facts:**

- none

Adviser: 

### 18. `no-answer-interpreter-at-vfs`

<!-- eval-case {"id": "no-answer-interpreter-at-vfs", "target": "no_answer", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ฉันพูดภาษาอังกฤษไม่ได้ พาล่ามไปด้วยตอนยื่นเอกสารที่ VFS ได้ไหมคะ
- English: I can't speak English. Can I bring an interpreter when I hand in my documents at VFS?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `no_answer`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)
- No-answer reason: no source cited

**Reply:**

> ขออภัย ไม่พบคำตอบสำหรับคำถามนี้ในแหล่งข้อมูลทางการที่เรามี กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com

**Expected facts:**

- none

Adviser: 

### 19. `own-chances-salary`

<!-- eval-case {"id": "own-chances-salary", "target": "individual_assessment", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ฉันทำงานร้านนวด เงินเดือนหนึ่งหมื่นห้าพันบาท ยื่นไปแล้วจะโดนปฏิเสธไหมคะ
- English: I work at a massage shop and earn fifteen thousand baht a month. Will my application be refused?
- Category: expected `individual_assessment`, actual `individual_assessment`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> ขออภัย เราไม่สามารถประเมินได้ว่าคุณจะได้รับวีซ่าหรือไม่ สถานทูตนอร์เวย์เป็นผู้พิจารณาและตัดสินคำร้องแต่ละคำร้อง และไม่มีใครอื่นที่ตอบคำถามนี้ได้ หากมีคำถามทั่วไปเกี่ยวกับเอกสารหรือขั้นตอนการยื่นขอวีซ่า ถามได้เลย

**Expected facts:**

- none

Adviser: 

### 20. `own-chances-earlier-overstay`

<!-- eval-case {"id": "own-chances-earlier-overstay", "target": "individual_assessment", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: เมื่อห้าปีก่อนเคยอยู่เกินวีซ่าที่ญี่ปุ่น เลขบัตรประชาชน 3-1012-34567-89-5 ช่วยดูหน่อยว่าสถานทูตนอร์เวย์จะให้วีซ่าฉันไหม
- English: Five years ago I overstayed a visa in Japan. (Gives a Thai ID number.) Please check whether the Norwegian embassy will give me a visa.
- Category: expected `individual_assessment`, actual `individual_assessment`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> ขออภัย เราไม่สามารถประเมินได้ว่าคุณจะได้รับวีซ่าหรือไม่ สถานทูตนอร์เวย์เป็นผู้พิจารณาและตัดสินคำร้องแต่ละคำร้อง และไม่มีใครอื่นที่ตอบคำถามนี้ได้ หากมีคำถามทั่วไปเกี่ยวกับเอกสารหรือขั้นตอนการยื่นขอวีซ่า ถามได้เลย

**Expected facts:**

- none

Adviser: 

### 21. `follow-up-own-chances`

<!-- eval-case {"id": "follow-up-own-chances", "target": "individual_assessment", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ถ้าเตรียมครบตามนี้ทุกอย่าง รับรองว่าได้วีซ่าแน่ใช่ไหมคะ
- English: If I prepare everything on this list, is it guaranteed that I get the visa?
- Earlier question 1: ไปเยี่ยมพี่สาวที่นอร์เวย์ต้องใช้เอกสารอะไรบ้างคะ
- Earlier answer 1: นอกจากเอกสารทั่วไปตามเช็คลิสต์ของสถานทูต เช่น หนังสือเดินทางและประกันการเดินทาง ต้องมีหลักฐานความสัมพันธ์ เช่น สูติบัตรหรือทะเบียนบ้าน และถ้าพี่สาวออกค่าใช้จ่ายให้ ต้องมีแบบฟอร์มสปอนเซอร์ด้วยค่ะ
- Category: expected `individual_assessment`, actual `individual_assessment`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> ขออภัย เราไม่สามารถประเมินได้ว่าคุณจะได้รับวีซ่าหรือไม่ สถานทูตนอร์เวย์เป็นผู้พิจารณาและตัดสินคำร้องแต่ละคำร้อง และไม่มีใครอื่นที่ตอบคำถามนี้ได้ หากมีคำถามทั่วไปเกี่ยวกับเอกสารหรือขั้นตอนการยื่นขอวีซ่า ถามได้เลย

**Expected facts:**

- none

Adviser: 

### 22. `out-of-scope-berry-picking-sweden`

<!-- eval-case {"id": "out-of-scope-berry-picking-sweden", "target": null, "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: อยากไปทำงานเก็บเบอร์รี่ที่สวีเดน ต้องขอวีซ่าประเภทไหนคะ
- English: I want to go to Sweden to work picking berries. Which type of visa do I need?
- Category: expected `out_of_scope`, actual `out_of_scope`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> ขออภัย แชทบอทนี้ตอบได้เฉพาะเรื่องวีซ่าท่องเที่ยวและวีซ่าเยี่ยมเยียนระยะสั้นสำหรับเดินทางไปนอร์เวย์เท่านั้น หากมีคำถามเรื่องอื่น กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com หากมีคำถามเกี่ยวกับวีซ่าระยะสั้นไปนอร์เวย์ ถามได้เลย

**Expected facts:**

- none

Adviser: 

### 23. `out-of-scope-move-to-husband`

<!-- eval-case {"id": "out-of-scope-move-to-husband", "target": null, "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: แต่งงานกับสามีชาวนอร์เวย์แล้ว อยากย้ายไปอยู่กับเขาถาวร ต้องขอใบอนุญาตอะไรคะ
- English: I am married to a Norwegian man and want to move to live with him permanently. Which permit do I need?
- Category: expected `out_of_scope`, actual `out_of_scope`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> ขออภัย แชทบอทนี้ตอบได้เฉพาะเรื่องวีซ่าท่องเที่ยวและวีซ่าเยี่ยมเยียนระยะสั้นสำหรับเดินทางไปนอร์เวย์เท่านั้น หากมีคำถามเรื่องอื่น กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com หากมีคำถามเกี่ยวกับวีซ่าระยะสั้นไปนอร์เวย์ ถามได้เลย

**Expected facts:**

- none

Adviser: 

### 24. `follow-up-study-permit`

<!-- eval-case {"id": "follow-up-study-permit", "target": null, "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ถ้าจะไปเรียนปริญญาโทที่ออสโลสองปี ต้องยื่นขออนุญาตแบบไหนคะ
- English: If I go to Oslo for a two-year master's degree, which kind of permit do I apply for?
- Earlier question 1: ไปเที่ยวนอร์เวย์สองอาทิตย์ ต้องเตรียมหลักฐานอะไรไปยื่นบ้างคะ
- Earlier answer 1: นอกจากหนังสือเดินทางและประกันการเดินทาง ต้องมีหลักฐานที่พักตลอดการเดินทาง ตั๋วเครื่องบินไปกลับ และรายการเดินบัญชีธนาคารย้อนหลังสามเดือนค่ะ
- Category: expected `out_of_scope`, actual `out_of_scope`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> ขออภัย แชทบอทนี้ตอบได้เฉพาะเรื่องวีซ่าท่องเที่ยวและวีซ่าเยี่ยมเยียนระยะสั้นสำหรับเดินทางไปนอร์เวย์เท่านั้น หากมีคำถามเรื่องอื่น กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com หากมีคำถามเกี่ยวกับวีซ่าระยะสั้นไปนอร์เวย์ ถามได้เลย

**Expected facts:**

- none

Adviser: 

### 25. `reach-person-call-back`

<!-- eval-case {"id": "reach-person-call-back", "target": "reach_person", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: รบกวนให้เจ้าหน้าที่โทรกลับที่เบอร์ 081-234-5678 หน่อยค่ะ อยากปรึกษาเรื่องวีซ่า
- English: (Gives a phone number.) Could a staff member please call me back? I would like advice about the visa.
- Category: expected `reach_person`, actual `reach_person`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> คุณสามารถติดต่อที่ปรึกษาได้โดยตรงที่ ngan.visaa@gmail.com ที่ปรึกษาจะช่วยตอบคำถามและให้คำแนะนำเกี่ยวกับการยื่นขอวีซ่าของคุณ คุณยังถามคำถามทั่วไปเกี่ยวกับวีซ่าที่นี่ได้เช่นกัน

**Expected facts:**

- none

Adviser: 

### 26. `reach-person-not-a-bot`

<!-- eval-case {"id": "reach-person-not-a-bot", "target": "reach_person", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: เบื่อแชทกับบอทแล้วค่ะ มีพนักงานตัวจริงให้ปรึกษาไหม
- English: I am tired of chatting with a bot. Is there a real staff member I can consult?
- Category: expected `reach_person`, actual `reach_person`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> คุณสามารถติดต่อที่ปรึกษาได้โดยตรงที่ ngan.visaa@gmail.com ที่ปรึกษาจะช่วยตอบคำถามและให้คำแนะนำเกี่ยวกับการยื่นขอวีซ่าของคุณ คุณยังถามคำถามทั่วไปเกี่ยวกับวีซ่าที่นี่ได้เช่นกัน

**Expected facts:**

- none

Adviser: 

### 27. `reach-person-whole-process`

<!-- eval-case {"id": "reach-person-whole-process", "target": "reach_person", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: อ่านแล้วงงไปหมด อยากได้คนมาจัดการเอกสารและนัด VFS แทนฉันทุกขั้นตอนค่ะ
- English: Reading this confuses me completely. I want someone to handle the documents and the VFS appointment for me, every step of the way.
- Category: expected `reach_person`, actual `reach_person`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> คุณสามารถติดต่อที่ปรึกษาได้โดยตรงที่ ngan.visaa@gmail.com ที่ปรึกษาจะช่วยตอบคำถามและให้คำแนะนำเกี่ยวกับการยื่นขอวีซ่าของคุณ คุณยังถามคำถามทั่วไปเกี่ยวกับวีซ่าที่นี่ได้เช่นกัน

**Expected facts:**

- none

Adviser: 

### 28. `reach-person-adviser-email-mixed-language`

<!-- eval-case {"id": "reach-person-adviser-email-mixed-language", "target": "reach_person", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ขอ email ของ adviser ตัวจริงหน่อยค่ะ จะส่งคำถามไปถามเอง
- English: Please give me the email address of a real adviser; I will send my questions myself.
- Category: expected `reach_person`, actual `reach_person`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> คุณสามารถติดต่อที่ปรึกษาได้โดยตรงที่ ngan.visaa@gmail.com ที่ปรึกษาจะช่วยตอบคำถามและให้คำแนะนำเกี่ยวกับการยื่นขอวีซ่าของคุณ คุณยังถามคำถามทั่วไปเกี่ยวกับวีซ่าที่นี่ได้เช่นกัน

**Expected facts:**

- none

Adviser: 

### 29. `done-thanks`

<!-- eval-case {"id": "done-thanks", "target": null, "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ชัดเจนมากเลยค่ะ ขอบคุณที่ช่วยนะคะ 😊
- English: That is very clear, thank you for helping!
- Category: expected `done`, actual `done`
- Outcome: expected `fixed_reply`, actual `fixed_reply`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> คุณได้รับข้อมูลที่ต้องการครบถ้วนแล้วหรือไม่

**Expected facts:**

- none

Adviser: 
