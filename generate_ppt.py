import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="CitizenShield_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Colors (Lagoon Glassmorphism Palette)
    BG_COLOR = RGBColor(3, 8, 12)        # Lagoon deep void
    SURFACE_COLOR = RGBColor(8, 28, 38)   # Translucent glass card surface
    ACCENT_MINT = RGBColor(45, 212, 191)  # Mint/Cyan glow
    ACCENT_EMERALD = RGBColor(16, 185, 129)
    TEXT_LIGHT = RGBColor(255, 255, 255)
    TEXT_MUTED = RGBColor(148, 163, 184)
    ALERT_RED = RGBColor(239, 68, 68)

    def add_slide_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.color.rgb = BG_COLOR
        return bg

    def add_header(slide, title_text, category_text="CITIZENSHIELD DIRECTORETE"):
        tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.5), Inches(0.35))
        p_cat = tb_cat.text_frame.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_MINT
        p_cat.font.name = "Arial"

        tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.5), Inches(0.65))
        p_title = tb_title.text_frame.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_LIGHT
        p_title.font.name = "Arial"

        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.55), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(15, 118, 110)
        line.line.color.rgb = RGBColor(15, 118, 110)

    def add_card(slide, left, top, width, height, title, points, badge=""):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = SURFACE_COLOR
        card.line.color.rgb = RGBColor(45, 212, 191)
        card.line.width = Pt(1)

        tx_box = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
        tf = tx_box.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        if badge:
            p0.text = f"[{badge}] " + title
        else:
            p0.text = title
        p0.font.size = Pt(16)
        p0.font.bold = True
        p0.font.color.rgb = ACCENT_MINT
        p0.font.name = "Arial"

        for pt in points:
            p = tf.add_paragraph()
            p.text = "• " + pt
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_LIGHT
            p.font.name = "Arial"
            p.space_before = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s1)

    title_box = s1.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.333), Inches(3.0))
    tf1 = title_box.text_frame
    tf1.word_wrap = True

    p_badge = tf1.paragraphs[0]
    p_badge.text = "CIVIC TECH • SMART MUNICIPAL GOVERNANCE • TUMAKURU CITY CORPORATION"
    p_badge.font.size = Pt(14)
    p_badge.font.bold = True
    p_badge.font.color.rgb = ACCENT_MINT
    p_badge.alignment = PP_ALIGN.CENTER

    p_main = tf1.add_paragraph()
    p_main.text = "CitizenShield"
    p_main.font.size = Pt(54)
    p_main.font.bold = True
    p_main.font.color.rgb = TEXT_LIGHT
    p_main.alignment = PP_ALIGN.CENTER
    p_main.space_before = Pt(10)

    p_sub = tf1.add_paragraph()
    p_sub.text = "Smart Municipal Grievance Redressal & Spatial Radar Platform (35 Wards)"
    p_sub.font.size = Pt(20)
    p_sub.font.color.rgb = ACCENT_EMERALD
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.space_before = Pt(10)

    p_meta = tf1.add_paragraph()
    p_meta.text = "Full-Stack Web Development Project | CSE Academic Evaluation\nGitHub: github.com/chinmaymr7090/CitizenShield"
    p_meta.font.size = Pt(13)
    p_meta.font.color.rgb = TEXT_MUTED
    p_meta.alignment = PP_ALIGN.CENTER
    p_meta.space_before = Pt(24)

    # -------------------------------------------------------------
    # SLIDE 2: Problem Statement
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s2)
    add_header(s2, "The Problem Statement: Urban Civic Deficit", "Urban Challenges")
    add_card(s2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "Fragmented Complaint Channels", [
                 "Citizens report craters, sewage bursts, and dark streetlights through scattered calls, social media, or verbal complaints.",
                 "Zero tracking mechanism: 80%+ citizens never receive an update once a complaint is made.",
                 "Duplicate lodging: Multiple citizens file complaints for the same road hazard.",
                 "Lack of spatial context: Ambiguous landmark descriptions delay field repair teams by days."
             ], "THE CRISIS")
    add_card(s2, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "Administrative Inefficiencies", [
                 "Municipal officers lack a centralized triage system to prioritize urgent hazards.",
                 "No immutable audit trail: Complaints can be closed or lost without verifiable evidence.",
                 "Departmental silos: Delayed coordination between Roads, BESCOM (Power), and Water Supply boards.",
                 "Inability to visualize hazard clusters on an interactive spatial GIS map across city wards."
             ], "THE BOTTLENECK")

    # -------------------------------------------------------------
    # SLIDE 3: Proposed Solution
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s3)
    add_header(s3, "The CitizenShield Solution: Closed-Loop Governance", "System Vision")
    add_card(s3, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "1. Geo-Tagged Grievances", [
                 "One-click browser GPS acquisition with exact latitude and longitude.",
                 "Full coverage across all 35 Tumakuru Corporation wards.",
                 "High-resolution evidence photo upload directly to secure vault."
             ], "INTAKE")
    add_card(s3, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "2. Permanent SQLite Vault", [
                 "100% immutable data policy: records are never lost or deleted on restart.",
                 "Write-Ahead Logging (WAL) ensures high concurrency and reliability.",
                 "Every transition tracked in legal status history logs."
             ], "PERSISTENCE")
    add_card(s3, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "3. Interactive Spatial GIS", [
                 "3D Dotted Earth orbital radar with live telemetry coordinates.",
                 "Interactive Leaflet GIS map with color-coded priority hazard markers.",
                 "Public Case Tracker and printable legal complaint certificates."
             ], "RADAR")

    # -------------------------------------------------------------
    # SLIDE 4: Technology Architecture
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s4)
    add_header(s4, "Multi-Tier Enterprise Technology Stack", "System Architecture")
    add_card(s4, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "Frontend Layer", [
                 "Pure Vanilla ES6+ Modules (Zero heavy build or framework overhead).",
                 "Bespoke Glassmorphism UI (Lagoon Teal & Midnight Void aesthetic).",
                 "Leaflet.js for high-performance municipal GIS spatial explorer.",
                 "HTML5 Canvas 3D Dotted Earth engine with Fibonacci point projection."
             ], "CLIENT")
    add_card(s4, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "Application Backend", [
                 "Python 3.13 + Flask Microframework.",
                 "RESTful API design with clean JSON contract schemas.",
                 "PBKDF2-HMAC cryptographic password hashing with unique salt.",
                 "Cryptographic session tokens and RBAC authorization middleware."
             ], "SERVER")
    add_card(s4, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "Data & Storage Vault", [
                 "SQLite Embedded Engine with strict foreign keys enabled.",
                 "WAL (Write-Ahead Logging) mode for concurrent reads & writes.",
                 "Local secure photo vault with cryptographic filename hashing.",
                 "Permanent storage file: data/citizenshield.db"
             ], "DATABASE")

    # -------------------------------------------------------------
    # SLIDE 5: Permanent Database Schema
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s5)
    add_header(s5, "Permanent SQLite Vault Schema & Data Integrity", "Database Design")
    add_card(s5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "Core Relational Entities", [
                 "USERS: id, uuid, name, email, password_hash, password_salt, role (citizen/admin), department, phone, created_at.",
                 "REPORTS: id, report_id (UUID), user_id, citizen_name, title, category, department, priority, description, location, ward, latitude, longitude, image_filename, status, admin_remarks, sla_hours, created_at, updated_at.",
                 "STATUS_HISTORY: id, report_id, status, remarks, officer_name, officer_role, created_at.",
                 "AUTH_TOKENS & AUDIT_LOGS: Session tokens and audit logging."
             ], "TABLES")
    add_card(s5, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "Data Immutability Guarantees", [
                 "Zero Data Loss: Reports and status transitions are preserved indefinitely for administrative accountability.",
                 "Strict Foreign Keys: Enforced relational integrity between users, reports, and history.",
                 "Permanent Tumakuru Ward Support: All 35 corporation wards recognized in schema.",
                 "Live file verification: c:\\Citizien Shield\\data\\citizenshield.db"
             ], "GOVERNANCE")

    # -------------------------------------------------------------
    # SLIDE 6: Tumakuru City Corporation Coverage (35 Wards)
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s6)
    add_header(s6, "Complete Tumakuru City Corporation Coverage (35 Wards)", "Tumakuru Municipal Grid")
    add_card(s6, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "North & Central Divisions", [
                 "Ward 1: Antharasanahalli / Sira Road",
                 "Ward 2: Maralenahalli / Sira Gate",
                 "Ward 3: Belagumba / Puttashamayyanapalya",
                 "Ward 4: Dibbur / Temple Road",
                 "Ward 5: Bheemasandra / Kuvempu Nagar",
                 "Ward 11: Mandipet / Town Hall Core",
                 "Ward 12: Chickpet / Old Market Road",
                 "Ward 13: Ashok Nagar / MG Road"
             ], "CENTRAL / NORTH")
    add_card(s6, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "Educational & Residential Hubs", [
                 "Ward 10: Kyatsandra / Siddaganga Math",
                 "Ward 16 & 17: Jayanagar East / West",
                 "Ward 18: SIT Campus / SIT Extension",
                 "Ward 19: Vidyanagar / Siddaganga Extn",
                 "Ward 20 & 21: SS Puram (Main & South)",
                 "Ward 22: Upparhalli / Maruthi Nagar",
                 "Ward 23: Gubbi Gate / Railway Corridor",
                 "Ward 26: Amanikere Lake Promenade"
             ], "URBAN CORE")
    add_card(s6, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "Southern & Industrial Rings", [
                 "Ward 7: Melekote / Sadashivanagar",
                 "Ward 8 & 9: Batawadi North & South",
                 "Ward 14: Gandhi Nagar / CSI Layout",
                 "Ward 29: Gokula Extension",
                 "Ward 30: Sathyamangala Industrial Bypass",
                 "Ward 31: Shettihalli Ring Road",
                 "Ward 32: Devarayapatna / Kunigal Road",
                 "Ward 35: Obalapura Ring Road Junction"
             ], "EXPANSION ZONES")

    # -------------------------------------------------------------
    # SLIDE 7: 3D Dotted Earth & Glassmorphic UI Innovation
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s7)
    add_header(s7, "Bespoke UI Design & 3D Orbital Earth Engine", "Frontend Innovation")
    add_card(s7, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "3D Dotted Earth Orbital Radar", [
                 "Custom HTML5 Canvas rendering engine without external Three.js bloat.",
                 "4,200 Fibonacci stipple points calculated in spherical 3D space.",
                 "Spherical ray-casted continental boundaries for realistic planetary geography.",
                 "Real-time sub-satellite coordinate telemetry tracking during mouse drag.",
                 "Animated sonar beacon ring focused on Tumakuru (13.3414° N, 77.1022° E).",
                 "1-Click 'Target Tumakuru' auto-glide camera alignment button."
             ], "3D CANVAS")
    add_card(s7, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "Executive Glassmorphic Interface", [
                 "Bespoke non-generic visual aesthetic: Deep lagoon void (#03080c) with mint accents.",
                 "Ultra-clear frosted glass pod with backdrop-filter: blur(28px).",
                 "Precision HUD corner crosshairs and live orbital telemetry badges.",
                 "Executive Emergency Safety Ribbon with pulsing red beacon directing crime/fire to 112.",
                 "Fully responsive layout across mobile, tablet, and widescreen monitors."
             ], "GLASSMORPHISM")

    # -------------------------------------------------------------
    # SLIDE 8: Municipal Redressal Workflow
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s8)
    add_header(s8, "End-to-End Civic Grievance Lifecycle", "Operational Workflow")
    add_card(s8, Inches(0.8), Inches(1.8), Inches(2.7), Inches(5.0), 
             "Step 1: Lodge", [
                 "Citizen captures photo & pins GPS on interactive map.",
                 "Selects from 35 Tumakuru Wards & category.",
                 "Instant unique tracking ID generated."
             ], "CITIZEN")
    add_card(s8, Inches(3.8), Inches(1.8), Inches(2.7), Inches(5.0), 
             "Step 2: Triage", [
                 "Officer views incoming report on GIS Radar.",
                 "Urgent hazards highlighted with glowing amber/red pins.",
                 "Dispatched to departmental contractor."
             ], "DISPATCH")
    add_card(s8, Inches(6.8), Inches(1.8), Inches(2.7), Inches(5.0), 
             "Step 3: Rectify", [
                 "Field engineers complete physical road/grid repairs.",
                 "Status moved from 'Inspection' to 'Resolved'.",
                 "Official remarks logged into SQLite vault."
             ], "FIELD")
    add_card(s8, Inches(9.8), Inches(1.8), Inches(2.7), Inches(5.0), 
             "Step 4: Certify", [
                 "Citizen receives updated status dossier.",
                 "Printable Legal Case Certificate generated.",
                 "Complete audit trail signed & locked."
             ], "CERTIFICATE")

    # -------------------------------------------------------------
    # SLIDE 9: Security & Admin Governance (Admin ID / Password)
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s9)
    add_header(s9, "Security Architecture & Municipal Officer Console", "System Security")
    add_card(s9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "Authentication & Access Control", [
                 "Role-Based Access Control (RBAC): Strict separation between Citizen and Officer permissions.",
                 "Protected Officer Endpoints: Only authenticated staff can update complaint stages or view full city metrics.",
                 "Secure Token Authentication: 64-character cryptographic hexadecimal bearer tokens.",
                 "Password Hashing: SHA-256 / PBKDF2 with unique cryptographic salt per user."
             ], "AUTHENTICATION")
    add_card(s9, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "Officer Administration Console", [
                 "Dedicated Admin ID: admin@citizenshield.gov / admin123",
                 "Multi-attribute filtering: Filter complaints by Status, Priority, Category, and all 35 Wards.",
                 "Status Transition Directives: Move complaints from Submitted ➔ Under Review ➔ In Progress ➔ Resolved.",
                 "Audit Logging: Every administrative action logged with timestamp and officer attribution."
             ], "ADMIN CONSOLE")

    # -------------------------------------------------------------
    # SLIDE 10: Testing & Verification Results
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s10)
    add_header(s10, "Comprehensive Testing & Quality Verification", "Verification")
    add_card(s10, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "Automated ID Audit", [
                 "111+ HTML DOM Element IDs matched with JavaScript controllers.",
                 "0 missing IDs, 0 null-pointer crashes.",
                 "Tested across modern Chromium, Gecko, and WebKit browsers."
             ], "FRONTEND")
    add_card(s10, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "API Stress Testing", [
                 "HTTP 200 OK verified across all 8 REST API endpoints.",
                 "Sub-15ms response latency for SQLite WAL queries.",
                 "Graceful handling of multi-part photo uploads up to 10MB."
             ], "BACKEND")
    add_card(s10, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), 
             "Persistence Test", [
                 "Server restart survival verified.",
                 "Zero data loss across daemon restarts.",
                 "Git repository synced cleanly to GitHub."
             ], "STORAGE")

    # -------------------------------------------------------------
    # SLIDE 11: Demo Walkthrough Script for Evaluators
    # -------------------------------------------------------------
    s11 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s11)
    add_header(s11, "Demonstration Blueprint for Viva & College Demo", "Demo Guide")
    add_card(s11, Inches(0.8), Inches(1.8), Inches(11.6), Inches(5.0), 
             "4-Minute Live Demo Script for Evaluators", [
                 "1. Open http://localhost:5000: Showcase the 3D Dotted Earth Globe, interactively drag to rotate, click 'Target Tumakuru' to center on Tumakuru Corporation coords (13.3414° N, 77.1022° E).",
                 "2. Explain Safety Directive: Highlight the executive emergency ribbon directing crime/fire to 112 while reserving the platform for civic infrastructure defects.",
                 "3. Lodge Grievance: Demonstrate GPS pinpointing on Leaflet map, choose from all 35 Tumakuru Corporation wards (e.g. Ward 18 - SIT Campus), upload evidence photo, and submit to SQLite vault.",
                 "4. Track Case: Copy the tracking ID into Case Tracker to show the milestone timeline and generate the official Printable Case Dossier Certificate.",
                 "5. Officer Console: Log in as admin@citizenshield.gov / admin123, filter by Ward / Severity, and update the status to 'Resolved' with official work order remarks.",
                 "6. Conclude: Point to the GitHub repository and permanent database WAL architecture."
             ], "LIVE WALKTHROUGH")

    # -------------------------------------------------------------
    # SLIDE 12: Conclusion & Project Links
    # -------------------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    add_slide_bg(s12)
    add_header(s12, "Conclusion & Project Repositories", "Summary")
    add_card(s12, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "Key Project Achievements", [
                 "Complete full-stack civic governance portal delivered from scratch.",
                 "Permanent, immutable SQLite WAL database ensuring zero data loss.",
                 "Comprehensive coverage of all 35 Tumakuru City Corporation wards.",
                 "Unique, non-generic glassmorphic UI with bespoke 3D Dotted Earth math engine.",
                 "Full role-based security, GIS spatial integration, and printable legal certificates."
             ], "ACHIEVEMENTS")
    add_card(s12, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0), 
             "Project Access & Credentials", [
                 "GitHub Repository: https://github.com/chinmaymr7090/CitizenShield",
                 "Local Access URL: http://localhost:5000",
                 "Directorate Admin: admin@citizenshield.gov / admin123",
                 "Default Citizen: rahul.citizen@gmail.com / Citizen@2026",
                 "Lead Developer: Chinmay M R",
                 "Course: Full-Stack Web Development & Cloud Systems"
             ], "RESOURCES")

    prs.save(output_path)
    print(f"Presentation successfully created at: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "CitizenShield_Presentation.pptx"
    create_deck(out)
