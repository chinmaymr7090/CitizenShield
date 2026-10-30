import sys, os
sys.path.insert(0, os.path.abspath('backend'))
from database import get_connection

conn = get_connection()
c = conn.cursor()

# Map the 2 user-created Kyatasandra reports to Ward 10 - Kyatsandra
c.execute("""
    UPDATE reports 
    SET ward = 'Ward 10 - Kyatsandra / Siddaganga Math Gateway'
    WHERE report_id IN ('CS-2026-89608', 'CS-2026-14559')
""")

# Map the 4 seed reports to Tumakuru Corporation Wards
c.execute("""
    UPDATE reports 
    SET ward = 'Ward 18 - SIT College Campus / SIT Extension',
        location = 'Near SIT Main Gate, BH Road, Ward 18, Tumakuru',
        latitude = 13.3275,
        longitude = 77.1262
    WHERE report_id = 'CS-2026-84912'
""")

c.execute("""
    UPDATE reports 
    SET ward = 'Ward 23 - Gubbi Gate Market / Railway Station Corridor',
        location = 'Gubbi Gate Circle Junction, Ward 23, Tumakuru',
        latitude = 13.3392,
        longitude = 77.0988
    WHERE report_id = 'CS-2026-30219'
""")

c.execute("""
    UPDATE reports 
    SET ward = 'Ward 11 - Mandipet / Town Hall Commercial Core',
        location = 'Near Town Hall Circle, Mandipet Cross, Ward 11, Tumakuru',
        latitude = 13.3421,
        longitude = 77.1015
    WHERE report_id = 'CS-2026-11840'
""")

c.execute("""
    UPDATE reports 
    SET ward = 'Ward 8 - Batawadi (North) / Bengaluru Highway',
        location = 'Batawadi Service Road, near KSRTC Depot, Ward 8, Tumakuru',
        latitude = 13.3312,
        longitude = 77.1215
    WHERE report_id = 'CS-2026-62841'
""")

# Update officer name & department in users
c.execute("""
    UPDATE users 
    SET name = 'Municipal Commissioner Office (Tumakuru)',
        department = 'Tumakuru City Corporation Directorate'
    WHERE email = 'admin@citizenshield.gov'
""")

c.execute("""
    UPDATE users 
    SET name = 'Er. K. Ramesh (Tumakuru Zone 1)',
        department = 'Roads & Civil Infrastructure, Tumakuru'
    WHERE email = 'engineer@citizenshield.gov'
""")

conn.commit()
conn.close()
print("SUCCESS: Database records updated for Tumakuru City Corporation!")
