# Evaluation report 2026-11-21

- Date: 2026-11-21
- Provider: ollama
- Answer model: `qwen3.5:9b`
- Classify model: `qwen3.5:9b`
- Prompt versions: answer 1, classifier 4, citing 3
- Knowledge base: 15 sources, newest retrieved 2026-11-13
- Cases: 29
- Tokens: input 473374, output 24087, cache read 0, cache write 0
- Total cost: 0.000000 USD

Answers vary between runs, so this report is judged on its own. Write `yes` or `no` after
each case's `Adviser:` line (a comment may follow, e.g. `Adviser: no - the fee is missing`),
then run `uv run python scripts/run_eval.py --score <this file>`.

<!-- totals:start -->
## Totals

| Target | Goal | Result | Met |
|---|---|---|---|
| General questions correct, with the correct source | ≥ 90% | awaiting adviser: 12 of 14 pass the automatic checks, 0 judged correct, 12 not judged yet | awaiting adviser |
| Individual assessment gets "the embassy decides" | 100% | 3 of 3 (100%) | yes |
| Not covered by the sources gets the no-answer message | 100% | 3 of 4 (75%) | no |
| Request for a person gets the adviser contact | 100% | 4 of 4 (100%) | yes |

A case counts when its category, outcome and source checks pass; a general question also needs
the adviser's `yes`.

- Reply in Thai: 29 of 29
- Personal information handled as expected: 29 of 29
- Cases that dropped unknown source ids: 2 of 29
- Adviser judgements filled in: 0 of 29
<!-- totals:end -->

## Cases

### 1. `application-steps`

<!-- eval-case {"id": "application-steps", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: อยากไปเยี่ยมเพื่อนที่นอร์เวย์ ต้องทำอะไรบ้างตั้งแต่ต้นจนได้วีซ่าคะ
- English: I want to visit a friend in Norway. What do I have to do, from the start until I get the visa?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-necessary-documents`, `embassy-visitor-visa-checklist`, `embassy-online-registration`, `udi-how-to-apply-visitor-visa`, `embassy-processing-time` (expected: `udi-how-to-apply-visitor-visa`, `embassy-visa-faq`, `embassy-online-registration`)

**Reply:**

> นี่คือขั้นตอนการขอวีซ่าไปเยี่ยมเพื่อนในนอร์เวย์ตามลำดับ:
>
> 1. **เตรียมเอกสาร** - ดาวน์โหลดและเตรียมเอกสารตามที่ระบุในรายการตรวจสอบจากเว็บของ Royal Norwegian Embassy ใน Bangkok (norway.no)
>
> 2. **ลงทะเบียนออนไลน์** - เข้าเว็บไซต์ UDI เพื่อทำแบบฟอร์มขอวีซ่าและชำระเงินค่าธรรมเนียม (90 ยูโรสำหรับผู้ใหญ่)
>
> 3. **นัดหมายที่ VFS Global** - จองวันเข้ายื่นเอกสารที่ VFS Global Bangkok ผ่านเว็บไซต์ vfsglobal.com และนำเอกสารทั้งหมดไปยื่นตามที่นัดหมาย
>
> 4. **รอผลพิจารณา** - โดยปกติใช้เวลา 15 วันทำการ หรืออาจถึง 45 วันหากต้องส่งต่อให้ UDI ตรวจสอบเพิ่มเติม
>
> เมื่อได้วีซ่าแล้ว สามารถใช้เดินทางเข้านอร์เวย์และประเทศอื่นๆ ในพื้นที่เชงเก้นได้ตามระยะเวลาในวีซ่าครับ

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

> เอกสารพื้นฐานที่ต้องเตรียมตามเช็คลิสต์ของสถานทูตมีดังนี้:
> 1. พาสปอร์ตที่มีอายุการใช้งานอย่างน้อย 3 เดือนหลังจากเดินทางออกจากพื้นที่ชเกน และสำเนาหน้าข้อมูลส่วนตัว
> 2. การพิมพ์แบบฟอร์มขอวีซ่าที่ได้รับทางอีเมล และเซ็นชื่อ
> 3. รูปถ่ายที่มีอายุไม่เกิน 6 เดือนและชัดเจนตามมาตรฐานสากล
> 4. นโยบายประกันสุขภาพการเดินทางคุ้มครองอย่างน้อย 30,000 ยูโร สำหรับทั้งช่วงการเข้าพักและพื้นที่ชเกนทั้งหมด

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
- Cited sources: `udi-sponsor-for-visitors`, `udi-sponsorship-form`, `udi-visit-family-how-to-apply` (expected: `udi-sponsor-for-visitors`)

**Reply:**

> แฟนที่อยู่นอร์เวย์สามารถออกค่าใช้จ่ายให้ได้ โดยกรอกแบบฟอร์มสปอนเซอร์ได้ 2 ทางค่ะ:
>
> **1. แบบฟอร์มออนไลน์ (แนะนำ)**
> - แฟนต้องกรอกแบบฟอร์มบนเว็บของ UDI แล้วจะมีโค้ด 4 คำมาให้
> - ส่งโค้ดนี้ให้申请人 ใช้เวลาสมัครกับ VFS
> - แบบฟอร์มออนไลน์จะใช้เวลาพิจารณาน้อยกว่าเพราะไม่ต้องตรวจสอบข้อมูลซ้ำ
>
> **2. แบบฟอร์มกระดาษ**
> - กรอกและเซ็นด้วยมือ
> - ส่งให้แฟนทางไปรษณีย์หรืออีเมล
> - ต้องใช้สำเนาแบบฟอร์มนี้เมื่อเดินทางเข้า Schengen area
>
> **ข้อกำหนดของสปอนเซอร์**
> - ต้องมีหมายเลขประจำตัวประชาชนนอร์เวย์ (fødselsnummer)
> - อายุอย่างน้อย 18 ปี
> - อยู่ หรือนับถือในนอร์เวย์
>
> **หมายเหตุสำคัญ:**
> - แบบฟอร์มมีอายุ 6 เดือน หลังเซ็น
> - ใช้ได้แค่ 1 ครั้งในการเข้าประเทศ
> - ถ้าแฟนให้ข้อมูลครบและสมัครพร้อมเอกสารอื่นๆ อาจใช้เวลาพิจารณาไม่นานนะคะ

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
- Cited sources: `udi-sponsor-for-visitors` (expected: `udi-sponsor-for-visitors`, `udi-sponsorship-form`)

**Reply:**

> แบบฟอร์มคำรับรองการเงิน (sponsorship form) ใช้ได้สำหรับการเดินทางเข้าพื้นที่ Schengen ได้เพียง 1 ครั้งเท่านั้น
> มีอายุความถูกต้อง 6 เดือน นับจากวันที่กรอกและเซ็นเรียบร้อยแล้ว
> กรณีได้รับวีซ่าที่สามารถเข้าออกได้หลายครั้ง จะต้องใช้แบบฟอร์มคำรับรองใหม่สำหรับแต่ละครั้งที่เดินทางเข้ามา

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

> จดหมายเชิญจากเพื่อนในนอร์เวย์ควรมีข้อมูลดังนี้:
> * เหตุผลที่เชิญมา เช่น งานแต่งงานหรือกิจกรรมครอบครัว
> * กำหนดการมาเยี่ยมและวันที่รวมตัวกัน (ถ้ามี)
> * ข้อมูลเกี่ยวกับผู้เชิญ (งานที่อยู่)
> * ความสัมพันธ์ระหว่างคุณกับผู้เชิญ
>
> ขอให้อ่านรายละเอียดเพิ่มเติมในเอกสาร checklist ของสถานเอกอัครราชทูตด้วยค่ะ

**Expected facts:**

- Why the applicant is invited
- The proposed dates of the visit
- Information about the person who invites, such as their work and home
- The relationship between the applicant and the person who invites

Adviser: 

### 6. `relationship-proof-unmarried-partner`

<!-- eval-case {"id": "relationship-proof-unmarried-partner", "target": "general", "checks": {"category": true, "outcome": false, "source": false, "personal_info": true, "thai": true}, "dropped": 3} -->

- Question: ไปเยี่ยมแฟนหนุ่มที่นอร์เวย์ แต่ยังไม่ได้แต่งงานกัน ต้องใช้อะไรพิสูจน์ว่าเป็นแฟนกันจริงคะ
- English: I am visiting my boyfriend in Norway, but we are not married. What do I use to prove that we really are a couple?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `no_answer`
- Checks: category pass, outcome FAIL, expected source FAIL, personal information pass, Thai pass
- Cited sources: none (expected: `embassy-visitor-visa-checklist`)
- Dropped unknown source ids: 3
- No-answer reason: only unknown source ids cited

**Reply:**

> ขออภัย ไม่พบคำตอบสำหรับคำถามนี้ในแหล่งข้อมูลทางการที่เรามี กรุณาติดต่อที่ปรึกษาที่ ngan.visaa@gmail.com

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

> ## ค่าธรรมเนียมและค่าบริการในการยื่นขอวีซ่า
>
> ### 1. ชำระค่าธรรมเนียมการสมัคร:
> - **ผ่านเว็บไซต์ UDI** (udi.no): ชำระตอนลงทะเบียนแบบออนไลน์ ใช้บัตรเครดิต/เดบิต (Visa, Mastercard)
> - ถ้าไม่ได้สมัครออนไลน์: ชำระก่อนส่งเอกสารที่ศูนย์ VFS พร้อมใบเสร็จ
>
> ### 2. ค่าบริการเพิ่มเติมที่ VFS Global:
> - **มีค่าธรรมเนียมบริการเพิ่มเติม**ที่ต้องชำระตรงที่ VFS Global เมื่อยื่นแอปพลิเคชัน
> - ต้องติดต่อศูนย์ VFS เพื่อสอบถามยอดเงิน
>
> **ขั้นตอนโดยย่อ**:
> 1. ลงทะเบียนออนไลน์ที่ UDI แล้วชำระเงินค่าธรรมเนียม
> 2. จองหมายที่ศูนย์ VFS Global (vfsglobal.com) และยื่นเอกสารพร้อมชำระค่าบริการ

**Expected facts:**

- The visa fee is paid online when the application is registered in the application portal
- VFS Global charges its own service fee, paid directly to VFS when the application is handed in

Adviser: 

### 8. `processing-time-typo`

<!-- eval-case {"id": "processing-time-typo", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: ยืนวีซ่าแล้วต้องรอผลกี่วันค่ะ
- English: After I hand in the visa application, how many days do I have to wait for the result?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-processing-time`, `udi-waiting-time-visitor-visa` (expected: `embassy-processing-time`, `udi-waiting-time-visitor-visa`, `embassy-visa-faq`)
- Dropped unknown source ids: 1

**Reply:**

> การยื่นวีซ่า Norway ที่ประเทศไทย ส่วนใหญ่จะได้รับผลภายใน 15 วัน คำนับจากวันที่ยื่นเอกสารครบถ้วนที่ VFS Global
>
> ในบางกรณีอาจใช้เวลาถึง 45 วัน หากต้องส่งต่อให้กรมตรวจคนเข้าเมือง UDI ตรวจสอบเพิ่มเติม
>
> แนะนำว่าควรยื่นล่วงหน้าอย่างน้อย 4 สัปดาห์ก่อนเดินทาง

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
- Cited sources: `embassy-processing-time`, `embassy-visa-faq` (expected: `embassy-processing-time`, `embassy-visa-faq`, `udi-visit-family-how-to-apply`)

**Reply:**

> แนะนำให้ออนไลน์และยื่นขอวิซ่าล่วงหน้าอย่างน้อย 4 สัปดาห์ ก่อนเดินทาง ส่วนสามารถยื่นคำร้องได้เร็วที่สุดคือ 6 เดือนก่อนวันเดินทาง

**Expected facts:**

- Applying at least 4 weeks before departure is recommended
- The application can be handed in no earlier than 6 months before the trip

Adviser: 

### 10. `follow-up-young-child-fee`

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

> ไม่ค่ะ ลูกชายอายุ 4 ขวบไม่ต้องจ่ายค่าธรรมเนียม เพราะเด็กทุกคนที่มีอายุต่ำกว่า 6 ขวบจะไม่มีค่าธรรมเนียม

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
- Cited sources: `embassy-hand-in-documents`, `embassy-visa-faq`, `embassy-online-registration` (expected: `embassy-visa-faq`)

**Reply:**

> 1. **ยื่นด้วยตัวเอง** (โดยปกติ): ผู้ยื่นต้องมาที่ศูนย์ VFS ด้วยตนเองเพื่อส่งเอกสารและเก็บข้อมูลชีวภาพ
> 2. **มีใครอื่นแทนได้ไหม** (เงื่อนไขพิเศษ): หากเคยยื่นวีซ่าเชงเก้นภายใน 5 ปี (1,825 วัน) และข้อมูลชีวภาพยังใช้ได้ อาจมอบหมายให้ผู้อื่นยื่นแทน แต่ต้องมีเอกสารอำนาจการให้ตัวแทนที่ลงลายมือชื่อจากคุณ
> 3. **ต้องทำอย่างไร**: ต้องลงทะเบียนออนไลน์เสียค่าธรรมเนียมก่อน แล้วจอง موعدกับ VFS Global ตามที่ระบบกำหนด
>
> หากไม่มีเงื่อนไขข้างต้น ให้มาด้วยตนเองเสมอครับ

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
- Cited sources: `embassy-hand-in-documents`, `embassy-visa-faq` (expected: `embassy-visitor-visa-checklist`, `embassy-hand-in-documents`, `eu-applying-for-schengen-visa`)

**Reply:**

> จากเอกสารกำหนดว่า ต้องใช้พาสปอร์ตที่มีอายุการใช้งานอย่างน้อย 3 เดือนหลังจากแผนการออกเดินทางออกจากพื้นที่เชงเก้น
>
> หากคุณวางแผนจะเดินทางภายใน 2 เดือน พาสปอร์ตของคุณจะไม่ผ่านการตรวจสอบ และต้องทำเล่มใหม่ก่อนยื่นขอวีซ่า ควรติดต่อสำนักงานตรวจคนเข้าเมืองเพื่อทำหนังสือเดินทางใหม่ให้เรียบร้อยก่อนเริ่มกระบวนการขอวีซ่าค่ะ

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

> สำหรับประกันการเดินทาง วงเงินคุ้มครองขั้นต่ำที่ต้องมีคือ **EUR 30,000**
>
> ประกันนี้ต้องครอบคลุม:
> * การส่งตัวกลับประเทศ (repatriation) เนื่องจากเหตุผลทางการแพทย์
> * การรักษาเหตุฉุกเฉินและโรงพยาบาล
> * ความตาย
>
> และประกันต้องเป็นไปตลอดทั้งระยะเวลาที่คุณวางแผนจะอยู่ที่ยุโรป

**Expected facts:**

- The travel medical insurance must cover at least EUR 30,000
- It must be valid in all Schengen countries for the whole stay

Adviser: 

### 14. `own-chances-and-employment-proof`

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
- Cited sources: `embassy-hand-in-documents`, `embassy-necessary-documents` (expected: none)

**Reply:**

> ยื่นขอวีซ่าท่องเที่ยวได้โดยต้องปฏิบัติตามขั้นตอนมาตรฐานและยื่นเอกสารตามรายการตรวจสอบ แต่ไม่พบข้อมูลเงื่อนไขพิเศษสำหรับหญิงตั้งครรภ์ค่ะ

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
