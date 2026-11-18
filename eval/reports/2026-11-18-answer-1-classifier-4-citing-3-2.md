# Evaluation report 2026-11-18

- Date: 2026-11-18
- Provider: ollama
- Answer model: `qwen3.5:9b`
- Classify model: `qwen3.5:9b`
- Prompt versions: answer 1, classifier 4, citing 3
- Knowledge base: 15 sources, newest retrieved 2026-11-13
- Cases: 30
- Tokens: input 500079, output 23782, cache read 0, cache write 0
- Total cost: 0.000000 USD

Answers vary between runs, so this report is judged on its own. Write `yes` or `no` after
each case's `Adviser:` line (a comment may follow, e.g. `Adviser: no - the fee is missing`),
then run `uv run python scripts/run_eval.py --score <this file>`.

<!-- totals:start -->
## Totals

| Target | Goal | Result | Met |
|---|---|---|---|
| General questions correct, with the correct source | ≥ 90% | awaiting adviser: 14 of 15 pass the automatic checks, 0 judged correct, 14 not judged yet | awaiting adviser |
| Individual assessment gets "the embassy decides" | 100% | 3 of 3 (100%) | yes |
| Not covered by the sources gets the no-answer message | 100% | 3 of 4 (75%) | no |
| Request for a person gets the adviser contact | 100% | 4 of 4 (100%) | yes |

A case counts when its category, outcome and source checks pass; a general question also needs
the adviser's `yes`.

- Reply in Thai: 30 of 30
- Personal information handled as expected: 30 of 30
- Cases that dropped unknown source ids: 2 of 30
- Adviser judgements filled in: 0 of 30
<!-- totals:end -->

## Cases

### 1. `application-steps`

<!-- eval-case {"id": "application-steps", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: อยากไปเยี่ยมเพื่อนที่นอร์เวย์ ต้องทำอะไรบ้างตั้งแต่ต้นจนได้วีซ่าคะ
- English: I want to visit a friend in Norway. What do I have to do, from the start until I get the visa?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-necessary-documents`, `embassy-online-registration`, `embassy-processing-time`, `udi-waiting-time-visitor-visa`, `udi-invitation-for-visitor-visa`, `udi-sponsor-for-visitors`, `eu-applying-for-schengen-visa`, `embassy-visa-faq` (expected: `udi-how-to-apply-visitor-visa`, `embassy-visa-faq`, `embassy-online-registration`)
- Dropped unknown source ids: 1

**Reply:**

> 1. **เตรียมเอกสาร** — ดาวน์โหลด Check List จากเว็บไซต์ Royal Norwegian Embassy ในกรุงเทพ (norway.no) แล้วเก็บเอกสารตามที่ระบุ
>
> 2. **ลงทะเบียนออนไลน์** — กรอกแบบฟอร์มสมัครวีซ่าผ่านเว็บ UDI (udi.no) และจ่ายค่าวีซ่าด้วยบัตร Visa/Mastercard/Apple Pay/Google Pay
>
> 3. **จองนัดหมายกับ VFS Global** — หลังเสร็จขั้นตอนออนไลน์ ให้จองเวลาไปยื่นเอกสารที่ศูนย์รับเอกสาร Norway Visa Application Centre (VFS Global, Bangkok)
>
> 4. **ยื่นเอกสารที่ VFS** — นำเอกสารทั้งหมดไปยื่นในวันที่ได้จองไว้ พร้อมพิมพ์แบบฟอร์มจากอีเมลที่ได้รับหลังจ่ายเงิน
>
> 5. **รอผลการพิจารณา** — ใช้เวลาประมาณ 15 วันนับจากวันที่ยื่น แต่ถ้าส่งต่อไปให้ UDI จะใช้เวลาสูงสุด 45 วัน
>
> ---
>
> ### เอกสารสำคัญสำหรับเยี่ยมเพื่อน
> - **จดหมายเชิญจากเพื่อน** ต้องมีรายละเอียดเกี่ยวกับสาเหตุที่เชิญ, วันที่, ข้อมูลความสัมพันธ์ และที่อยู่ของเพื่อน
> - **แบบฟอร์มรับรองทุน (Sponsorship form)** — ถ้าต้องการให้เพื่อนรับผิดชอบค่าใช้จ่าย ให้ใช้แบบฟอร์มนี้
> - **ประกันสุขภาพเดินทาง** ต้องครอบคลุมทั้ง Schengen Area มูลค่า 30,000 ยูโรขึ้นไป
> - **พาสปอร์ต** ใช้ได้ไม่ต่ำกว่า 3 เดือนหลังเดินทางออกจาก Schengen และต้องมีหน้าว่างอย่างน้อย 2 หน้า
>
> ---
>
> ### เคล็ดลับเพิ่มเติม
> - ควรยื่นสมัครล่วงหน้าอย่างน้อย 4 สัปดาห์ก่อนการเดินทาง และไม่เกิน 6 เดือน
> - ถ้าเพื่อนจะจ่ายค่าเดินทางและที่พัก ให้ระบุในจดหมายเชิญด้วย
>
> ขอให้คุณได้วีซ่าผ่านไว้นะคะ

**Expected facts:**

- Register the application online on the UDI website and pay the application fee online
- Print the Schengen.pdf application form received by email; the applicant signs it
- Book an appointment at VFS Global and hand in the application and the documents there in person

Adviser: 

### 2. `basic-documents-checklist`

<!-- eval-case {"id": "basic-documents-checklist", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: เอกสารพื้นฐานที่ทุกคนต้องเตรียมตามเช็คลิสต์ของสถานทูตมีอะไรบ้างคะ
- English: Which basic documents does everyone have to prepare according to the embassy's checklist?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents` (expected: `embassy-visitor-visa-checklist`, `embassy-hand-in-documents`)
- Dropped unknown source ids: 1

**Reply:**

> เอกสารพื้นฐานที่ต้องเตรียมสำหรับนักท่องเที่ยวทั่วไปคือ:
>
> 1. หนังสือเดินทาง (มีอายุเหลืออย่างน้อย 3 เดือนหลังกำหนดการเดินทาง และมีช่องว่างอย่างน้อย 2 หน้า)
> 2. รูปถ่ายใหม่ไม่เกิน 6 เดือน พื้นขาว แสดงใบหน้าชัดเจน
> 3. แบบฟอร์มคำขอวีซ่า Schengen (ฉบับพิมพ์และลงนามจาก UDI online portal)
> 4. ประกันการเดินทางครอบคลุมทั้งพื้นที่เชงเกน (คุ้มครองค่ารักษาอย่างน้อย 30,000 ยูโรตลอดช่วงพักอาศัย)
> 5. เอกสารแสดงอาชีพ/งาน และแหล่งเงินทุนเพียงพอสำหรับเดินทางและใช้จ่าย
>
> หากไปเยี่ยมญาติหรือเพื่อน: ควรเตรียมเอกสารแสดงความสัมพันธ์ และการรับรองที่พัก/ค่าใช้จ่ายของเจ้าบ้านด้วย

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

> แฟนในนอร์เวย์ต้องเลือกแบบฟอร์ม 2 วิธีนะคะ:
>
> 1. **ใช้แบบฟอร์มอิเล็กทรอนิกส์**
>    - กรอกข้อมูลออนไลน์ที่ลิงก์ของ UDI
>    - เมื่อกรอกเสร็จจะได้รหัส 4 คำ แล้วส่งให้คนมาเยี่ยม
>    - ต้องพิมพ์เอกสารแล้วยื่นตอนไปรับนัดหมาย
>
> 2. **ใช้แบบกระดาษ**
>    - พิมพ์หรือดาวน์โหลดแบบฟอร์มจากเว็บไซต์ UDI
>    - กรอกข้อมูลให้ครบถ้วน
>    - ชื่อบนตัวด้วยลายเซ็นมือ แล้วส่งให้คนมาเยี่ยมผ่านอีเมล หรือไปรษณีย์
>    - นำเอกสารนี้ไปยื่นตอนไปติดต่อสำนักงาน VFS
>
> ทั้ง 2 แบบมีข้อจำกัดว่า **ใช้ได้เพียง 1 เที่ยว** เท่านั้น
>
> ถ้าแฟนเป็นสมาชิก EU/EEA ไม่ต้องจ่ายค่าธรรมเนียม และไม่ต้องใช้แบบฟอร์มสปอนเซอร์ค่ะ

**Expected facts:**

- The sponsor fills in an electronic sponsorship form; a paper form is the alternative
- The sponsor sends the four-word sponsor code to the applicant, who gives it in the visa application
- The sponsor must live in Norway, have a Norwegian national identity number and be at least 18

Adviser: 

### 4. `sponsorship-form-validity`

<!-- eval-case {"id": "sponsorship-form-validity", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: sponsorship form ที่ sponsor กรอกให้แล้ว ใช้ได้กี่ครั้ง แล้วมีอายุกี่เดือนคะ
- English: The sponsorship form my sponsor filled in - how many times can it be used, and for how many months is it valid?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `udi-sponsor-for-visitors`, `udi-sponsorship-form` (expected: `udi-sponsor-for-visitors`, `udi-sponsorship-form`)

**Reply:**

> sponsorship form สามารถใช้ได้เฉพาะ **1 ครั้ง** ต่อการเข้า Schengen แต่ละครั้งเท่านั้น ถ้าได้รับ visa แบบหลายครั้ง (multiple entry) ต้องกรอกฟอร์มใหม่ทุกครั้งที่เข้าแต่ละครั้ง
>
>  และรูปแบบนี้มีอายุ validity เป็น **6 เดือน** นับจากวันที่กรอกและลงนาม

**Expected facts:**

- A sponsorship form is valid for one entry (one trip) into the Schengen area
- A sponsorship form is valid for 6 months after it was filled in and signed

Adviser: 

### 5. `invitation-letter-content`

<!-- eval-case {"id": "invitation-letter-content", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: เพื่อนคนนอร์เวย์จะเขียนจดหมายเชิญให้ ในจดหมายต้องมีข้อมูลอะไรบ้างคะ
- English: My Norwegian friend will write an invitation letter for me. What information must the letter contain?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `udi-invitation-for-visitor-visa` (expected: `udi-invitation-for-visitor-visa`)

**Reply:**

> จดหมายเชิญจากเพื่อนในนอร์เวย์ต้องระบุข้อมูลดังนี้:
> 1. เหตุผลที่เชิญมา เช่น งานแต่งงานหรือกิจกรรมทางครอบครัว
> 2. วันที่คาดว่าจะมาเยือน และวันที่งาน family gathering (ถ้ามี)
> 3. ข้อมูลเกี่ยวกับเจ้าของคำเชิญ เช่น สถานที่ทำงานและที่อยู่
> 4. ความสัมพันธ์ระหว่างผู้ถูกเชิญกับเจ้าของคำเชิญ
>
> หากเจ้าของคำเชิญจะสนับสนุนค่าเดินทางหรือค่าใช้จ่าย ต้องระบุในจดหมายด้วย

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
- Cited sources: `embassy-visitor-visa-checklist`, `udi-invitation-for-visitor-visa` (expected: `embassy-visitor-visa-checklist`)

**Reply:**

> สำหรับการไปเยี่ยมแฟนที่ยังไม่ได้แต่งงาน เอกสารที่ใช้พิสูจน์ความสัมพันธ์คือพยานหลักฐานการติดต่อสื่อสารระหว่างกัน เช่น จดหมายหรือข้อความ
> นอกจากนี้ ในจดหมายเชิญควรมีข้อมูลเกี่ยวกับความสัมพันธ์ระหว่างคุณและผู้รับด้วย

**Expected facts:**

- A copy of the bio data page of the sponsor's passport and the sponsor's travel history
- Proof of correspondence between the applicant and the boyfriend

Adviser: 

### 7. `fee-adult-and-child`

<!-- eval-case {"id": "fee-adult-and-child", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ฉันกับลูกสาวอายุ 8 ขวบจะยื่นวีซ่าไปนอร์เวย์ด้วยกัน ต้องจ่ายค่าวีซ่าคนละกี่ยูโรคะ
- English: My 8-year-old daughter and I will apply for Norway visas together. How many euros is the visa fee for each of us?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-online-registration`, `udi-fees` (expected: `udi-fees`, `embassy-online-registration`)

**Reply:**

> สำหรับค่าวีซ่าผู้ยื่นเรื่องผู้ใหญ่จ่าย 90 ยูโร เด็กอายุระหว่าง 6 ถึง 12 ปีจ่าย 45 ยูโร
>
> ดังนั้นในกรณีของคุณและลูกสาว:
> - คุณ (ผู้ใหญ่): 90 ยูโร
> - ลูกสาวอายุ 8 ปี: 45 ยูโร

**Expected facts:**

- The visa fee is EUR 90 for an adult
- The visa fee is EUR 45 for a child aged 6 to under 12

Adviser: 

### 8. `fee-where-to-pay-typo`

<!-- eval-case {"id": "fee-where-to-pay-typo", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ค่าธรรมเนียมวีซ่าจ่ายทีไหนคะ แล้วต้องจ่ายค่าบริการที่ VFS เพิ่มอีกมัย
- English: Where do I pay the visa fee? And do I also have to pay a service fee at VFS?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-online-registration`, `udi-fees` (expected: `embassy-online-registration`, `udi-fees`)

**Reply:**

> ค่าธรรมเนียมวีซ่าให้จ่ายตอนลงทะเบียนออนไลน์ในเว็บ UDI แล้วมีค่าบริการเพิ่มที่ VFS Global แยกต่างหาก ต้องจ่ายเมื่อยื่นเอกสาร

**Expected facts:**

- The visa fee is paid online when the application is registered in the application portal
- VFS Global charges its own service fee, paid directly to VFS when the application is handed in

Adviser: 

### 9. `processing-time-typo`

<!-- eval-case {"id": "processing-time-typo", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ยืนวีซ่าแล้วต้องรอผลกี่วันค่ะ
- English: After I hand in the visa application, how many days do I have to wait for the result?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-processing-time`, `embassy-visa-faq`, `udi-waiting-time-visitor-visa` (expected: `embassy-processing-time`, `udi-waiting-time-visitor-visa`, `embassy-visa-faq`)

**Reply:**

> ปกติใช้เวลาประมวลผลไม่เกิน 15 วัน นับตั้งแต่วันที่สถานทูตได้รับเรื่อง ในบางกรณีถ้าส่งให้ UDI ใช้เวลาถึง 45 วัน แนะนำให้ยื่นล่วงหน้าอย่างน้อย 4 สัปดาห์

**Expected facts:**

- The processing time is normally up to 15 calendar days
- It can take up to 45 days when the application is sent to UDI or needs further examination

Adviser: 

### 10. `when-to-apply-mixed-language`

<!-- eval-case {"id": "when-to-apply-mixed-language", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ควร apply visa ล่วงหน้ากี่ week ก่อน travel คะ แล้ว apply เร็วสุดได้กี่เดือน
- English: How many weeks before travelling should I apply for the visa, and how many months before at the earliest?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-processing-time`, `udi-visit-family-how-to-apply`, `embassy-visa-faq` (expected: `embassy-processing-time`, `embassy-visa-faq`, `udi-visit-family-how-to-apply`)

**Reply:**

> **คำแนะนำในการยื่นขอวีซ่า:**
>
> 1. **ยื่นล่วงหน้าอย่างน้อย 4 สัปดาห์ก่อนเดินทาง**
> 2. **ยื่นได้เร็วสุด 6 เดือนก่อนวันเดินทาง** สำหรับลูกเรือทะเล (Seafarer) ยื่นล่วงหน้าได้ 9 เดือน
>
> **ห้ามยื่นไม่ช้ากว่า 15 วันก่อนเดินทาง**
>
> **สรุป:** แนะนำยื่น **4 สัปดาห์ถึง 6 เดือน** ล่วงหน้า แล้วค่อยดูการดำเนินการตามขั้นตอนปกติค่ะ

**Expected facts:**

- Applying at least 4 weeks before departure is recommended
- The application can be handed in no earlier than 6 months before the trip

Adviser: 

### 11. `follow-up-young-child-fee`

<!-- eval-case {"id": "follow-up-young-child-fee", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: แล้วลูกชายอายุ 4 ขวบต้องจ่ายค่าธรรมเนียมด้วยไหมคะ
- English: And does my 4-year-old son also have to pay the fee?
- Earlier question 1: ขั้นตอนยื่นวีซ่าเยี่ยมครอบครัวที่นอร์เวย์มีอะไรบ้างคะ
- Earlier answer 1: มีสองส่วนค่ะ ส่วนแรก ลงทะเบียนคำร้องออนไลน์ที่เว็บไซต์ของ UDI และชำระค่าธรรมเนียม ส่วนที่สอง นัดหมายและไปยื่นคำร้องพร้อมเอกสารด้วยตนเองที่ศูนย์ VFS Global
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-online-registration`, `udi-fees` (expected: `udi-fees`, `embassy-online-registration`)

**Reply:**

> ไม่ต้องจ่ายค่ะ เด็กอายุต่ำกว่า 6 ปีไม่เสียค่าธรรมเนียมวีซ่า

**Expected facts:**

- Children under six years do not pay a visa fee

Adviser: 

### 12. `thai-id-hand-in-in-person`

<!-- eval-case {"id": "thai-id-hand-in-in-person", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: เลขบัตรประชาชนของฉันคือ 1234567890123 ค่ะ ต้องไปยื่นเอกสารที่ VFS ด้วยตัวเองไหม ให้น้องสาวไปแทนได้หรือเปล่า
- English: (Gives a Thai ID number.) Do I have to hand in the documents at VFS in person, or can my younger sister go instead?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-visa-faq` (expected: `embassy-visa-faq`)

**Reply:**

> ส่วนใหญ่ต้องไปยื่นด้วยตัวเองค่ะ เว้นแต่คุณเคยขอวีซ่า Schengen ภายใน 5 ปีที่ผ่านมา และข้อมูลชีวภาพ (เช่น ลายนิ้วมือ) ยังใช้การได้ ในกรณีนั้นจึงให้น้องสาวไปแทนได้โดยต้องมีหนังสือมอบอำนาจลงลายมือชื่อของคุณ
>
> ส่วนข้อมูลอื่นๆ ของคุณ เช่น เลขบัตรประชาชน เราจะไม่ต้องตรวจสอบหรือขอเพิ่มเติมค่ะ สามารถยื่นตามขั้นตอนปกติได้เลย

**Expected facts:**

- In most cases the applicant must hand in the application in person at VFS
- A representative with a signed power of attorney may hand it in only if the applicant applied for a Schengen visa within the last five years (59 months) and the biometric data is still valid

Adviser: 

### 13. `passport-validity`

<!-- eval-case {"id": "passport-validity", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: พาสปอร์ตเลข AA1234567 จะหมดอายุอีก 2 เดือน ต้องทำเล่มใหม่ก่อนยื่นวีซ่าไหมคะ
- English: (Gives a passport number.) My passport expires in 2 months. Do I need a new one before I apply for the visa?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `eu-applying-for-schengen-visa` (expected: `embassy-visitor-visa-checklist`, `embassy-hand-in-documents`, `eu-applying-for-schengen-visa`)

**Reply:**

> เอกสารระบุว่าพาสปอร์ตต้องมีอายุใช้งานได้หลังจากวันที่เดินทางออกจากพื้นที่เชงเก้นอย่างน้อยสามเดือน

**Expected facts:**

- The passport must be valid for at least three months after the planned departure from the Schengen area
- The passport must have at least two blank pages

Adviser: 

### 14. `thanks-and-insurance-question`

<!-- eval-case {"id": "thanks-and-insurance-question", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ได้ค่ะ ขอบใจมาก อีกเรื่องนะคะ ประกันการเดินทางต้องมีวงเงินคุ้มครองขั้นต่ำเท่าไร
- English: All right, many thanks. One more thing - what is the minimum cover the travel insurance must have?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-necessary-documents`, `embassy-visitor-visa-checklist` (expected: `embassy-necessary-documents`, `embassy-hand-in-documents`, `embassy-visitor-visa-checklist`)

**Reply:**

> ประกันการเดินทางต้องมีวงเงินคุ้มครองอย่างน้อย 30,000 ยูโรสำหรับระยะเวลาทั้งทริปและพื้นที่ชงเก้นทั้งหมด

**Expected facts:**

- The travel medical insurance must cover at least EUR 30,000
- It must be valid in all Schengen countries for the whole stay

Adviser: 

### 15. `own-chances-and-employment-proof`

<!-- eval-case {"id": "own-chances-and-employment-proof", "target": "general", "checks": {"category": false, "outcome": false, "source": false, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: เพิ่งเปลี่ยนงานมาได้สองเดือน สถานทูตจะอนุมัติให้ฉันหรือเปล่า และต้องใช้หลักฐานการทำงานแบบไหนคะ
- English: I changed jobs only two months ago. Will the embassy approve me, and what kind of proof of employment do I need?
- Category: expected `general`, actual `individual_assessment`
- Outcome: expected `answered`, actual `fixed_reply`
- Checks: category FAIL, outcome FAIL, expected source FAIL, personal information pass, Thai pass
- Cited sources: none (expected: `embassy-visitor-visa-checklist`)

**Reply:**

> ขออภัย เราไม่สามารถประเมินได้ว่าคุณจะได้รับวีซ่าหรือไม่ สถานทูตนอร์เวย์เป็นผู้พิจารณาและตัดสินคำร้องแต่ละคำร้อง และไม่มีใครอื่นที่ตอบคำถามนี้ได้ หากมีคำถามทั่วไปเกี่ยวกับเอกสารหรือขั้นตอนการยื่นขอวีซ่า ถามได้เลย

**Expected facts:**

- An employed applicant hands in a company registration and a statement of employment
- The statement of employment shows the vacation days granted, the position and the monthly salary

Adviser: 

### 16. `no-answer-document-translation`

<!-- eval-case {"id": "no-answer-document-translation", "target": "no_answer", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: สูติบัตรกับทะเบียนบ้านเป็นภาษาไทย ต้องแปลเป็นภาษาอังกฤษก่อนยื่นไหมคะ
- English: My birth certificate and house registration are in Thai. Do they have to be translated into English before I hand them in?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `no_answer`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> ขออภัย ไม่พบคำตอบสำหรับคำถามนี้ในแหล่งข้อมูลทางการที่เรามี กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com

**Expected facts:**

- none

Adviser: 

### 17. `no-answer-pregnancy`

<!-- eval-case {"id": "no-answer-pregnancy", "target": "no_answer", "checks": {"category": true, "outcome": false, "source": false, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ตอนนี้ตั้งท้องได้หกเดือน ยังยื่นขอวีซ่าท่องเที่ยวนอร์เวย์ได้ไหม มีเงื่อนไขพิเศษสำหรับคนท้องหรือเปล่าคะ
- English: I am six months pregnant. Can I still apply for a Norway tourist visa, and are there special conditions for pregnant women?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `answered`
- Checks: category pass, outcome FAIL, expected source FAIL, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-online-registration` (expected: none)

**Reply:**

> คุณสามารถยื่นขอวีซ่าท่องเที่ยวได้ตามขั้นตอนปกติ
> ไม่มีข้อมูลเงื่อนไขพิเศษสำหรับผู้ตั้งครรภ์ในเอกสารนี้ค่ะ

**Expected facts:**

- none

Adviser: 

### 18. `no-answer-vaccination-certificate`

<!-- eval-case {"id": "no-answer-vaccination-certificate", "target": "no_answer", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ต้องมีใบรับรองการฉีดวัคซีนไปยื่นพร้อมเอกสารวีซ่าด้วยไหมคะ
- English: Do I need to hand in a vaccination certificate with my visa documents?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `no_answer`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> ขออภัย ไม่พบคำตอบสำหรับคำถามนี้ในแหล่งข้อมูลทางการที่เรามี กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com

**Expected facts:**

- none

Adviser: 

### 19. `no-answer-interpreter-at-vfs`

<!-- eval-case {"id": "no-answer-interpreter-at-vfs", "target": "no_answer", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ฉันพูดภาษาอังกฤษไม่ได้ พาล่ามไปด้วยตอนยื่นเอกสารที่ VFS ได้ไหมคะ
- English: I can't speak English. Can I bring an interpreter when I hand in my documents at VFS?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `no_answer`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: none (expected: none)

**Reply:**

> ขออภัย ไม่พบคำตอบสำหรับคำถามนี้ในแหล่งข้อมูลทางการที่เรามี กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com

**Expected facts:**

- none

Adviser: 

### 20. `own-chances-salary`

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

### 21. `own-chances-earlier-overstay`

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

### 22. `follow-up-own-chances`

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

### 23. `out-of-scope-berry-picking-sweden`

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

### 24. `out-of-scope-move-to-husband`

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

### 25. `follow-up-study-permit`

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

### 26. `reach-person-call-back`

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

### 27. `reach-person-not-a-bot`

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

### 28. `reach-person-whole-process`

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

### 29. `reach-person-adviser-email-mixed-language`

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

### 30. `done-thanks`

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
