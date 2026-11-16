# Evaluation report 2026-11-16

- Date: 2026-11-16
- Provider: ollama
- Answer model: `qwen3.5:9b`
- Classify model: `qwen3.5:9b`
- Prompt versions: answer 1, classifier 3, citing 2
- Knowledge base: 15 sources, newest retrieved 2026-11-13
- Cases: 30
- Tokens: input 488691, output 20128, cache read 0, cache write 0
- Total cost: 0.000000 USD

Answers vary between runs, so this report is judged on its own. Write `yes` or `no` after
each case's `Adviser:` line (a comment may follow, e.g. `Adviser: no - the fee is missing`),
then run `uv run python scripts/run_eval.py --score <this file>`.

<!-- totals:start -->
## Totals

| Target | Goal | Result | Met |
|---|---|---|---|
| General questions correct, with the correct source | ≥ 90% | 13 of 15 (86.7%) | no |
| Individual assessment gets "the embassy decides" | 100% | 3 of 3 (100%) | yes |
| Not covered by the sources gets the no-answer message | 100% | 1 of 4 (25%) | no |
| Request for a person gets the adviser contact | 100% | 4 of 4 (100%) | yes |

A case counts when its category, outcome and source checks pass; a general question also needs
the adviser's `yes`.

- Reply in Thai: 30 of 30
- Personal information handled as expected: 30 of 30
- Cases that dropped unknown source ids: 4 of 30
- Adviser judgements filled in: 30 of 30
<!-- totals:end -->

## Cases

### 1. `application-steps`

<!-- eval-case {"id": "application-steps", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: อยากไปเยี่ยมเพื่อนที่นอร์เวย์ ต้องทำอะไรบ้างตั้งแต่ต้นจนได้วีซ่าคะ
- English: I want to visit a friend in Norway. What do I have to do, from the start until I get the visa?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-necessary-documents`, `embassy-online-registration`, `udi-how-to-apply-visitor-visa`, `embassy-hand-in-documents`, `udi-invitation-for-visitor-visa`, `udi-sponsor-for-visitors`, `udi-fees`, `embassy-processing-time`, `embassy-visa-faq` (expected: `udi-how-to-apply-visitor-visa`, `embassy-visa-faq`, `embassy-online-registration`)
- Dropped unknown source ids: 1

**Reply:** 

> ## ขั้นตอนการขอวีซ่าท่องเที่ยวเพื่อไปเยี่ยมเพื่อนที่นอร์เวย์
>
> 1. **เตรียมเอกสาร** - ใช้รายการตรวจเช็คจากเว็บไซต์ n norway.no
> 2. **ลงทะเบียนออนไลน์ที่ UDI** - เข้าเว็บ udi.no แล้วกรอกแบบฟอร์มและชำระเงินค่าธรรมเนียม
> 3. **จองนัดหมายกับ VFS Global** - จองผ่าน vfsglobal.com และส่งเอกสารที่ศูนย์นั้น ๆ
>
> ### เอกสารที่ต้องเตรียม (สำหรับไปเยี่ยมเพื่อน)
> * บัตรเดินทางสุขภาพ (ครอบคลุม 30,000 ยูโร ทั้งพื้นที่เชงเก้น)
> * หนังสือเชิญจากเพื่อนในนอร์เวย์ หรือแบบ Sponsorship form
> * หลักฐานที่อยู่/การสนับสนุนค่าใช้จ่ายของเพื่อนในนอร์เวย์
>
> ### การชำระเงินค่าธรรมเนียม
> * ผู้ใหญ่ชำระ 90 ยูโร (เด็ก 6-12 ปี ชำระ 45 ยูโร, เด็กต่ำกว่า 6 ปี ไม่ต้องชำระ)
>
> ### เวลาในการพิจารณา
> * ใช้เวลาประมาณ 15 วัน (หรือสูงสุด 45 วันหากส่งต่อให้ UDI พิจารณา)
>
> แนะนำให้ยื่นขอล่วงหน้าอย่างน้อย 4 สัปดาห์ก่อนเดินทาง

**Expected facts:**

- Register the application online on the UDI website and pay the application fee online
- Print the Schengen.pdf application form received by email; the applicant signs it
- Book an appointment at VFS Global and hand in the application and the documents there in person

Adviser: yes

### 2. `basic-documents-checklist`

<!-- eval-case {"id": "basic-documents-checklist", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: เอกสารพื้นฐานที่ทุกคนต้องเตรียมตามเช็คลิสต์ของสถานทูตมีอะไรบ้างคะ
- English: Which basic documents does everyone have to prepare according to the embassy's checklist?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-visitor-visa-checklist`, `embassy-online-registration` (expected: `embassy-visitor-visa-checklist`, `embassy-hand-in-documents`)

**Reply:**

> เอกสารพื้นฐานที่ทุกคนต้องเตรียมตามเช็คลิสต์ของสถานทูตมีดังนี้ครับ
>
> 1. **หนังสือเดินทาง (Passport)** ต้องเป็นฉบับเดิม อายุความคงเหลือไม่น้อยกว่า 3 เดือนหลังวันออกเดินทาง และมีหน้าว่างอย่างน้อย 2 หน้า พร้อมสำเนาหน้าข้อมูลส่วนบุคคล
> 2. **รูปถ่าย (Photo)** จำนวน 1 รูป ถ่ายมาไม่เกิน 6 เดือน ไม่ผ่านการตัดต่อ พื้นหลังสีขาว ขนาดถูกต้องตามมาตรฐานสากล
> 3. **แบบฟอร์มใบสมัคร (Application Form)** ต้องพิมพ์ออกมาจากเว็บไซต์ UDI แล้วเซ็นชื่อด้วยตนเอง
> 4. **ประกันสุขภาพเดินทาง (Travel Medical Insurance)** ต้องคุ้มครองตลอดระยะเวลาอยู่ในประเทศสมาชิกสเชนเจนทั้งหมด และครอบคลุมค่ารักษาพยาบาลขั้นต่ำ 30,000 ยูโร
> 5. **เอกสารแสดงอาชีพและตัวตน** เช่น สำเนาใบเปลี่ยนชื่อ หรือหลักฐานงาน/ธุรกิจ หากมีอยู่ (กรณีต้องแสดงให้ครบตามวัตถุประสงค์)

**Expected facts:**

- A passport valid for at least three months after the trip, with at least two blank pages
- A signed printout of the application form from the UDI application portal
- Travel medical insurance for the whole trip and the whole Schengen area, covering at least EUR 30,000

Adviser: yes

### 3. `sponsor-how-to-fill-in`

<!-- eval-case {"id": "sponsor-how-to-fill-in", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: แฟนที่อยู่นอร์เวย์จะออกค่าใช้จ่ายให้ เขาต้องกรอกแบบฟอร์มสปอนเซอร์ยังไงคะ
- English: My partner in Norway will pay for the trip. How does he fill in the sponsorship form?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `udi-sponsor-for-visitors`, `udi-visit-family-how-to-apply`, `udi-sponsorship-form`, `embassy-necessary-documents` (expected: `udi-sponsor-for-visitors`)
- Dropped unknown source ids: 1

**Reply:**

> **ขั้นตอนให้แฟนในนอร์เวย์กรอกแบบฟอร์มสปอนเซอร์:**
>
> 1. **ใช้แบบฟอร์มอิเล็กทรอนิกส์ (แนะนำ)**
>    - กรอกแบบฟอร์มออนไลน์บนเว็บไซต์ของ UDI
>    - หลังจากยืนยันข้อมูล จะได้รับ **รหัส 4 คำ** ที่ส่งให้แฟนคุณ
>    - แฟนจะพิมพ์เอกสารและนำยื่นตอนไป递交ที่ VFS Global
>
> 2. **ใช้แบบฟอร์มกระดาษ (ทางเลือก)**
>    - ดาวน์โหลดแบบฟอร์มจากเว็บไซต์ UDI
>    - กรอกข้อมูลและส่งทางอีเมลหรือทางไปรษณีย์
>    - ต้องลงลายมือชื่อด้วยปากกา
>    - ประเมินว่าใช้เวลาตรวจสอบนานกว่าแบบอิเล็กทรอนิกส์
>
> 3. **ส่งให้แฟนคุณ**
>    - ส่งรหัสสปอนเซอร์ หรือแบบฟอร์มกระดาษให้แฟนคุณ
>    - แฟนจะนำมายื่นพร้อมกับเอกสารอื่นๆ ที่ศูนย์บริการวีซ่า (VFS Global) ในไทย
>
> 4. **ข้อมูลสำคัญของสปอนเซอร์**
>    - ต้องเป็นพลเมืองนอร์เวย์ และอาศัยในนอร์เวย์
>    - อายุอย่างน้อย 18 ปี
>    - มีเลขประจำตัวประชาชนนอร์เวย์ (fødselsnummer)
>    - กรอกข้อมูลให้ถูกต้องครบถ้วน
>
> **หมายเหตุ:**
> - แบบฟอร์มมีอายุ 6 เดือนหลังจากกรอกเสร็จ
> - ใช้ได้กับการเดินทางหนึ่งครั้งเท่านั้น
> - ไม่สามารถใช้แบบเดียวกันสำหรับการเดินทางหลายครั้งถ้าขอวีซ่า multiple-entry

**Expected facts:**

- The sponsor fills in an electronic sponsorship form; a paper form is the alternative
- The sponsor sends the four-word sponsor code to the applicant, who gives it in the visa application
- The sponsor must live in Norway, have a Norwegian national identity number and be at least 18

Adviser: yes

### 4. `sponsorship-form-validity`

<!-- eval-case {"id": "sponsorship-form-validity", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: sponsorship form ที่ sponsor กรอกให้แล้ว ใช้ได้กี่ครั้ง แล้วมีอายุกี่เดือนคะ
- English: The sponsorship form my sponsor filled in - how many times can it be used, and for how many months is it valid?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `udi-sponsor-for-visitors`, `udi-sponsorship-form` (expected: `udi-sponsor-for-visitors`, `udi-sponsorship-form`)

**Reply:**

> **ใช้ได้เพียง 1 ครั้งเท่านั้น** (สำหรับการเข้า Schengen area หนึ่งครั้ง)
>
> **มีอายุใช้ 6 เดือน** นับจากวันที่กรอกและเซ็นเรียบร้อยแล้ว
>
> ถ้าได้รับวิซ่าแบบเข้าได้หลายครั้ง (multiple entry) ต้องกรอกฟอร์มใหม่สำหรับแต่ละเที่ยวที่เดินทางเข้าไปคะ

**Expected facts:**

- A sponsorship form is valid for one entry (one trip) into the Schengen area
- A sponsorship form is valid for 6 months after it was filled in and signed

Adviser: yes

### 5. `invitation-letter-content`

<!-- eval-case {"id": "invitation-letter-content", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: เพื่อนคนนอร์เวย์จะเขียนจดหมายเชิญให้ ในจดหมายต้องมีข้อมูลอะไรบ้างคะ
- English: My Norwegian friend will write an invitation letter for me. What information must the letter contain?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `udi-invitation-for-visitor-visa` (expected: `udi-invitation-for-visitor-visa`)

**Reply:**

> สำหรับจดหมายเชิญจากเพื่อนคนนอร์เวย์ ควรมีข้อมูลดังนี้:
>
> 1. **เหตุผลว่าทำไมถึงได้รับเชิญ** เช่น งานแต่งงานหรืองานรวมตัวในครอบครัว
> 2. **วันที่ที่เสนอไว้สำหรับการมาเยือน** และหากเกี่ยวข้อง วันที่ของงานปาร์ตี้/การชุมนุมในครอบครัว
> 3. **ข้อมูลเกี่ยวกับผู้เชิญ** เช่น ที่ทำงานและที่อยู่ของเขา/เธอ
> 4. **ความสัมพันธ์ระหว่างคุณและผู้เชิญ** เช่น เป็นญาติกันหรือไม่
>
> *หมายเหตุ*: ถ้าผู้เชิญจะรับผิดชอบค่าใช้จ่ายด้วย ควรระบุไว้ในจดหมายนี้

**Expected facts:**

- Why the applicant is invited
- The proposed dates of the visit
- Information about the person who invites, such as their work and home
- The relationship between the applicant and the person who invites

Adviser: yes

### 6. `relationship-proof-unmarried-partner`

<!-- eval-case {"id": "relationship-proof-unmarried-partner", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ไปเยี่ยมแฟนหนุ่มที่นอร์เวย์ แต่ยังไม่ได้แต่งงานกัน ต้องใช้อะไรพิสูจน์ว่าเป็นแฟนกันจริงคะ
- English: I am visiting my boyfriend in Norway, but we are not married. What do I use to prove that we really are a couple?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-visitor-visa-checklist`, `udi-invitation-for-visitor-visa` (expected: `embassy-visitor-visa-checklist`)

**Reply:**

> เพื่อพิสูจน์ความสัมพันธ์ว่าเป็นแฟนกัน (ยังไม่แต่งงาน) คุณควรเตรียมเอกสารเหล่านี้ตามระเบียบของทางนอร์เวย์:
>
> 1. **หลักฐานการติดต่อสื่อสาร** เช่น แชทไลน์, อีเมล, โพสต์ในโซเชียลมีเดีย ที่มีระหว่างคุณและแฟน
>
> 2. **รูปถ่ายคู่ของคุณ** ที่แสดงว่า你们是ไปด้วยกัน
>
> 3. **จดหมายเชิญจากแฟนในนอร์เวย์** ซึ่งระบุความสัมพันธ์ระหว่างคุณกับเขา
>
> 4. **แบบฟอร์มการรับรองจากสปอนเซอร์ (ถ้ามี)** ถ้าแฟนของคุณจะช่วยค่างวดให้
>
> **ข้อควรจำ:** เอกสารต้องยืนยันว่าแฟนของคุณอาศัยอยู่ในนอร์เวย์จริง และคุณจะกลับไปไทยหลังเที่ยวเสร็จ เพื่อไม่ให้มองว่าคุณมาทำงานหรือนำเข้าถิ่นที่นอร์เวย์ครับ

**Expected facts:**

- A copy of the bio data page of the sponsor's passport and the sponsor's travel history
- Proof of correspondence between the applicant and the boyfriend

Adviser: yes

### 7. `fee-adult-and-child`

<!-- eval-case {"id": "fee-adult-and-child", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ฉันกับลูกสาวอายุ 8 ขวบจะยื่นวีซ่าไปนอร์เวย์ด้วยกัน ต้องจ่ายค่าวีซ่าคนละกี่ยูโรคะ
- English: My 8-year-old daughter and I will apply for Norway visas together. How many euros is the visa fee for each of us?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-online-registration`, `udi-fees` (expected: `udi-fees`, `embassy-online-registration`)

**Reply:**

> สำหรับคุณและลูกสาววัย 8 ขวบที่ต้องเดินทางด้วยกัน:
>
> 1. คุณ (ผู้ใหญ่): จ่ายค่าธรรมเนียม **90 ยูโร**
> 2. ลูกสาว (อายุ 6-12 ปี): จ่ายค่าธรรมเนียม **45 ยูโร**
>
> รวมเป็น 135 ยูโร สำหรับคนทั้ง 2 คนค่ะ

**Expected facts:**

- The visa fee is EUR 90 for an adult
- The visa fee is EUR 45 for a child aged 6 to under 12

Adviser: yes

### 8. `fee-where-to-pay-typo`

<!-- eval-case {"id": "fee-where-to-pay-typo", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ค่าธรรมเนียมวีซ่าจ่ายทีไหนคะ แล้วต้องจ่ายค่าบริการที่ VFS เพิ่มอีกมัย
- English: Where do I pay the visa fee? And do I also have to pay a service fee at VFS?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-online-registration`, `udi-fees` (expected: `embassy-online-registration`, `udi-fees`)

**Reply:**

> 1. จ่ายค่าธรรมเนียมวีซ่า (EUR 90) ออนไลน์บนเว็บไซต์ UDI เมื่อลงทะเบียนใบสมัคร
> 2. จ่ายค่าบริการเพิ่มเติมที่ศูนย์ VFS Global โดยตรงเมื่อยื่นเอกสารในวันนัดหมาย

**Expected facts:**

- The visa fee is paid online when the application is registered in the application portal
- VFS Global charges its own service fee, paid directly to VFS when the application is handed in

Adviser: yes

### 9. `processing-time-typo`

<!-- eval-case {"id": "processing-time-typo", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ยืนวีซ่าแล้วต้องรอผลกี่วันค่ะ
- English: After I hand in the visa application, how many days do I have to wait for the result?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-processing-time`, `udi-waiting-time-visitor-visa` (expected: `embassy-processing-time`, `udi-waiting-time-visitor-visa`, `embassy-visa-faq`)

**Reply:**

> ระยะเวลาในการรอผลวีซ่าขึ้นอยู่กับหลายปัจจัย:
>
> 1. **ปกติ**: ใช้เวลาสูงสุด **15 วัน** หลังสำนักงานตรวจคนเข้าเมือง (UDI) หรือสถานทูตได้รับเอกสาร
> 2. **กรณีพิเศษ**: หากยื่นผ่านประเทศอื่นหรือ UDI ตรวจสอบเพิ่มเติม อาจใช้เวลาสูงสุด **45 วัน**
> 3. **การอุทธรณ์**: กรณียื่นขออุทธรณ์จะใช้เวลาเพิ่มอีกสูงสุด **6 เดือน**
>
> *ข้อแนะนำ*: ควรยื่นคำร้องล่วงหน้าอย่างน้อย **4 สัปดาห์ก่อนเดินทาง** เพื่อป้องกันความล่าช้า

**Expected facts:**

- The processing time is normally up to 15 calendar days
- It can take up to 45 days when the application is sent to UDI or needs further examination

Adviser: yes

### 10. `when-to-apply-mixed-language`

<!-- eval-case {"id": "when-to-apply-mixed-language", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ควร apply visa ล่วงหน้ากี่ week ก่อน travel คะ แล้ว apply เร็วสุดได้กี่เดือน
- English: How many weeks before travelling should I apply for the visa, and how many months before at the earliest?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-processing-time`, `embassy-visa-faq` (expected: `embassy-processing-time`, `embassy-visa-faq`, `udi-visit-family-how-to-apply`)

**Reply:**

> แนะนำให้ยื่นขอวิซาล่วงหน้าอย่างน้อย **4 สัปดาห์** ก่อนเดินทาง
>
> ยื่นได้เร็วที่สุด: **6 เดือนก่อนวันวางแผนเดินทาง** (สำหรับนักเดินเรืออาจยื่นล่วงหน้าได้ 9 เดือน)
>
> แต่ต้องยื่นไม่เกิน **15 วันก่อนวันเดินทาง**
>
> แนะนำให้เช็คเวลาให้ดี อย่ายื่นใกล้วันเดินทางเกินไป เพราะถ้ามีเหตุฉุกเฉินอาจส่งผลกระทบกับการรับผลวิซ่าได้ครับ

**Expected facts:**

- Applying at least 4 weeks before departure is recommended
- The application can be handed in no earlier than 6 months before the trip

Adviser: yes

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

> ไม่ต้องจ่ายค่ะ เด็กอายุต่ำกว่า 6 ขวบได้รับการยกเว้นค่าธรรมเนียม

**Expected facts:**

- Children under six years do not pay a visa fee

Adviser: yes

### 12. `thai-id-hand-in-in-person`

<!-- eval-case {"id": "thai-id-hand-in-in-person", "target": "general", "checks": {"category": true, "outcome": true, "source": false, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: เลขบัตรประชาชนของฉันคือ 1234567890123 ค่ะ ต้องไปยื่นเอกสารที่ VFS ด้วยตัวเองไหม ให้น้องสาวไปแทนได้หรือเปล่า
- English: (Gives a Thai ID number.) Do I have to hand in the documents at VFS in person, or can my younger sister go instead?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source FAIL, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-online-registration` (expected: `embassy-visa-faq`)
- Dropped unknown source ids: 1

**Reply:**

> 1. ใช่ คุณต้องไปยื่นด้วยตัวเองเป็นหลัก เพราะเป็น C-visa โดยทั่วไปต้องปรากฏตัวที่ VFS Global
>
> 2. น้องสาวสามารถไปแทนได้ **เฉพาะกรณี** ที่เคยขอ Schengen visa ใน 5 ปีที่ผ่านมา และลายนิ้วมือยังใช้ได้ แล้วมีหนังสือมอบอำนาจลงลายเซ็นจากคุณให้
>
> 3. ถ้าไม่มีข้อมูลเดิม คุณต้องไปเองที่ VFS Bangkok (The Shoppes at Belle Grand Rama 9, 1st Floor)
>
> 4. ขอแนะนำให้เตรียมเอกสารล่วงหน้าก่อนไปตามนัด เพื่อไม่ให้เสียเวลา

**Expected facts:**

- In most cases the applicant must hand in the application in person at VFS
- A representative with a signed power of attorney may hand it in only if the applicant applied for a Schengen visa within the last five years (59 months) and the biometric data is still valid

Adviser: yes

### 13. `passport-validity`

<!-- eval-case {"id": "passport-validity", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: พาสปอร์ตเลข AA1234567 จะหมดอายุอีก 2 เดือน ต้องทำเล่มใหม่ก่อนยื่นวีซ่าไหมคะ
- English: (Gives a passport number.) My passport expires in 2 months. Do I need a new one before I apply for the visa?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-visitor-visa-checklist`, `eu-applying-for-schengen-visa`, `embassy-online-registration` (expected: `embassy-visitor-visa-checklist`, `embassy-hand-in-documents`, `eu-applying-for-schengen-visa`)

**Reply:**

> ตามเอกสารที่กำหนด **พาสปอร์ตต้องมีอายุใช้งานอย่างน้อย 3 เดือนหลังวันที่วางแผนจะออกจากพื้นที่เชงเก้น**
>
> ดังนั้น หากพาสปอร์ตหมดอายุในอีก 2 เดือน คุณไม่จำเป็นต้องทำเล่มใหม่ทันที **แต่ควรตรวจสอบวันเดินทาง** - ถ้าวันเดินทางของคุณอยู่ก่อนที่พาสปอร์ตจะหมดอายุ (เมื่อลบ 3 เดือนออก) ก็อาจใช้พาสปอร์ตเดิมได้ครับ
>
> คำแนะนำคือ:
> 1. ดูวันที่แผนจะออกจากเชงเก้น
> 2. นับย้อนกลับ 3 เดือนจากวันนั้น
> 3. หากพาสปอร์ตยังอยู่เกินจุดนี้ก่อนวันเดินทาง ใช้เล่มเดิมได้
>
> หากไม่แน่ใจ แนะนำให้ปรึกษาเจ้าหน้าที่วีซ่าเพื่อประเมินตามกรณีจริงของคุณครับ

**Expected facts:**

- The passport must be valid for at least three months after the planned departure from the Schengen area
- The passport must have at least two blank pages

Adviser: yes

### 14. `thanks-and-insurance-question`

<!-- eval-case {"id": "thanks-and-insurance-question", "target": "general", "checks": {"category": true, "outcome": true, "source": true, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ได้ค่ะ ขอบใจมาก อีกเรื่องนะคะ ประกันการเดินทางต้องมีวงเงินคุ้มครองขั้นต่ำเท่าไร
- English: All right, many thanks. One more thing - what is the minimum cover the travel insurance must have?
- Category: expected `general`, actual `general`
- Outcome: expected `answered`, actual `answered`
- Checks: category pass, outcome pass, expected source pass, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `embassy-necessary-documents` (expected: `embassy-necessary-documents`, `embassy-hand-in-documents`, `embassy-visitor-visa-checklist`)

**Reply:**

> ประกันเดินทางต้องมีวงเงินคุ้มครองขั้นต่ำอย่างน้อย 30,000 ยูโร หรือเทียบเท่าในสกุลเงินอื่น และต้องคุ้มครองตลอดระยะเวลาที่อยู่ในเขตเชงเก้นทุกประเทศ รวมถึงค่ารักษาพยาบาลและการส่งตัวกลับผู้ป่วย

**Expected facts:**

- The travel medical insurance must cover at least EUR 30,000
- It must be valid in all Schengen countries for the whole stay

Adviser: yes

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

Adviser: yes

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

Adviser: yes

### 17. `no-answer-pregnancy`

<!-- eval-case {"id": "no-answer-pregnancy", "target": "no_answer", "checks": {"category": true, "outcome": false, "source": false, "personal_info": true, "thai": true}, "dropped": 1} -->

- Question: ตอนนี้ตั้งท้องได้หกเดือน ยังยื่นขอวีซ่าท่องเที่ยวนอร์เวย์ได้ไหม มีเงื่อนไขพิเศษสำหรับคนท้องหรือเปล่าคะ
- English: I am six months pregnant. Can I still apply for a Norway tourist visa, and are there special conditions for pregnant women?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `answered`
- Checks: category pass, outcome FAIL, expected source FAIL, personal information pass, Thai pass
- Cited sources: `embassy-hand-in-documents`, `udi-visit-family-how-to-apply`, `embassy-necessary-documents` (expected: none)
- Dropped unknown source ids: 1

**Reply:**

> ข้อมูลในเอกสารที่คุณให้มาไม่ได้ระบุเกี่ยวกับเงื่อนไขพิเศษสำหรับคนตั้งครรภ์ในการยื่นขอวีซ่า
>
> สำหรับวีซ่าผู้เยี่ยมเยือนทั่วไป ข้อกำหนดหลักคือต้องมี:
> 1. หนังสือเดินทางที่มีอายุการใช้งานอย่างน้อย 3 เดือนหลังออกเดินทางจากเขตเชงเกน
> 2. ประกันสุขภาพการเดินทางที่ครอบคลุมอย่างน้อย 30,000 ยูโร
>
> หากต้องการข้อมูลเกี่ยวกับคนตั้งครรภ์โดยเฉพาะ แนะนำให้ติดต่อศูนย์ขอวีซ่าโดยตรงหรือ UDI เพราะเงื่อนไขอาจมีการเปลี่ยนแปลงได้

**Expected facts:**

- none

Adviser: yes

### 18. `no-answer-vaccination-certificate`

<!-- eval-case {"id": "no-answer-vaccination-certificate", "target": "no_answer", "checks": {"category": true, "outcome": false, "source": false, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ต้องมีใบรับรองการฉีดวัคซีนไปยื่นพร้อมเอกสารวีซ่าด้วยไหมคะ
- English: Do I need to hand in a vaccination certificate with my visa documents?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `answered`
- Checks: category pass, outcome FAIL, expected source FAIL, personal information pass, Thai pass
- Cited sources: `embassy-necessary-documents`, `embassy-hand-in-documents`, `embassy-visitor-visa-checklist` (expected: none)

**Reply:**

> จากเอกสารที่มีให้ **ไม่มีข้อกำหนดว่าต้องมีใบรับรองการฉีดวัคซีน** สำหรับการยื่นขอวีซ่าเยี่ยมครอบครัวหรือคู่รักในนอร์เวย์
>
> เอกสารที่จำเป็นประกอบด้วย:
> * สำเนาหนังสือเดินทาง
> * รูปถ่ายตามมาตรฐาน
> * แบบฟอร์มการสมัครออนไลน์ (Schengen.pdf)
> * ประกันสุขภาพครอบคลุมอย่างน้อย 30,000 ยูโร
>
> หากเอกสารไม่มีระบุ อาจไม่ใช่ข้อกำหนดของนอร์เวย์ หรืออาจเปลี่ยนแปลงได้ แนะนำตรวจสอบอีกครั้งเมื่อเข้ายื่นที่ VFS Global

**Expected facts:**

- none

Adviser: yes

### 19. `no-answer-interpreter-at-vfs`

<!-- eval-case {"id": "no-answer-interpreter-at-vfs", "target": "no_answer", "checks": {"category": true, "outcome": false, "source": false, "personal_info": true, "thai": true}, "dropped": 0} -->

- Question: ฉันพูดภาษาอังกฤษไม่ได้ พาล่ามไปด้วยตอนยื่นเอกสารที่ VFS ได้ไหมคะ
- English: I can't speak English. Can I bring an interpreter when I hand in my documents at VFS?
- Category: expected `general`, actual `general`
- Outcome: expected `no_answer`, actual `answered`
- Checks: category pass, outcome FAIL, expected source FAIL, personal information pass, Thai pass
- Cited sources: `embassy-visa-faq`, `udi-how-to-apply-visitor-visa` (expected: none)

**Reply:**

> จากเอกสารที่ให้มา ไม่ระบุข้อจำกัดเรื่องการพาล่ามไปด้วยในการยื่นคำขอ คุณต้องปรากฏตัวไปเองที่ศูนย์บริการวีซ่า (VFS Global) เพื่อตรวจสอบเอกสารและลงนามตามขั้นตอน
>
> หากต้องการสอบถามนโยบายของศูนย์บริการโดยตรง แนะนำให้ติดต่อ VFS โดยตรงผ่านช่องทางโทรศัพท์หรืออีเมลตามที่ระบุในเอกสารครับ

**Expected facts:**

- none

Adviser: yes

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

Adviser: yes

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

Adviser: yes

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

Adviser: yes

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

Adviser: yes

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

Adviser: yes

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

Adviser: yes

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

Adviser: yes

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

Adviser: yes

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

Adviser: yes

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

Adviser: yes

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

Adviser: yes
