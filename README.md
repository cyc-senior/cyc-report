# CYC Report

รายงานโครงงาน **CYC: AI-Driven Platform for UX/UI Development Life Cycle**
ใช้ template `cpe-thesis-th` ของภาควิชาวิศวกรรมคอมพิวเตอร์ มจธ.

codebase เดียว ออกรายงานได้ 4 เล่ม:

| ไฟล์หลัก | เล่ม | สถานะ |
|---|---|---|
| `proposal.tex` | รายงานเล่มแรก (ข้อเสนอโครงงาน) | ส่งแล้ว ห้ามแก้ (เนื้อหาอยู่ใน `reports/proposal/`) |
| `progress-sem1.tex` | รายงานความก้าวหน้า ภาคการศึกษาที่ 1 | **เล่มปัจจุบัน** |
| `progress-sem2.tex` | รายงานความก้าวหน้า ภาคการศึกษาที่ 2 | โครงชั่วคราว (รอตัวอย่าง PDF) |
| `final.tex` | ปริญญานิพนธ์ฉบับสมบูรณ์ | โครงชั่วคราว (รอตัวอย่าง PDF) |

กติกาและขั้นตอนทั้งหมด (สำหรับคนและ AI agent) อยู่ใน [AGENTS.md](AGENTS.md)

## โครงสร้างโฟลเดอร์

```
cyc-report/
├── proposal.tex progress-sem1.tex progress-sem2.tex final.tex
│                               ← ไฟล์หลักของแต่ละเล่ม: เลือก style, front matter และลำดับไฟล์เนื้อหา
├── cpe-thesis-th.cls           ← template ภาษาไทย (ต้องอยู่ที่ root)
├── config/
│   ├── preamble.tex            ← packages, ฟอนต์, ขนาดตัวอักษร (ใช้ร่วมกัน)
│   ├── report-info.tex         ← ชื่อโครงงาน ผู้จัดทำ อาจารย์ที่ปรึกษา กรรมการ
│   ├── bibliography.tex        ← เอกสารอ้างอิง
│   └── styles/                 ← layout ของแต่ละแบบ: progress.tex, final.tex
├── frontmatter/                ← หน้าปก หน้าลายเซ็น บทคัดย่อ สารบัญ (layout) + ลำดับหน้าของแต่ละเล่ม
├── content/                    ← เนื้อหาทั้งหมด แก้ที่นี่ (1 ไฟล์ = 1 หัวข้อ)
│   ├── abstract/ glossary.tex acknowledgement.tex appendix.tex
│   ├── ch1/ ch2/ ch3/          ← ใช้ร่วมกันทุกเล่ม (ch3/development-sem1, -sem2 แยกตามเทอม)
│   ├── ch4/sem1/ ch4/sem2/ ch4/final/
│   └── ch5/                    ← เฉพาะเล่ม final
├── reports/proposal/           ← เนื้อหาเล่มแรกที่ส่งไปแล้ว (frozen)
├── figures/<บท>/               ← รูปภาพ
├── bib/ fonts/ packages/
├── tools/                      ← pdf_outline.py (วัด layout จาก PDF ตัวอย่าง), gantt_to_latex.py, er_diagram.py
└── archive/                    ← draft เก่า ไม่ได้ใช้คอมไพล์
```

## วิธีแก้รายงาน

- แก้เนื้อหา → เปิดไฟล์ใน `content/` (ชื่อไฟล์บอกหัวข้อ)
- เพิ่มหัวข้อใหม่ → สร้างไฟล์ใน `content/chX/` แล้วเพิ่ม `\input{content/chX/ชื่อไฟล์}` ในไฟล์หลักของเล่มที่ต้องการ
- เนื้อหาที่ต่างกันตามเล่ม → แยกไฟล์ (เช่น `content/ch4/sem2/`) อย่าใช้ `\if`
- เพิ่มรูป → `figures/chX-.../` แล้วอ้างด้วย path จาก root เช่น `figures/ch3-methodology/UC-1.png`
- เพิ่มรายการอ้างอิง → `bib/cyc.bib`
- ส่วนที่ยังไม่ได้เขียน → `\todo{...}` (ขึ้นตัวแดงใน PDF)
- **ห้าม commit PDF ที่ root** (`.gitignore` กันไว้แล้ว)

## Build PDF

ต้องใช้ **XeLaTeX + Biber**

```bash
latexmk                    # เล่มปัจจุบัน (progress-sem1)
latexmk final.tex          # เลือกเล่ม
```

- **GitHub Actions:** แท็บ Actions → **Build report PDF** → Run workflow → เลือกเล่ม (หรือ `all`) → โหลด PDF จาก Artifacts
  ทุก push/PR จะ build เล่มปัจจุบันให้อัตโนมัติ
- **Overleaf:** ตั้ง Compiler เป็น XeLaTeX และตั้ง Main document เป็นไฟล์หลักของเล่มที่ต้องการ

### VS Code

1. ติดตั้ง TeX (macOS: `brew install --cask mactex-no-gui`, Windows: TeX Live หรือ MiKTeX) ซึ่งมี xelatex, biber, latexmk
2. ติดตั้งส่วนขยาย **LaTeX Workshop**
3. กด Save ไฟล์ .tex ไหนก็ได้ จะ build เล่มที่ระบุไว้ในบรรทัด `% !TeX root = ...` บนสุดของไฟล์นั้น

ค่าที่ใช้ build อยู่ใน `.latexmkrc` และ `.vscode/settings.json`
