"""
Local fallback content for every dynamic section of the site.

This is NOT meant to stay hardcoded forever — it's the Phase-1
stand-in for Firestore collections (services, testimonials, gallery,
doctor profile, site_content) so the site is fully populated and
demoable before Firebase credentials + admin data entry exist.
Once Firestore is wired in (Phase 5 admin panel), content_service.py
will read live documents and only fall back to this file if a
collection is empty or unreachable.
"""

HERO = {
    "clinic_name": "Pandey Health Clinic",
    "doctor_name": "Dr. Ved Prakash Pandey",
    "qualification": "B.Sc (MU), B.E.MS, M.D. Kolkata (WB)",
    "tagline": "Lord's Cares Better",
    "city": "Gaya, Bihar",
    "phone": "8083250208",
    "working_hours": "8 AM – 9 PM, Mon–Sat",
    "google_rating": 4.8,
    "google_reviews_count": 210,
    "trust_badges": [
        "15+ Years of Practice",
        "5,000+ Patients Treated",
        "Firebase-Secured Records",
        "Online & In-Clinic Care",
    ],
}

ABOUT = {
    "eyebrow": "About the Clinic",
    "heading": "Care that knows your name, not just your file number",
    "body": (
        "Pandey Health Clinic has served families in Gaya for over a "
        "decade, combining Dr. Ved Prakash Pandey's clinical training "
        "across Kolkata and Bihar with a genuinely personal approach to "
        "treatment. Every consultation is unhurried, every prescription "
        "explained, and every patient followed up on."
    ),
    "years_experience": 15,
    "patients_treated": "5,000+",
}

VISION = {
    "eyebrow": "Our Vision",
    "heading": "Affordable, modern healthcare for every home in Gaya",
    "points": [
        {
            "title": "Accessible Healthcare",
            "description": "Online and offline consultations so no patient is turned away by distance or time.",
        },
        {
            "title": "Modern Treatment",
            "description": "Evidence-based care paired with a digital record of every visit and prescription.",
        },
        {
            "title": "Community Healthcare",
            "description": "Preventive checkups and vaccination drives for the neighbourhoods we serve.",
        },
    ],
}

WHY_CHOOSE_US = [
    {"title": "Experienced Doctor", "description": "15+ years treating families across Bihar and West Bengal."},
    {"title": "Affordable Treatment", "description": "Transparent, upfront pricing on every service."},
    {"title": "Quality Medicines", "description": "Verified pharmacy stock with expiry and batch tracking."},
    {"title": "Fast Service", "description": "Most appointments confirmed within the hour."},
    {"title": "Online Consultation", "description": "Video, audio, or chat — from anywhere."},
    {"title": "Trusted Clinic", "description": "Rated 4.8/5 by patients across 200+ reviews."},
    {"title": "Friendly Staff", "description": "A calm, welcoming clinic experience for every visit."},
    {"title": "Modern Facilities", "description": "Clean, well-equipped treatment and waiting areas."},
    {"title": "Transparent Pricing", "description": "No hidden charges — every service lists its price."},
    {"title": "Personal Care", "description": "Follow-ups and reminders so nothing falls through."},
]

SERVICES = [
    {
        "id": "general-consultation",
        "name": "General Consultation",
        "description": "Routine checkups, diagnosis, and treatment for everyday health concerns.",
        "price": 300,
        "duration": "20 min",
        "image": "service-general.jpg",
    },
    {
        "id": "fever-treatment",
        "name": "Fever Treatment",
        "description": "Diagnosis and treatment for viral, bacterial, and seasonal fevers.",
        "price": 250,
        "duration": "15 min",
        "image": "service-fever.jpg",
    },
    {
        "id": "diabetes-management",
        "name": "Diabetes Management",
        "description": "Ongoing monitoring, medication review, and lifestyle guidance.",
        "price": 400,
        "duration": "30 min",
        "image": "service-diabetes.jpg",
    },
    {
        "id": "bp-check",
        "name": "Blood Pressure Check",
        "description": "Quick BP screening with guidance on diet and medication.",
        "price": 150,
        "duration": "10 min",
        "image": "service-bp.jpg",
    },
    {
        "id": "skin-problems",
        "name": "Skin Problems",
        "description": "Consultation for rashes, allergies, infections, and chronic skin issues.",
        "price": 350,
        "duration": "20 min",
        "image": "service-skin.jpg",
    },
    {
        "id": "child-care",
        "name": "Child Care",
        "description": "Pediatric checkups, growth tracking, and minor illness treatment.",
        "price": 300,
        "duration": "20 min",
        "image": "service-child.jpg",
    },
    {
        "id": "womens-health",
        "name": "Women's Health",
        "description": "Confidential consultations covering general and reproductive health.",
        "price": 400,
        "duration": "30 min",
        "image": "service-women.jpg",
    },
    {
        "id": "elderly-care",
        "name": "Elderly Care",
        "description": "Chronic condition management and mobility-friendly checkups for seniors.",
        "price": 350,
        "duration": "30 min",
        "image": "service-elderly.jpg",
    },
    {
        "id": "vaccination",
        "name": "Vaccination",
        "description": "Routine and travel vaccinations for all age groups.",
        "price": 200,
        "duration": "10 min",
        "image": "service-vaccination.jpg",
    },
    {
        "id": "online-consultation",
        "name": "Online Consultation",
        "description": "Video, audio, or chat consultation from home.",
        "price": 250,
        "duration": "20 min",
        "image": "service-online.jpg",
    },
    {
        "id": "health-checkup",
        "name": "Health Checkups",
        "description": "Full-body screening packages with lab report review.",
        "price": 900,
        "duration": "45 min",
        "image": "service-checkup.jpg",
    },
]

DOCTOR = {
    "name": "Dr. Ved Prakash Pandey",
    "qualification": "B.Sc (MU), B.E.MS, M.D. Kolkata (WB)",
    "experience_years": 15,
    "specializations": ["General Medicine", "Diabetes Care", "Chronic Disease Management"],
    "languages": ["Hindi", "English", "Bhojpuri"],
    "working_hours": "8 AM – 9 PM, Mon–Sat",
    "photo": "doctor-profile.jpg",
    "bio": (
        "Dr. Ved Prakash Pandey completed his M.D. in Kolkata, West Bengal, "
        "and has practiced general medicine in Gaya for over 15 years, "
        "treating thousands of patients with a focus on affordable, "
        "attentive care."
    ),
}

TESTIMONIALS = [
    {
        "name": "Ramesh Kumar",
        "rating": 5,
        "text": "Dr. Pandey took the time to actually explain my prescription. First clinic in Gaya that's felt this organized.",
        "approved": True,
    },
    {
        "name": "Sunita Devi",
        "rating": 5,
        "text": "Booked an online consultation for my mother — the doctor called right on time and followed up two days later.",
        "approved": True,
    },
    {
        "name": "Amit Verma",
        "rating": 4,
        "text": "Clean waiting area, fair pricing, and the staff remembered my case history from last visit.",
        "approved": True,
    },
]

GALLERY = [
    {"category": "Clinic", "image": "gallery-clinic-1.jpg", "caption": "Reception & waiting area"},
    {"category": "Clinic", "image": "gallery-clinic-2.jpg", "caption": "Treatment room"},
    {"category": "Doctor", "image": "gallery-doctor-1.jpg", "caption": "Dr. Pandey during a consultation"},
    {"category": "Events", "image": "gallery-event-1.jpg", "caption": "Free vaccination camp, 2025"},
]

CONTACT = {
    "address": "Pandey Health Clinic, Gaya, Bihar",
    "phone": "8083250208",
    "whatsapp": "918083250208",
    "email": "contact@pandeyhealthclinic.in",
    "working_hours": "8 AM – 9 PM, Mon–Sat",
    "emergency_contact": "8083250208",
    "map_embed_query": "Pandey Health Clinic, Gaya, Bihar",
}

NAV_LINKS = [
    {"label": "Home", "href": "#home"},
    {"label": "About", "href": "#about"},
    {"label": "Vision", "href": "#vision"},
    {"label": "Services", "href": "#services"},
    {"label": "Doctor", "href": "#doctor"},
    {"label": "Medicines", "href": "/medicines/"},
    {"label": "Testimonials", "href": "#testimonials"},
    {"label": "Gallery", "href": "#gallery"},
    {"label": "Contact", "href": "#contact"},
]

MEDICINE_CATEGORIES = [
    "Tablets", "Capsules", "Syrups", "Creams", "Supplements",
    "Baby Care", "Medical Equipment", "Personal Care", "Healthcare Devices",
]

MEDICINES = [
    {
        "id": "paracetamol-500",
        "name": "Paracetamol 500mg (Strip of 10)",
        "category": "Tablets",
        "description": "Fast-acting relief for fever, headache, and mild to moderate pain.",
        "mrp": 40,
        "offer_price": 32,
        "stock": 120,
        "prescription_required": False,
        "rating": 4.6,
        "review_count": 84,
        "image": "med-paracetamol.jpg",
    },
    {
        "id": "azithromycin-500",
        "name": "Azithromycin 500mg (Strip of 3)",
        "category": "Tablets",
        "description": "Antibiotic used to treat a variety of bacterial infections.",
        "mrp": 120,
        "offer_price": 99,
        "stock": 40,
        "prescription_required": True,
        "rating": 4.4,
        "review_count": 21,
        "image": "med-azithromycin.jpg",
    },
    {
        "id": "omeprazole-20",
        "name": "Omeprazole 20mg Capsules (Strip of 10)",
        "category": "Capsules",
        "description": "Reduces stomach acid to relieve heartburn and acid reflux.",
        "mrp": 85,
        "offer_price": 70,
        "stock": 65,
        "prescription_required": False,
        "rating": 4.5,
        "review_count": 37,
        "image": "med-omeprazole.jpg",
    },
    {
        "id": "cough-syrup-100ml",
        "name": "Herbal Cough Syrup (100ml)",
        "category": "Syrups",
        "description": "Ayurvedic cough syrup for dry and wet cough relief.",
        "mrp": 110,
        "offer_price": 95,
        "stock": 55,
        "prescription_required": False,
        "rating": 4.3,
        "review_count": 46,
        "image": "med-cough-syrup.jpg",
    },
    {
        "id": "iron-folic-syrup",
        "name": "Iron & Folic Acid Syrup (200ml)",
        "category": "Syrups",
        "description": "Supports healthy hemoglobin levels, recommended during pregnancy and anaemia.",
        "mrp": 140,
        "offer_price": 125,
        "stock": 30,
        "prescription_required": False,
        "rating": 4.5,
        "review_count": 18,
        "image": "med-iron-syrup.jpg",
    },
    {
        "id": "antifungal-cream",
        "name": "Antifungal Cream (20g)",
        "category": "Creams",
        "description": "Treats ringworm, athlete's foot, and other fungal skin infections.",
        "mrp": 75,
        "offer_price": 60,
        "stock": 48,
        "prescription_required": False,
        "rating": 4.2,
        "review_count": 29,
        "image": "med-antifungal-cream.jpg",
    },
    {
        "id": "moisturizing-cream",
        "name": "Daily Moisturizing Cream (50g)",
        "category": "Creams",
        "description": "Gentle, fragrance-free moisturizer for sensitive and dry skin.",
        "mrp": 180,
        "offer_price": 149,
        "stock": 70,
        "prescription_required": False,
        "rating": 4.7,
        "review_count": 63,
        "image": "med-moisturizer.jpg",
    },
    {
        "id": "multivitamin-tabs",
        "name": "Daily Multivitamin Tablets (30 count)",
        "category": "Supplements",
        "description": "A complete daily blend of essential vitamins and minerals.",
        "mrp": 260,
        "offer_price": 210,
        "stock": 90,
        "prescription_required": False,
        "rating": 4.6,
        "review_count": 102,
        "image": "med-multivitamin.jpg",
    },
    {
        "id": "protein-powder",
        "name": "Whey Protein Powder (500g)",
        "category": "Supplements",
        "description": "Supports muscle recovery and daily protein intake.",
        "mrp": 950,
        "offer_price": 799,
        "stock": 15,
        "prescription_required": False,
        "rating": 4.4,
        "review_count": 22,
        "image": "med-protein.jpg",
    },
    {
        "id": "baby-diaper-rash-cream",
        "name": "Baby Diaper Rash Cream (50g)",
        "category": "Baby Care",
        "description": "Soothes and protects delicate baby skin from diaper rash.",
        "mrp": 165,
        "offer_price": 140,
        "stock": 38,
        "prescription_required": False,
        "rating": 4.8,
        "review_count": 54,
        "image": "med-baby-cream.jpg",
    },
    {
        "id": "digital-thermometer",
        "name": "Digital Thermometer",
        "category": "Medical Equipment",
        "description": "Fast, accurate temperature readings for the whole family.",
        "mrp": 220,
        "offer_price": 179,
        "stock": 25,
        "prescription_required": False,
        "rating": 4.5,
        "review_count": 41,
        "image": "med-thermometer.jpg",
    },
    {
        "id": "bp-monitor",
        "name": "Automatic Blood Pressure Monitor",
        "category": "Healthcare Devices",
        "description": "Easy-to-use upper-arm BP monitor with digital display and memory.",
        "mrp": 2200,
        "offer_price": 1849,
        "stock": 12,
        "prescription_required": False,
        "rating": 4.6,
        "review_count": 33,
        "image": "med-bp-monitor.jpg",
    },
    {
        "id": "n95-mask-pack",
        "name": "N95 Face Masks (Pack of 10)",
        "category": "Personal Care",
        "description": "5-layer protection, comfortable fit for daily use.",
        "mrp": 350,
        "offer_price": 279,
        "stock": 0,
        "prescription_required": False,
        "rating": 4.3,
        "review_count": 47,
        "image": "med-n95-mask.jpg",
    },
    {
        "id": "glucometer-kit",
        "name": "Glucometer Kit with 25 Strips",
        "category": "Healthcare Devices",
        "description": "Complete blood glucose monitoring kit for home use.",
        "mrp": 1350,
        "offer_price": 1099,
        "stock": 18,
        "prescription_required": False,
        "rating": 4.5,
        "review_count": 26,
        "image": "med-glucometer.jpg",
    },
]
