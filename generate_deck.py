import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette: Professional Executive Dark Teal / Navy
    BG_COLOR = RGBColor(8, 29, 36)          # #081d24
    HEADER_COLOR = RGBColor(45, 212, 191)   # #2dd4bf (Teal/Aqua)
    WHITE_COLOR = RGBColor(255, 255, 255)   # #ffffff
    BODY_COLOR = RGBColor(203, 213, 225)    # #cbd5e1 (Soft gray/white)
    CARD_BG = RGBColor(14, 42, 53)          # #0e2a35
    CARD_BORDER = RGBColor(20, 184, 166)    # #14b8a6
    GOLD_COLOR = RGBColor(251, 191, 36)     # #fbbf24

    def add_background(slide):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = BG_COLOR
        shape.line.color.rgb = BG_COLOR
        return shape

    def add_header(slide, title_text, subtitle_text):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = HEADER_COLOR

        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.size = Pt(13)
        p2.font.color.rgb = BODY_COLOR

    def add_card(slide, left, top, width, height, title, points):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = CARD_BORDER
        shape.line.width = Pt(1)

        tf = shape.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.2)
        tf.margin_bottom = Inches(0.2)

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = WHITE_COLOR

        for pt_text in points:
            p_pt = tf.add_paragraph()
            p_pt.text = "• " + pt_text
            p_pt.font.size = Pt(12)
            p_pt.font.color.rgb = BODY_COLOR
            p_pt.space_before = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 1: TITLE SLIDE
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s1)

    tbox = s1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.3), Inches(4.8))
    tf1 = tbox.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "SRI SIDDHARTHA SCHOOL OF ENGINEERING"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = GOLD_COLOR

    p2 = tf1.add_paragraph()
    p2.text = "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING"
    p2.font.size = Pt(13)
    p2.font.color.rgb = BODY_COLOR
    p2.space_before = Pt(4)

    p3 = tf1.add_paragraph()
    p3.text = "CitizenShield"
    p3.font.size = Pt(50)
    p3.font.bold = True
    p3.font.color.rgb = HEADER_COLOR
    p3.space_before = Pt(24)

    p4 = tf1.add_paragraph()
    p4.text = "AI-Powered Civic Grievance Detection & Management System"
    p4.font.size = Pt(22)
    p4.font.color.rgb = WHITE_COLOR
    p4.space_before = Pt(6)

    p5 = tf1.add_paragraph()
    p5.text = "Smart City Governance Solution for Tumakuru City Corporation (35 Administrative Wards)"
    p5.font.size = Pt(14)
    p5.font.color.rgb = BODY_COLOR
    p5.space_before = Pt(16)

    p6 = tf1.add_paragraph()
    p6.text = "Final Year Engineering Major Project Presentation"
    p6.font.size = Pt(13)
    p6.font.bold = True
    p6.font.color.rgb = GOLD_COLOR
    p6.space_before = Pt(26)

    # -------------------------------------------------------------
    # SLIDE 2: CONTENTS (Matching User's Syllabus Slide)
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s2)
    add_header(s2, "Contents / Project Outline", "Comprehensive presentation flow following university evaluation guidelines")

    add_card(s2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Part 1: Problem & Approach", [
        "1. Introduction — What is CitizenShield?",
        "2. Problem Statement — Why do traditional portals fail?",
        "3. Literature Survey — Modern AI & Smart City Research",
        "4. Research / Project Gap — Missing AI verification & proof",
        "5. Objectives — What our system achieves",
        "6. Scope of the Project — Tumakuru City 35 wards & 4 departments"
    ])

    add_card(s2, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Part 2: Technology & Delivery", [
        "7. Proposed Methodology — Real-time AI + GIS pipeline",
        "8. System Design & Architecture — Flask, SQLite & YOLOv8",
        "9. Implementation — AI Vision, Officer Replies, 10-Stage Tracker",
        "10. Results & Discussion — 17-Step automated verification tests",
        "11. Conclusion & Future Scope — Drone & mobile integration",
        "12. References — Standards and academic citations"
    ])

    # -------------------------------------------------------------
    # SLIDE 3: 1. INTRODUCTION (Simple Plain Words)
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s3)
    add_header(s3, "1. Introduction — CitizenShield Explained Simply", "What is CitizenShield and why was it built?")

    add_card(s3, Inches(0.8), Inches(1.8), Inches(3.6), Inches(5.0), "What is CitizenShield?", [
        "It is a smart website for cities where people report problems like potholes, garbage, or pipe leaks.",
        "Instead of waiting days on a phone helpline, citizens take a photo, and the computer understands the defect automatically.",
        "It directly links citizens with municipal engineers and city officials."
    ])

    add_card(s3, Inches(4.8), Inches(1.8), Inches(3.6), Inches(5.0), "How Does it Help People?", [
        "Easy 1-minute reporting from any mobile phone or laptop.",
        "Takes the exact GPS location with zero confusion.",
        "Citizens can track their complaint step-by-step just like tracking an Amazon or Swiggy delivery parcel."
    ])

    add_card(s3, Inches(8.8), Inches(1.8), Inches(3.6), Inches(5.0), "How Does it Help Officers?", [
        "Shows an interactive map of Tumakuru with Red, Orange, and Green danger zones.",
        "Officers can reply directly to citizens with work notes.",
        "Officers MUST upload a photo after fixing the problem before closing the file."
    ])

    # -------------------------------------------------------------
    # SLIDE 4: 2. PROBLEM STATEMENT
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s4)
    add_header(s4, "2. Problem Statement — The Real Pain Points", "Why traditional municipal grievance systems are broken")

    add_card(s4, Inches(0.8), Inches(1.8), Inches(3.6), Inches(5.0), "1. Manual Confusion", [
        "Citizens don't know which government department to contact (Water Board? Road Division? Electricity?).",
        "Complaints get sent to the wrong officers, causing weeks of delays.",
        "Paper forms and phone helplines are slow and lose track of records."
    ])

    add_card(s4, Inches(4.8), Inches(1.8), Inches(3.6), Inches(5.0), "2. Fake Closures", [
        "Complaints are often marked 'Resolved' on paper without any work actually being done.",
        "Citizens have no proof and have to complain again and again.",
        "No accountability for contractors and repair crews."
    ])

    add_card(s4, Inches(8.8), Inches(1.8), Inches(3.6), Inches(5.0), "3. No Live Visibility", [
        "Senior commissioners have no live map to see where most problems are concentrated.",
        "Multiple citizens file the same pothole multiple times, wasting crew fuel and time.",
        "Citizens feel ignored because they never receive official updates."
    ])

    # -------------------------------------------------------------
    # SLIDE 5: 3. LITERATURE SURVEY & 4. PROJECT GAP
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s5)
    add_header(s5, "3. Literature Survey & 4. Project Gap", "What research says and what existing systems were missing")

    add_card(s5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "3. Existing Research & Studies", [
        "YOLO Object Detection (Redmon et al.): Proves deep neural networks detect cracks and road holes in real-time.",
        "GIS & Geolocation Systems: Show that clustering complaints within 75 meters reduces duplicate visits by 35%.",
        "E-Governance Portals (CPGRAMS, State Portals): Found that lack of feedback leads to public distrust in online portals."
    ])

    add_card(s5, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "4. The Research / Project Gap", [
        "Gap 1: Existing portals only store text; they do NOT use AI to scan the uploaded image for verification.",
        "Gap 2: No portal requires a 'Post-Repair Photo' before an officer can close a ticket.",
        "Gap 3: No real-time colour-coded danger map exists for municipal commissioners in mid-sized Indian smart cities like Tumakuru."
    ])

    # -------------------------------------------------------------
    # SLIDE 6: 5. OBJECTIVES & 6. SCOPE
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s6)
    add_header(s6, "5. Project Objectives & 6. Scope", "What we set out to build and where it operates")

    add_card(s6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "5. Main Project Objectives", [
        "1. Real AI Image Recognition: Identify Potholes, Road damage, Garbage, Water leakage, and Drainage problems.",
        "2. Geotagging & Duplicate Detection: Auto-detect GPS coordinates and alert if a complaint already exists within 75 meters.",
        "3. Live Colour-Coded Map: Green (0-3), Orange (4-7), and Red (8+) hazard sectors on Tumakuru Leaflet map.",
        "4. Officer Reply & Status Update: Direct communication between engineer and citizen with audit trails.",
        "5. 10-Stage Tracking Pipeline: Full vertical timeline showing every stage from lodgment to completion."
    ])

    add_card(s6, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "6. Scope of the Application", [
        "Territory: All 35 Municipal Wards of Tumakuru City Corporation (Ward 1 to Ward 35).",
        "Covered Directorate Departments:",
        "  • Roads & Civil Infrastructure",
        "  • Electrical & Public Lighting (BESCOM)",
        "  • Water Supply & Sewerage Board (KUWSDB)",
        "  • Solid Waste Management Cell",
        "Users: Citizens, Municipal Engineers, Municipal Commissioners."
    ])

    # -------------------------------------------------------------
    # SLIDE 7: 7. PROPOSED METHODOLOGY
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s7)
    add_header(s7, "7. Proposed Methodology — The 5-Step Workflow", "How data flows through CitizenShield from citizen to resolution")

    add_card(s7, Inches(0.8), Inches(1.8), Inches(2.2), Inches(5.0), "Step 1: Capture", [
        "Citizen snaps a photo.",
        "Browser acquires GPS coordinates.",
        "Image uploaded to Flask server."
    ])

    add_card(s7, Inches(3.2), Inches(1.8), Inches(2.2), Inches(5.0), "Step 2: AI Scan", [
        "YOLOv8 scans for potholes, cracks, or garbage.",
        "OpenCV checks water sheen.",
        "Auto-suggests category & priority."
    ])

    add_card(s7, Inches(5.6), Inches(1.8), Inches(2.2), Inches(5.0), "Step 3: Save & Map", [
        "Checked for 75m duplicates.",
        "Stored permanently in SQLite.",
        "Live zone map colour updates automatically."
    ])

    add_card(s7, Inches(8.0), Inches(1.8), Inches(2.2), Inches(5.0), "Step 4: Dispatch", [
        "Officer gets ticket.",
        "Reviews AI confidence score.",
        "Dispatches road/water crew.",
        "Sends official reply."
    ])

    add_card(s7, Inches(10.4), Inches(1.8), Inches(2.2), Inches(5.0), "Step 5: Resolve", [
        "Crew fixes problem.",
        "Officer uploads after-repair photo.",
        "Citizen tracking timeline updates to 'Resolved'."
    ])

    # -------------------------------------------------------------
    # SLIDE 8: 8. SYSTEM DESIGN & ARCHITECTURE
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s8)
    add_header(s8, "8. System Design & Database Architecture", "The engineering building blocks powering the system")

    add_card(s8, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Core Technology Stack", [
        "Backend: Python Flask 3.1.3 (Fast, lightweight REST API)",
        "Server: Multi-threaded Waitress WSGI Server (Enterprise ready)",
        "Database: SQLite 3 with Foreign Key Enforcement & Migrations",
        "AI Deep Learning: Ultralytics YOLOv8 + OpenCV 5.0",
        "Frontend: HTML5, CSS3, Modern ES6 JavaScript Modules",
        "Maps & GIS: Leaflet.js with OpenStreetMap Tiles"
    ])

    add_card(s8, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Relational Database Vault", [
        "users: Citizen & Officer logins with salted SHA-256 hashes",
        "reports: Grievance details, coordinates, photos, status",
        "ai_detections: Detected class, confidence score, model name",
        "officer_replies: Official messages, previous & new status",
        "status_history: Immutable audit timestamps for every update",
        "notifications: Citizen in-app alert inbox with unread counts",
        "audit_logs: System security and login audit trail"
    ])

    # -------------------------------------------------------------
    # SLIDE 9: 9. IMPLEMENTATION — AI & OFFICER DIRECTIVES
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s9)
    add_header(s9, "9. Implementation — Real Features, No Shortcuts", "Actual working modules built into CitizenShield")

    add_card(s9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Module A: Real AI Vision Engine", [
        "pothole_yolov8n.pt: Deep neural segmentation trained for potholes.",
        "road_distress_yolov8n.pt: Detects transverse, longitudinal, and alligator cracks.",
        "garbage_yolov8n.pt: Identifies solid waste and commercial litter.",
        "OpenCV Spectral Analyzer: Detects water bursts & sewage pooling.",
        "Honest Fallback: If an image is not recognized, it clearly tells the citizen and allows manual selection (Zero fake predictions)."
    ])

    add_card(s9, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Module B: Officer Directives & Reply", [
        "'Reply to Citizen' Button: Directly in Officer Console.",
        "Re-route Department: Reassign from Roads to Water if needed.",
        "Urgency SLA: Set from Low (72h) to Urgent (12h).",
        "Mandatory Resolution Photo: The system strictly blocks marking a complaint as 'Resolved' unless an after-repair photo is attached.",
        "Live In-App Notification: Citizen gets an instant bell alert."
    ])

    # -------------------------------------------------------------
    # SLIDE 10: 9. IMPLEMENTATION — CITIZEN TRACKING & MAP
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s10)
    add_header(s10, "9. Implementation — 10-Stage Milestone Tracker", "Transparent complaint lifecycle for citizens")

    add_card(s10, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "The 10-Stage Milestone Pipeline", [
        "1. Complaint Submitted (Permanently recorded in SQLite)",
        "2. Received by Municipal Department (Control room verified)",
        "3. Department Assigned (Roads, BESCOM, Water, Sanitation)",
        "4. Officer Assigned (Field engineer designated)",
        "5. Field Inspection Started (On-site defect check)",
        "6. Inspection Completed (Technical note generated)",
        "7. Work Order Issued (Contractor ticket approved)",
        "8. Repair Work Started (Asphalt / jetting pump deployed)",
        "9. Complaint Resolved (Post-repair verification photo uploaded)",
        "10. Citizen Feedback Received (Closure confirmed)"
    ])

    add_card(s10, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Live Colour-Coded Zone Radar", [
        "Green Zone: 0 to 3 active complaints (Normal low-hazard area)",
        "Orange Zone: 4 to 7 active complaints (Medium priority zone)",
        "Red Zone: 8+ active complaints (High emergency risk zone)",
        "Auto-Recalculation: Whenever an officer resolves a complaint, the zone count drops and colour updates automatically.",
        "Clickable Sectors: Clicking any zone opens all complaints inside it."
    ])

    # -------------------------------------------------------------
    # SLIDE 11: 10. RESULTS & DISCUSSION
    # -------------------------------------------------------------
    s11 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s11)
    add_header(s11, "10. Results & Discussion — Automated Testing", "Proven 17-step end-to-end testing with zero errors")

    add_card(s11, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Test Suite Execution (test_full_workflow.py)", [
        "Test 1: Citizen registered successfully (SQLite user ID generated).",
        "Test 2 & 3: YOLOv8 model detected Road Damage with 75% confidence.",
        "Test 4 & 5: Complaint saved in SQLite (Tracking ID: CS-2026-66737).",
        "Test 6 & 7: Municipal Engineer retrieved report with evidence photo.",
        "Test 8, 9, 10: Officer sent reply & updated status to 'In Progress'.",
        "Test 11, 12, 13: Citizen tracking showed new status & latest reply.",
        "Test 14: Citizen received real-time in-app notification alert."
    ])

    add_card(s11, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "Resolution & Security Verification", [
        "Test 15: Officer marked 'Resolved' with required after-repair photo.",
        "Test 16: Citizen dossier displayed 'Resolved' badge + repair photo.",
        "Test 17: Security Check — When a different citizen tried to view this private complaint, the system returned HTTP 403 Forbidden.",
        "Performance Summary:",
        "  • AI Inference Time: ~180 milliseconds",
        "  • Database Query Time: < 5 milliseconds",
        "  • Test Suite Pass Rate: 100% (17 / 17 Passed)"
    ])

    # -------------------------------------------------------------
    # SLIDE 12: 11. CONCLUSION, FUTURE SCOPE & REFERENCES
    # -------------------------------------------------------------
    s12 = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(s12)
    add_header(s12, "11. Conclusion, Future Scope & 12. References", "Final summary and academic citations")

    add_card(s12, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "11. Conclusion & Future Scope", [
        "Conclusion: CitizenShield successfully replaces slow, paper-based municipal systems with an AI-driven, transparent e-governance platform.",
        "Ensures zero false closures through mandatory photographic repair verification.",
        "Future Enhancements:",
        "  • Native Android/iOS App with on-device camera inference.",
        "  • Automated Drone Video Feeds scanning roads for cracks.",
        "  • WhatsApp Chatbot integration for elderly citizens."
    ])

    add_card(s12, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), "12. References", [
        "1. Ultralytics YOLOv8 Deep Learning Computer Vision Architecture (2024).",
        "2. Redmon et al., 'You Only Look Once: Unified, Real-Time Object Detection', IEEE CVPR.",
        "3. Leaflet.js Interactive Mapping APIs & OpenStreetMap Geolocation Protocols.",
        "4. Miguel Grinberg, 'Flask Web Development', O'Reilly Media.",
        "5. Centralized Public Grievance Redress & Monitoring System (CPGRAMS) Guidelines, DARPG, Govt of India."
    ])

    output_path = os.path.abspath("CitizenShield_Major_Project_Presentation.pptx")
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_deck()
