#!/usr/bin/env python3
"""Turn the Gantt sheet (CSV export of the "Gantt Date Shifted" tab) into the
two Gantt tables of chapter 1, laid out like the progress report example:
one table per semester, weekly columns grouped by month, shaded weeks, owner.

Usage:
    python3 tools/gantt_to_latex.py <exported-sheet.csv> > chapters/gantt-tables.tex

The export may hold several tabs (each starting with "## Sheet name: ..."); the
first tab is used unless --sheet "<name>" is given.
"""
import csv, sys, re, datetime as dt, argparse

OWNERS = {"1003": "กัญญ์ญาพัชร", "1029": "นาวิน", "1033": "ปัณณวิชญ์", "1040": "ภูบดินทร์", "All": "ทุกคน"}
THAI_MONTHS = {1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
               7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."}
MILESTONES = {"0": "M0: Foundation", "1": "M1: Secure Access", "2": "M2: Project Setup",
              "3": "M3: AI Design Generation", "4": "M4: Testing Space", "5": "M5: Feedback",
              "6": "M6: Stakeholder Report", "7": "M7: Pilot and Launch"}
#: Thai task names, worded as in the Task Breakdown (section 1.4.1 of the report).
#: Keyed by the sheet's ID column, or by the English task name for rows without an ID.
#: A task missing here keeps its English name and is reported on stderr.
THAI_NAMES = {
    # Documentation
    "Topic Selection": "ศึกษาค้นคว้าหัวข้อโครงงาน",
    "Project Idea document": "จัดทำเอกสาร Project Idea",
    "Literature Review": "เอกสารและงานวิจัยที่เกี่ยวข้อง",
    "Proposal Report": "จัดทำเอกสาร Proposal report",
    "Proposal [Presentation]": "นำเสนอ Proposal",
    "Semester 1 Progress Report": "จัดทำเอกสาร Progress report ภาคเรียนที่ 1",
    "Semester 1 [Presentation]": "นำเสนอ Progress ภาคเรียนที่ 1",
    "Semester 2 Progress Report": "จัดทำเอกสาร Progress report ภาคเรียนที่ 2",
    "Semester 2 [Presentation]": "นำเสนอ Progress ภาคเรียนที่ 2",
    "Final Report": "จัดทำเอกสาร Final Report",
    "Final Defense [Presentation]": "นำเสนอ Final Defense",
    # Requirements Analysis & System Design
    "Stakeholder Interview": "สัมภาษณ์ผู้มีส่วนได้ส่วนเสีย",
    "Requirements Analysis": "ระบุ Requirements",
    "Functional & Non-Functional Requirements": "ระบุ Functional & Non-Functional Requirements",
    "Use Cases & User Flow": "จัดทำ Use Cases & Sequence Diagram",
    "System Architecture": "วางโครงสร้าง System Architecture",
    "AI Workflow & Prompt Architecture": "วางโครงสร้าง AI Workflow & Prompt Architecture",
    "Database Design": "ออกแบบ Database",
    "API Design": "ออกแบบ API Design",
    "UI/UX Design (User Flow & Wireframe)": "ออกแบบ UI/UX Design (User Flow & Wireframe)",
    "System Prototype": "System prototype (PoC)",
    # M0: Foundation
    "0.1": "ระบุกลุ่มเป้าหมาย ขอบเขต และ MVP",
    "0.2": "กำหนด data model (workspace, project, story, variant, session, task, feedback, round, report)",
    "0.3": "เลือก architecture: auth, LLM provider, prototype rendering, hosting",
    "0.4": "สำรวจและเลือก design system และ UI kit",
    "0.5": "กำหนด requirements ด้าน PDPA และข้อความขอ consent",
    "0.6": "ตั้งค่า CI/CD, environments และ event analytics",
    "0.7": "การกำหนดดัชนีชี้วัดผล และแผนการดำเนินงาน",
    # M1: Secure Access
    "1.1": "จัดทำ Landing page",
    "1.2": "จัดทำ Register page",
    "1.3": "การยืนยันตัวตนผ่านอีเมล",
    "1.4": "การเข้าสู่ระบบพร้อมระบบจัดการข้อผิดพลาด",
    "1.5": "ระบบรีเซ็ตรหัสผ่าน",
    "1.6": "ระบบควบคุมการเข้าถึง",
    "1.7": "จัดทำระบบ routing ตามบทบาทของผู้ใช้",
    "1.8": "ทดสอบระบบยืนยันตัวตนและการควบคุมการเข้าถึง",
    # M2: Project Setup
    "2.1": "ระบบสร้าง workspace",
    "2.2": "ระบบสร้างโปรเจกต์",
    "2.3": "ฟอร์มกำหนดความต้องการทางการออกแบบ",
    "2.4": "ระบบจัดเก็บความต้องการทางการออกแบบเพื่อใช้เป็น reusable AI context",
    # M3: AI Design Generation
    "3.1": "การสร้าง User story และ Problem statement",
    "3.2": "เครื่องมือสร้างคำสั่งที่รวมความต้องการทางการออกแบบและ user story",
    "3.3": "การสร้าง two-alternative UI",
    "3.4": "การปรับปรุง UI (Chat-based)",
    "3.5": "การดูตัวอย่างรูปแบบหน้าจอ",
    "3.6": "การอนุมัติและมอบหมายงานให้ผู้เข้าร่วมทดสอบ",
    "3.7": "การเริ่มเซสชันการทดสอบ",
    "3.8": "ชุดข้อมูลสำหรับการประเมินคุณภาพผลลัพธ์ของ AI",
    # M4: Testing Space
    "4.1": "การเข้าสู่เซสชันด้วยรหัสหรือลิงก์ พร้อมระบบตรวจสอบความถูกต้องของอายุการใช้งาน",
    "4.2": "สถานะสิ้นสุดของระบบ",
    "4.3": "การขอความยินยอมตามกฎหมายคุ้มครองข้อมูลส่วนบุคคล (PDPA) พร้อมระบบบันทึกประวัติการให้ความยินยอม",
    "4.4": "การกำหนดผู้ใช้งานให้เข้าร่วมการทดสอบ",
    "4.5": "การแนะนำการใช้งานเครื่องมือทดสอบสำหรับผู้ใช้ใหม่",
    "4.6": "ระบบทำภารกิจพร้อมการบันทึกพฤติกรรมการโต้ตอบของผู้ใช้",
    "4.7": "การทบทวนหน้าจอหลังทำภารกิจและคำถามเฉพาะจุด",
    "4.8": "การแสดงความคิดเห็น การระบุตำแหน่งคอมโพเนนต์ การแสดงความคิดเห็นทั้งหน้าจอ หรือการข้ามการแสดงความคิดเห็น",
    "4.9": "วงจรการทำภารกิจที่เหลืออยู่จนกระทั่งสิ้นสุดการทดสอบของผู้ทดสอบ",
    "4.10": "การทดสอบข้ามเบราว์เซอร์",
    # M5: Feedback
    "5.1": "การติดตามเซสชันการทดสอบ",
    "5.2": "การรวบรวมและประมวลผลฟีดแบ็ก",
    "5.3": "การวิเคราะห์ด้วย AI การหาประเด็นหลัก การติดป้ายกำกับ และการสรุปผล",
    "5.4": "หน้าจอเพื่อการตรวจสอบของนักออกแบบ การเปลี่ยนป้ายกำกับ การรวม การแยก การจดบันทึก และการทำเครื่องหมาย \"ไม่แก้ไข\" พร้อมระบุเหตุผล",
    "5.5": "วงจรการอนุมัติหรือการปรับปรุงแก้ไข",
    "5.6": "การนำฟีดแบ็กที่เลือกไปป้อนเป็นพรอมต์สำหรับรอบถัดไป",
    "5.7": "การตัดสินใจสิ้นสุดเซสชัน การทำเวอร์ชันของรอบการทำงาน และประวัติการทำงาน",
    "5.8": "การทดสอบวงจรการทำงานแบบต้นทางถึงปลายทาง",
    # M6: Stakeholder Report
    "6.1": "รายการโปรเจกต์ (แบบอ่านอย่างเดียว สำหรับงานที่อนุมัติแล้วเท่านั้น)",
    "6.2": "มุมมองผู้ใช้งานที่แตกต่างกัน",
    "6.3": "การส่งมอบงานให้นักพัฒนา",
    "6.4": "สถานะสำหรับผู้จัดการโครงการ",
    "6.5": "เครื่องมือสร้างรายงาน",
    "6.6": "การจัดทำรายงานเฉพาะสำหรับแต่ละบทบาท",
    "6.7": "การส่งออกและการแชร์รายงาน",
    # M7: Pilot and Launch
    "7.1": "ทดสอบ E2E และ UAT",
    "7.2": "ทดสอบ Security test และ PDPA audit",
    "7.3": "ทดสอบ Load test ด้วยผู้ทดสอบพร้อมกัน",
    "7.4": "ทดลองใช้งานกับทีมจริง 2–3 ทีมและเก็บข้อเสนอแนะ",
    "7.5": "จัดทำคู่มือการใช้งาน การเริ่มต้นใช้งาน และกระบวนการสนับสนุน",
    "7.6": "ติดตามระบบและแดชบอร์ดตัวชี้วัดทางธุรกิจ",
    "7.7": "Go live",
}

SEMESTERS = [("1", dt.date(2026, 7, 1), dt.date(2026, 12, 31)),
             ("2", dt.date(2027, 1, 1), dt.date(2027, 5, 31))]


def tex(s):
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("$", r"\$"), ("~", r"\~{}")]:
        s = s.replace(a, b)
    s = s.replace(">", r"\textgreater{}").replace("<", r"\textless{}")
    return re.sub(r"\[(.*?)\]", r"(\1)", s)  # [Presentation] -> (Presentation)


def load(path, sheet):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    starts = [i for i, r in enumerate(rows) if r and r[0].startswith("## Sheet name")]
    if starts:
        pick = 0
        if sheet:
            pick = [k for k, i in enumerate(starts) if rows[i][0].split(":", 1)[1].strip() == sheet][0]
        a = starts[pick]
        b = starts[pick + 1] if pick + 1 < len(starts) else len(rows)
        rows = rows[a:b]
    hi = [i for i, r in enumerate(rows) if "Phase / Milestone" in r][0]
    head = rows[hi]
    col = {name: head.index(name) for name in ["Phase / Milestone", "ID", "Task", "Owner", "Start", "Due Date"]}
    tasks, phase = [], None
    for r in rows[hi + 1:]:
        if len(r) <= col["Due Date"] or not r[col["Task"]].strip():
            continue
        if r[col["Phase / Milestone"]].strip():
            phase = r[col["Phase / Milestone"]].strip()
        tid = r[col["ID"]].strip()
        name = MILESTONES.get(tid.split(".")[0], phase) if tid else phase.split(" - ")[0]
        try:
            s = dt.datetime.strptime(r[col["Start"]].strip(), "%d %b %Y").date()
            e = dt.datetime.strptime(r[col["Due Date"]].strip(), "%d %b %Y").date()
        except ValueError:
            continue
        owners = [OWNERS.get(o.strip(), o.strip()) for o in r[col["Owner"]].split(",") if o.strip()]
        tasks.append(dict(phase=name, id=tid, task=r[col["Task"]].strip(), start=s, end=e,
                          owner=", ".join(owners) if owners else "--"))
    return tasks


def table(tasks, sem, first, last):
    weeks, d = [], dt.date(2026, 7, 1)  # sheet columns are weekly from 1 Jul 2026
    while d <= last:
        if d >= first:
            weeks.append(d)
        d += dt.timedelta(days=7)
    months = []
    for w in weeks:
        if months and months[-1][0] == (w.year, w.month):
            months[-1][1] += 1
        else:
            months.append([(w.year, w.month), 1])
    rows = [t for t in tasks if t["start"] <= last and t["end"] >= first]
    n = len(weeks)
    out = []
    out.append(r"\begingroup")
    out.append(r"\footnotesize")
    out.append(r"\setlength{\tabcolsep}{2pt}")
    out.append(r"\renewcommand{\arraystretch}{1.15}")
    wk = rf"\dimexpr(\linewidth-4.4cm-1.9cm-4\tabcolsep-{n+3}\arrayrulewidth)/{n}\relax"
    out.append(r"\begin{longtable}{|>{\RaggedRight\arraybackslash}p{4.4cm}|" + ("@{}" + r">{\centering\arraybackslash}p{\ganttweek}@{}|") * n
               + r">{\RaggedRight\arraybackslash}p{1.9cm}|}")
    out.append(rf"\caption{{แผนการดำเนินงานในภาคการศึกษาที่ {sem}}}\label{{tab:gantt-semester-{sem}}}\\")
    hdr = [r"\hline",
           r"\multirow{2}{*}{\textbf{รายละเอียดงาน}} & "
           + " & ".join(rf"\multicolumn{{{c}}}{{c|}}{{\textbf{{{THAI_MONTHS[m]} {y + 543 - 2500}}}}}" for (y, m), c in months)
           + r" & \multirow{2}{*}{\textbf{ผู้รับผิดชอบ}} \\",
           rf"\cline{{2-{n + 1}}}",
           " & " + " & ".join(str(i + 1) for (_, c) in months for i in range(c)) + r" & \\",
           r"\hline"]
    out += hdr + [r"\endfirsthead"]
    out.append(rf"\multicolumn{{{n + 2}}}{{l}}{{\textit{{ตารางที่ \thetable\ (ต่อ)}}}}\\")
    out += hdr + [r"\endhead"]
    phase = None
    for t in rows:
        if t["phase"] != phase:
            phase = t["phase"]
            out.append(rf"\multicolumn{{{n + 2}}}{{|l|}}{{\textbf{{{tex(phase)}}}}} \\ \hline")
        cells = []
        for w in weeks:
            on = t["start"] <= w + dt.timedelta(days=6) and t["end"] >= w
            cells.append(r"\cellcolor{ganttbar}" if on else "")
        label = THAI_NAMES.get(t["id"] or t["task"])
        if label is None:
            label = t["task"]
            print(f"warning: no Thai name for {t['id'] or t['task']!r}; kept the English name", file=sys.stderr)
        out.append(tex(label) + " & " + " & ".join(cells) + " & " + tex(t["owner"]) + r" \\ \hline")
    out.append(r"\end{longtable}")
    out.append(r"\endgroup")
    return "\n".join(out).replace(r"\ganttweek", wk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--sheet")
    a = ap.parse_args()
    tasks = load(a.csv, a.sheet)
    print("% !TeX root = ../report.tex")
    print("% Generated by tools/gantt_to_latex.py from the Gantt sheet. Edit the sheet and regenerate,")
    print("% rather than editing this file by hand.")
    for sem, first, last in SEMESTERS:
        print(table(tasks, sem, first, last))
        print()


if __name__ == "__main__":
    main()
