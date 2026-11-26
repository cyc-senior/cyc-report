# CYC Report

รายงานโครงงาน **CYC: AI-Driven Platform for UX/UI Development Life Cycle**
ใช้ template `cpe-thesis-th` ของภาควิชาวิศวกรรมคอมพิวเตอร์ มจธ.

## โครงสร้างโฟลเดอร์

```
cyc-report/
├── report.tex                  ← ไฟล์หลัก คอมไพล์ไฟล์นี้
├── cpe-thesis-th.cls           ← template ภาษาไทย (ต้องอยู่ที่ root)
├── cpe-thesis-en.cls           ← template ภาษาอังกฤษ
│
├── config/
│   ├── preamble.tex            ← packages, ฟอนต์, ระยะขอบ, caption, macro
│   └── report-info.tex         ← ชื่อโครงงาน ชื่อผู้จัดทำ อาจารย์ที่ปรึกษา
│
├── chapters/                   ← เนื้อหา แก้ที่นี่
│   ├── 00-frontmatter.tex      ← หน้าปก บทคัดย่อ สารบัญ คำศัพท์
│   ├── 01-introduction.tex     ← บทที่ 1 บทนำ
│   ├── 02-literature-review.tex← บทที่ 2 ทฤษฎีและงานที่เกี่ยวข้อง
│   ├── 03-methodology.tex      ← บทที่ 3 วิธีการดำเนินงาน
│   ├── 04-results.tex          ← บทที่ 4 ผลการดำเนินงาน (ยังไม่เขียน)
│   ├── 05-conclusion.tex       ← บทที่ 5 บทสรุป (ยังไม่เขียน)
│   └── appendix.tex            ← ภาคผนวก
│
├── figures/                    ← รูปภาพ แยกตามบท
│   ├── common/                 ← โลโก้ ฯลฯ
│   ├── ch1-introduction/
│   ├── ch2-literature-review/
│   ├── ch3-methodology/
│   └── unused/                 ← รูปเวอร์ชันเก่า / ไฟล์ต้นฉบับ (svg) ที่ยังไม่ได้ใช้
│
├── bib/                        ← cyc.bib (รายการอ้างอิง) + ไฟล์ .bst
├── fonts/                      ← TH Sarabun New, Courier Prime
├── packages/                   ← .sty เสริม (listings golang/yaml, compat)
└── archive/                    ← draft เก่า เก็บไว้ดูอ้างอิง ไม่ได้ใช้คอมไพล์
```

## วิธีแก้รายงาน

- แก้เนื้อหาบทไหน → เปิดไฟล์ใน `chapters/`
- เพิ่มรูป → วางใน `figures/chX-.../` แล้วอ้างด้วย path จาก root เช่น `figures/ch3-methodology/UC-1.png`
- เพิ่มบทใหม่ → สร้างไฟล์ใน `chapters/` แล้วเพิ่ม `\input{chapters/ชื่อไฟล์}` ใน `report.tex`
- เพิ่มรายการอ้างอิง → `bib/cyc.bib`

## Build PDF

ต้องใช้ **XeLaTeX + Biber** (Overleaf: ตั้ง Compiler เป็น XeLaTeX, Main document เป็น `report.tex`)

```bash
latexmk -xelatex report.tex
# หรือ
xelatex report.tex && biber report && xelatex report.tex && xelatex report.tex
```

### VS Code (macOS)

1. ติดตั้ง TeX: `brew install --cask mactex-no-gui` (มี xelatex, biber, latexmk และ biblatex มาให้ครบ) แล้วเปิด Terminal ใหม่
2. ติดตั้งส่วนขยาย **LaTeX Workshop** (VS Code จะแนะนำให้เองตอนเปิดโฟลเดอร์นี้)
3. เปิดโฟลเดอร์ `cyc-report` ใน VS Code แล้วกด Save ไฟล์ .tex ไฟล์ไหนก็ได้ ระบบจะ build `report.tex` ให้อัตโนมัติ
   (หรือสั่งเองด้วย `⌥⌘B`; ดู PDF ได้ด้วย `⌥⌘V`)

ค่าที่ใช้ build อยู่ใน `.latexmkrc` และ `.vscode/settings.json` ส่วนไฟล์ใน `chapters/` และ `config/` มีบรรทัด `% !TeX root = ../report.tex` อยู่บนสุด เวลา build จากไฟล์บทจึงคอมไพล์ทั้งเล่มให้เลย

ไฟล์ draft ใน `archive/` ถ้าจะคอมไพล์ให้ copy ออกมาไว้ที่ root ก่อน
