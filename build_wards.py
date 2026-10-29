import json

bbmp = [
    (1, 'Kempegowda (Yelahanka)'), (2, 'Chowdeshwari'), (3, 'Atturu'), (4, 'Yelahanka Satellite Town'),
    (5, 'Jakkuru'), (6, 'Thanisandra'), (7, 'Byatarayanapura'), (8, 'Kodigehalli'), (9, 'Vidyaranyapura'),
    (10, 'Dodda Bommasandra'), (11, 'Kuvempu Nagar'), (12, 'Shettihalli'), (13, 'Mallasandra'),
    (14, 'Bagalagunte'), (15, 'T Dasarahalli'), (16, 'Jalahalli'), (17, 'J.P. Park'), (18, 'Radhakrishna Temple'),
    (19, 'Sanjaya Nagar'), (20, 'Ganga Nagar'), (21, 'Hebbala'), (22, 'Vishwanath Nagenahalli'),
    (23, 'Nagavara'), (24, 'HBR Layout'), (25, 'Horamavu'), (26, 'Ramamurthy Nagar'), (27, 'Banasavadi'),
    (28, 'Kammanahalli'), (29, 'Kacharkanahalli'), (30, 'Kadugondanahalli'), (31, 'Kushal Nagar'),
    (32, 'Kaval Bairasandra'), (33, 'Manorayanapalya'), (34, 'Gangenahalli'), (35, 'Aramane Nagara'),
    (36, 'Mattikere'), (37, 'Yeshwanthpura'), (38, 'HMT Ward'), (39, 'Chokkasandra'), (40, 'Dodda Bidarakallu'),
    (41, 'Peenya Industrial Area'), (42, 'Lakshmidevi Nagar'), (43, 'Nandini Layout'), (44, 'Marappana Palya'),
    (45, 'Malleshwaram'), (46, 'Jayachamarajendra Nagar'), (47, 'Devara Jeevanahalli'), (48, 'Muneshwara Nagar'),
    (49, 'Lingarajapura'), (50, 'Benniganahalli'), (51, 'Vijnanapura'), (52, 'KR Puram'),
    (53, 'Basavanapura'), (54, 'Hoodi'), (55, 'Devasandra'), (56, 'A Narayanapura'),
    (57, 'Vijnana Nagar'), (58, 'New Tippasandra'), (59, 'Maruthi Seva Nagar'), (60, 'Sagayara Puram'),
    (61, 'SK Garden'), (62, 'Ramaswamy Palya'), (63, 'Jayamahal'), (64, 'Rajamahal Guttahalli'),
    (65, 'Kadu Malleshwaram'), (66, 'Subramanya Nagar'), (67, 'Gayithri Nagar'), (68, 'Prakash Nagar'),
    (69, 'Rajaji Nagar'), (70, 'Rajajinagar 6th Block'), (71, 'Agrahara Dasarahalli'), (72, 'Dr. Rajkumar Ward'),
    (73, 'Shiva Nagar'), (74, 'Basaveshwara Nagar'), (75, 'Shankar Matt'), (76, 'Shakthi Ganapathi Nagar'),
    (77, 'Kamala Nagar'), (78, 'Vrishabhavathi Nagar'), (79, 'Kamakshipalya'), (80, 'Dayananda Nagar'),
    (81, 'Prakash Nagar East'), (82, 'Rajajinagar Industrial'), (83, 'Govindaraja Nagar'), (84, 'Kaveripura'),
    (85, 'Shivajinagar'), (86, 'Maruthi Mandir'), (87, 'Mudalapalya'), (88, 'Nagapura'),
    (89, 'Mahalakshmipuram'), (90, 'Kalyana Nagar'), (91, 'Bharathi Nagar'), (92, 'Shivaji Nagar North'),
    (93, 'Vasanth Nagar'), (94, 'Gandhi Nagar'), (95, 'Subhash Nagar'), (96, 'Okalipuram'),
    (97, 'Dayananda Nagar South'), (98, 'Prakash Nagar West'), (99, 'Rajajinagar North'), (100, 'Kempapura Agrahara'),
    (101, 'Kamakshipalya South'), (102, 'Vrushabhavathi East'), (103, 'Kaveripura South'), (104, 'Govindaraja Nagar South'),
    (105, 'Agrahara'), (106, 'Dr. Rajkumar Ward South'), (107, 'Shiva Nagar South'), (108, 'Sri Ram Mandir'),
    (109, 'Chickpete / Commercial'), (110, 'Sampangiram Nagar'), (111, 'Shantala Nagar (MG Road/Brigade)'),
    (112, 'Domlur / Indiranagar (Central)'), (113, 'Konena Agrahara'), (114, 'HAL Airport Ward'),
    (115, 'Vimanapura'), (116, 'Nilasandra'), (117, 'Shanthi Nagar'), (118, 'Austin Town'),
    (119, 'Ejipura'), (120, 'Koramangala North'), (121, 'BTM Layout North'), (122, 'Madiwala Central'),
    (123, 'Jayanagar East'), (124, 'Jayanagar South'), (125, 'Byrasandra'), (126, 'Pattabhiram Nagar'),
    (127, 'Jayanagar 4th T Block'), (128, 'Gurappanapalya'), (129, 'BTM Layout South'), (130, 'Madiwala South'),
    (131, 'Nayandahalli'), (132, 'Attiguppe'), (133, 'Hampi Nagar'), (134, 'Bapuji Nagar'),
    (135, 'Padarayanapura'), (136, 'Jagajivanram Nagar'), (137, 'Rayapuram'), (138, 'Chalavadipalya'),
    (139, 'KR Market'), (140, 'Chamrajpet'), (141, 'Azad Nagar'), (142, 'Sunkenahalli / Indiranagar'),
    (143, 'Vishveshwara Puram'), (144, 'Siddapura'), (145, 'Hombegowda Nagar'), (146, 'Lakkasandra'),
    (147, 'Adugodi'), (148, 'Ejipura South'), (149, 'Varthur'), (150, 'Bellandur'),
    (151, 'Koramangala Central'), (152, 'Madivala'), (153, 'Jakkasandra'), (154, 'HSR Layout North'),
    (155, 'Hanumanth Nagar'), (156, 'Srinagar'), (157, 'Gali Anjaneya Temple'), (158, 'Deepanjali Nagar'),
    (159, 'Hosahalli'), (160, 'Vijayanagar'), (161, 'Hosahalli West'), (162, 'Attiguppe West'),
    (163, 'Nayandahalli South'), (164, 'Kengeri Satellite Town'), (165, 'Gnanabharathi'), (166, 'Nagarabhavi'),
    (167, 'Kottigepalya'), (168, 'Herohalli'), (169, 'Ullalu'), (170, 'Ullalu Satellite'),
    (171, 'Byatarayanapura South'), (172, 'Channasandra'), (173, 'Rajarajeshwari Nagar'), (174, 'HSR Layout Central'),
    (175, 'Bommanahalli'), (176, 'BTM Layout Central'), (177, 'J.P. Nagar 2nd Phase'), (178, 'Sarakki'),
    (179, 'Shakambari Nagar'), (180, 'Banashankari Temple'), (181, 'Kumaraswamy Layout'), (182, 'Padmanaba Nagar'),
    (183, 'Chikkalasandra'), (184, 'Uttarahalli'), (185, 'Yelachenahalli'), (186, 'Jaraganahalli'),
    (187, 'Puttenahalli'), (188, 'Bilekahalli'), (189, 'Hulimavu'), (190, 'Begur'),
    (191, 'Konanakunte'), (192, 'Anjanapura'), (193, 'Gottigere'), (194, 'Kothnur'),
    (195, 'Kudlu / Harlur'), (196, 'Ananthapura'), (197, 'Vasanthapura'), (198, 'Hemmigepura (Kengeri)')
]

other_corps = {
    'Mysuru City Corporation (MCC) - 65 Wards': [
        (1, 'Chamundi Hill & Foot Area'), (2, 'Siddartha Layout'), (3, 'K.C. Layout'),
        (4, 'Nazarbad'), (5, 'Ittegagud & Zoo Area'), (6, 'Girishnagar'), (7, 'Jayalakshmipuram'),
        (8, 'Vani Vilas Puram'), (9, 'Paduvarahalli'), (10, 'Yadavagiri'), (11, 'V.V. Mohalla'),
        (12, 'Gokulam 1st Stage'), (13, 'Gokulam 3rd Stage'), (14, 'Brindavan Extension'),
        (15, 'Kumbarakoppal'), (16, 'Metagalli Industrial'), (17, 'Hebbal 1st Stage'),
        (18, 'Mankalapur'), (19, 'Vijayanagar 1st Stage'), (20, 'Vijayanagar 2nd Stage'),
        (21, 'Hootagalli'), (22, 'Belavadi'), (23, 'Bogadi'), (24, 'Saraswathipuram'),
        (25, 'K.G. Koppal'), (26, 'Tonachikoppal'), (27, 'Sharadadevi Nagar'), (28, 'Dattagalli'),
        (29, 'Ramakrishnanagar'), (30, 'Kuvempunagar North'), (31, 'Kuvempunagar Central'),
        (32, 'Kuvempunagar South'), (33, 'Srirampura'), (34, 'Vivekananda Nagar'), (35, 'Kanakagiri'),
        (36, 'Vidyaranyapuram'), (37, 'Ashokapuram'), (38, 'Chamarajapuram'), (39, 'Krishnaraja Mohalla'),
        (40, 'Agrahara'), (41, 'Sunnadakeri'), (42, 'Fort Mohalla'), (43, 'Santhepet & Old Market'),
        (44, 'Devaraja Market Central'), (45, 'Subbarayanakere'), (46, 'Irwin Road Commercial'),
        (47, 'Lashkar Mohalla'), (48, 'Mandi Mohalla'), (49, 'Tilak Nagar'), (50, 'Bannimantap East'),
        (51, 'Bannimantap West'), (52, 'Hanumanthanagar'), (53, 'Shivarampet'), (54, 'Gousianagar'),
        (55, 'Udayagiri Central'), (56, 'Kyathamaranahalli'), (57, 'Kalyangiri'), (58, 'Shanthinagar'),
        (59, 'Mahadevapura Road'), (60, 'Gandhinagar'), (61, 'Rajivnagar 1st Stage'),
        (62, 'Rajivnagar 2nd Stage'), (63, 'Kesare'), (64, 'Naidunagar'), (65, 'R.S. Naidu Nagar')
    ],
    'Hubballi-Dharwad Municipal Corporation (HDMC) - 40 Wards': [
        (1, 'Unkal Lake & North Hubballi'), (2, 'Bhairidevarakoppa'), (3, 'Navanagar Central'),
        (4, 'Amargol'), (5, 'Rayapur Industrial Corridor'), (6, 'Sattur Hubballi'),
        (7, 'Gandhinagar Dharwad'), (8, 'Lakamanahalli'), (9, 'Dharwad City & Subhas Road'),
        (10, 'Vidyanagar Hubballi'), (11, 'Shirur Park'), (12, 'Kallur Layout'),
        (13, 'Bhavani Nagar'), (14, 'Lingaraj Nagar'), (15, 'Keshwapur Central'),
        (16, 'Kusugal Road'), (17, 'Madhavpur'), (18, 'Railway Colony'),
        (19, 'Ganesh Peth'), (20, 'Durgad Bail Commercial'), (21, 'Broadway Market'),
        (22, 'Old Hubballi Central'), (23, 'Kamaladinni'), (24, 'Bengeri Extension'),
        (25, 'Gopankoppa'), (26, 'Ashok Nagar Hubballi'), (27, 'Deshpande Nagar'),
        (28, 'Court Circle & PB Road'), (29, 'Saptapur Dharwad'), (30, 'Kalyan Nagar Dharwad'),
        (31, 'Malmaddi Dharwad'), (32, 'Karnataka University Campus'), (33, 'Kelageri Dharwad'),
        (34, 'Tejaswi Nagar'), (35, 'Narayanpur Dharwad'), (36, 'Haliyal Road Extension'),
        (37, 'Madihal Dharwad'), (38, 'Kamalapur Dharwad'), (39, 'Hosayellapur Dharwad'),
        (40, 'Dharwad Market & Line Bazar')
    ],
    'Mangaluru City Corporation (MCC) - 50 Wards': [
        (1, 'Surathkal West'), (2, 'Surathkal East'), (3, 'Katipalla North'), (4, 'Katipalla East'),
        (5, 'Iddya'), (6, 'Hosabettu'), (7, 'Kulai'), (8, 'Baikampady Industrial'),
        (9, 'Panambur Port'), (10, 'Bengre Sandspit'), (11, 'Kavoor'), (12, 'Kunjathbail North'),
        (13, 'Kunjathbail South'), (14, 'Marakada'), (15, 'Derebail North'), (16, 'Derebail West'),
        (17, 'Derebail South'), (18, 'Derebail East'), (19, 'Pachanady'), (20, 'Bondel'),
        (21, 'Padavu West'), (22, 'Kadri North'), (23, 'Kadri South & Mallikatte'), (24, 'Bejai Central'),
        (25, 'Anegundi'), (26, 'Kodialbail Commercial'), (27, 'Kambla'), (28, 'Mannagudda'),
        (29, 'Barke'), (30, 'Alake'), (31, 'Dongerkery'), (32, 'Kudroli'),
        (33, 'Bunder Old Port'), (34, 'Port Ward'), (35, 'Cantonment'), (36, 'Milagres'),
        (37, 'Hampankatta Central'), (38, 'Falnir'), (39, 'Attavar'), (40, 'Mangaladevi Temple'),
        (41, 'Pandeshwar'), (42, 'Bolar Heritage'), (43, 'Jeppu'), (44, 'Kankanady'),
        (45, 'Valencia'), (46, 'Pumpwell Junction'), (47, 'Bajal'), (48, 'Kannur Mangalore'),
        (49, 'Ullal & Netravathi Bridge'), (50, 'Padil & Mahaveer Circle')
    ],
    'Belagavi City Corporation - 20 Wards': [
        (1, 'Camp Cantonment Area'), (2, 'Civil Hospital & Court'), (3, 'Tilakwadi North'),
        (4, 'Tilakwadi South'), (5, 'Congress Road & 1st Gate'), (6, 'Hindwadi'),
        (7, 'Bhagya Nagar'), (8, 'Angol'), (9, 'Vadgaon Central'), (10, 'Shahapur Market'),
        (11, 'Khasbag'), (12, 'Fort & Military Area'), (13, 'Khade Bazar'), (14, 'Ganpat Galli'),
        (15, 'Raviwar Peth'), (16, 'Kittur Chennamma Circle'), (17, 'Nehru Nagar'),
        (18, 'Shivaji Nagar Belagavi'), (19, 'Auto Nagar Industrial'), (20, 'Kuvempu Nagar Belagavi')
    ],
    'Kalaburagi (Gulbarga) City Corporation - 12 Wards': [
        (1, 'High Court & MSK Mill'), (2, 'Super Market & Central Town'), (3, 'Sedam Road & University'),
        (4, 'Nehru Gunj Market'), (5, 'Shah Bazar'), (6, 'Brahmpur'), (7, 'Gazipura'),
        (8, 'Khaja Colony & Dargah Area'), (9, 'Afzalpur Road'), (10, 'Humnabad Ring Road'),
        (11, 'Jewargi Colony'), (12, 'KHB Colony & Aland Road')
    ]
}

data = []
data.append({
    "corporation": "Bruhat Bengaluru Mahanagara Palike (BBMP) - 198 Wards",
    "prefix": "BBMP",
    "wards": [f"BBMP Ward {num} - {name}" for num, name in bbmp]
})

for corp_title, wards_list in other_corps.items():
    prefix = corp_title.split()[0]
    data.append({
        "corporation": corp_title,
        "prefix": prefix,
        "wards": [f"{prefix} Ward {num} - {name}" for num, name in wards_list]
    })

js_content = "// Comprehensive Karnataka Municipal Wards Directory\nexport const KARNATAKA_MUNICIPAL_ZONES = " + json.dumps(data, indent=2) + ";\n"

with open("js/karnataka-wards.js", "w", encoding="utf-8") as f:
    f.write(js_content)

print(f"Generated js/karnataka-wards.js with {sum(len(x['wards']) for x in data)} total wards across {len(data)} corporations!")
