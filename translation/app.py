from flask import Flask, request, jsonify
from flask_cors import CORS
from libre_translate_api import LibreTranslateAPI
import re
import pytesseract
from PIL import Image
import os
import time
import requests
import math # Added for distance calculation

# NOTE: The Tesseract code is now restored. For a real application,
# you must have Tesseract installed on your system and provide the
# correct path below. If the path is not set correctly, this will fail.

# Uncomment this line and set your local Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
CORS(app)

# Connect to your local LibreTranslate server
lt = LibreTranslateAPI("http://localhost:5000")

# --- Expanded Medical Glossary with all languages ---
medical_glossary = {
    "fever": {"en": "fever", "hi": "बुखार", "es": "fiebre", "de": "Fieber", "fr": "fièvre", "ar": "حمى", "bn": "জ্বর", "zh": "发烧", "ja": "熱", "ko": "열", "ru": "лихорадка", "pt": "febre", "it": "febbre", "nl": "koorts", "tr": "ateş", "pl": "gorączka", "sv": "feber"},
    "cancer": {"en": "cancer", "hi": "कैंसर", "es": "cáncer", "de": "Krebs", "fr": "cancer", "ar": "سرطان", "bn": "ক্যান্সার", "zh": "癌症", "ja": "癌", "ko": "암", "ru": "рак", "pt": "câncer", "it": "cancro", "nl": "kanker", "tr": "kanser", "pl": "rak", "sv": "cancer"},
    "headache": {"en": "headache", "hi": "सिरदर्द", "es": "dolor de cabeza", "de": "Kopfschmerzen", "fr": "mal de tête", "ar": "صداع", "bn": "মাথাব্যথা", "zh": "头晕", "ja": "頭痛", "ko": "두통", "ru": "головная боль", "pt": "dor de cabeça", "it": "mal di testa", "nl": "hoofdpijn", "tr": "baş ağrıısı", "pl": "ból głowy", "sv": "huvudvärk"},
    "diabetes": {"en": "diabetes", "hi": "मधुमेह", "es": "diabetes", "de": "Diabetes", "fr": "diabète", "ar": "سكري", "bn": "ডায়াবেটিস", "zh": "糖尿病", "ja": "糖尿病", "ko": "당뇨병", "ru": "диабет", "pt": "diabetes", "it": "diabete", "nl": "diabetes", "tr": "diyabet", "pl": "cukrzyca", "sv": "diabetes"},
    "asthma": {"en": "asthma", "hi": "दमा", "es": "asma", "de": "Asthma", "fr": "asthme", "ar": "ربو", "bn": "হাঁপানি", "zh": "哮喘", "ja": "喘息", "ko": "천식", "ru": "астма", "pt": "asma", "it": "asma", "nl": "astma", "tr": "astım", "pl": "astma", "sv": "astma"},
    "fracture": {"en": "fracture", "hi": "फ्रैक्चर", "es": "fractura", "de": "Fraktur", "fr": "fracture", "ar": "كسر", "bn": "ফ্র্যাকচার", "zh": "骨折", "ja": "骨折", "ko": "골절", "ru": "перелом", "pt": "fratura", "it": "frattura", "nl": "fractuur", "tr": "kırık", "pl": "złamanie", "sv": "fraktur"},
    "infection": {"en": "infection", "hi": "संक्रमण", "es": "infección", "de": "Infektion", "fr": "infection", "ar": "عدوى", "bn": "সংক্রমণ", "zh": "感染", "ja": "感染症", "ko": "감염", "ru": "инфекция", "pt": "infecção", "it": "infezione", "nl": "infectie", "tr": "enfeksiyon", "pl": "infekcja", "sv": "infektion"},
    "pain": {"en": "pain", "hi": "दर्द", "es": "dolor", "de": "Schmerz", "fr": "douleur", "ar": "ألم", "bn": "ব্যথা", "zh": "痛", "ja": "痛み", "ko": "통증", "ru": "боль", "pt": "dor", "it": "dolore", "nl": "pijn", "tr": "ağrı", "pl": "ból", "sv": "smärta"},
    "vomiting": {"en": "vomiting", "hi": "उल्टी", "es": "vómito", "de": "Erbrechen", "fr": "vomissement", "ar": "قيء", "bn": "বমি", "zh": "呕吐", "ja": "嘔吐", "ko": "구토", "ru": "рвота", "pt": "vômito", "it": "vomito", "nl": "braken", "tr": "kusma", "pl": "wymioty", "sv": "kräkningar"},
    "cough": {"en": "cough", "hi": "खांसी", "es": "tos", "de": "Husten", "fr": "toux", "ar": "سعال", "bn": "কাশি", "zh": "咳嗽", "ja": "咳", "ko": "기침", "ru": "кашель", "pt": "tosse", "it": "tosse", "nl": "hoest", "tr": "öksürük", "pl": "kaszel", "sv": "hosta"},
    "nausea": {"en": "nausea", "hi": "मतली", "es": "náusea", "de": "Übelkeit", "fr": "nausée", "ar": "غثيان", "bn": "বমি বমি ভাব", "zh": "头晕", "ja": "吐き気", "ko": "메스꺼움", "ru": "тошнота", "pt": "náusea", "it": "nausea", "nl": "misselijkheid", "tr": "mide bulantısı", "pl": "mdłości", "sv": "illamående"},
    "dizziness": {"en": "dizziness", "hi": "चक्कर", "es": "mareo", "de": "Schwindel", "fr": "vertige", "ar": "دوخة", "bn": "মাথা ঘোরা", "zh": "头晕", "ja": "めまい", "ko": "현기증", "ru": "головокружение", "pt": "tontura", "it": "vertigini", "nl": "duizeligheid", "tr": "baş dönmesi", "pl": "zawroty głowy", "sv": "yrsel"},
    "stroke": {"en": "stroke", "hi": "स्ट्रोक", "es": "derrame cerebral", "de": "Schlaganfall", "fr": "AVC", "ar": "سكتة دماغية", "bn": "স্ট্রোক", "zh": "中风", "ja": "脳卒中", "ko": "뇌졸증", "ru": "инсульт", "pt": "AVC", "it": "ictus", "nl": "beroerte", "tr": "inme", "pl": "udar", "sv": "stroke"},
    "heart attack": {"en": "heart attack", "hi": "दिल का दौरा", "es": "ataque al corazón", "de": "Herzinfarkt", "fr": "crise cardiaque", "ar": "نوبة قلبية", "bn": "হার্ট অ্যাটাক", "zh": "心脏病发作", "ja": "心臓発作", "ko": "심장 मাবি", "ru": "сердечный приступ", "pt": "ataque cardíaco", "it": "infarto", "nl": "hartaanval", "tr": "kalp krizi", "pl": "zawał serca", "sv": "hjärtattack"},
    "allergy": {"en": "allergy", "hi": "एलर्जी", "es": "alergia", "de": "Allergie", "fr": "allergie", "ar": "حساسية", "bn": "অ্যালার্জি", "zh": "过敏", "ja": "アレルギー", "ko": "알레르기", "ru": "аллергия", "pt": "alergia", "it": "allergia", "nl": "allergie", "tr": "alerji", "pl": "alergia", "sv": "allergi"},
    "blood pressure": {"en": "blood pressure", "hi": "रक्तचाप", "es": "presión arterial", "de": "Blutdruck", "fr": "pression artérielle", "ar": "ضغط الدم", "bn": "রক্তচাপ", "zh": "血压", "ja": "血圧", "ko": "혈압", "ru": "кровяное давление", "pt": "pressão arterial", "it": "pressione sanguigna", "nl": "bloeddruk", "tr": "tansiyon", "pl": "ciśnienie krwi", "sv": "blodtryck"},
    "surgery": {"en": "surgery", "hi": "सर्जरी", "es": "cirugía", "de": "Operation", "fr": "chirurgie", "ar": "جراحة", "bn": "অস্ত্রোপচার", "zh": "手术", "ja": "手術", "ko": "수술", "ru": "хирургия", "pt": "cirurgia", "it": "chirurgia", "nl": "operatie", "tr": "cerrahi", "pl": "operacja", "sv": "kirurgi"},
    "vaccine": {"en": "vaccine", "hi": "टीका", "es": "vacuna", "de": "Impfstoff", "fr": "vaccin", "ar": "لقاح", "bn": "টিকা", "zh": "疫苗", "ja": "ワクチン", "ko": "백신", "ru": "вакцина", "pt": "vacina", "it": "vaccino", "nl": "vaccin", "tr": "aşı", "pl": "szczepionka", "sv": "vaccin"},
    "prescription": {"en": "prescription", "hi": "नुस्खा", "es": "receta", "de": "Rezept", "fr": "ordonnance", "ar": "وصفة طبية", "bn": "প্রেসক্রিপশন", "zh": "处方", "ja": "処方箋", "ko": "처방전", "ru": "рецепт", "pt": "prescrição", "it": "prescrizione", "nl": "recept", "tr": "reçete", "pl": "recepta", "sv": "recept"},
    "medicine": {"en": "medicine", "hi": "দવા", "es": "medicina", "de": "Medizin", "fr": "médicament", "ar": "দواء", "bn": "ঔষধ", "zh": "药", "ja": "薬", "ko": "약", "ru": "лекарство", "pt": "remédio", "it": "medicina", "nl": "medicijn", "tr": "ilaç", "pl": "lekarstwo", "sv": "medicin"},
    "doctor": {"en": "doctor", "hi": "डॉक्टर", "es": "médico", "de": "Arzt", "fr": "médecin", "ar": "طبيب", "bn": "ডাক্তার", "zh": "医生", "ja": "医者", "ko": "의사", "ru": "врач", "pt": "médico", "it": "dottore", "nl": "dokter", "tr": "doktor", "pl": "lekarz", "sv": "läkare"},
    "nurse": {"en": "nurse", "hi": "নर्स", "es": "enfermera", "de": "Krankenschwester", "fr": "infirmière", "ar": "ممرضة", "bn": "নার্স", "zh": "护士", "ja": "看護師", "ko": "간호사", "ru": "медсестра", "pt": "enfermeira", "it": "infermiera", "nl": "verpleegkundige", "tr": "hemşire", "pl": "pielęgniarka", "sv": "sjuksköterska"},
    "hospital": {"en": "hospital", "hi": "अस्पताल", "es": "hospital", "de": "Krankenhaus", "fr": "hôpital", "ar": "مستشفى", "bn": "হাসপাতাল", "zh": "医院", "ja": "病院", "ko": "병원", "ru": "больница", "pt": "hospital", "it": "ospedale", "nl": "ziekenhuis", "tr": "hastane", "pl": "szpital", "sv": "sjukhus"},
    "pharmacy": {"en": "pharmacy", "hi": "ফಾರ್মেসি", "es": "farmacia", "de": "Apotheke", "fr": "pharmacie", "ar": "صيدلية", "bn": "ফার্মেসি", "zh": "药店", "ja": "薬局", "ko": "약국", "ru": "аптека", "pt": "farmácia", "it": "farmacia", "nl": "apotheek", "tr": "eczane", "pl": "apteka", "sv": "apotek"},
    "ambulance": {"en": "ambulance", "hi": "এम्बুলেন্স", "es": "ambulancia", "de": "Krankenwagen", "fr": "ambulance", "ar": "سياره اسعاف", "bn": "অ্যাম্বুলেন্স", "zh": "救护车", "ja": "救急車", "ko": "구급차", "ru": "скорая помощь", "pt": "ambulância", "it": "ambulanza", "nl": "ambulance", "tr": "ambulans", "pl": "karetka", "sv": "ambulans"},
}

# --- Symptom to Department Mapping ---
symptom_to_department = {
    "fever": ["General Medicine"],
    "headache": ["Neurology", "General Medicine"],
    "cough": ["Pulmonology", "General Medicine"],
    "pain": ["General Medicine", "Orthopedics"],
    "fracture": ["Orthopedics", "Emergency"],
    "dizziness": ["Neurology", "ENT"],
    "nausea": ["Gastroenterology"],
    "vomiting": ["Gastroenterology", "Emergency"],
    "heart attack": ["Cardiology", "Emergency"],
    "stroke": ["Neurology", "Emergency"],
    "cancer": ["Oncology"],
    "diabetes": ["Endocrinology"],
    "asthma": ["Pulmonology"],
    "allergy": ["Allergy & Immunology"],
    "infection": ["Infectious Disease", "General Medicine"],
    "blood pressure": ["Cardiology", "General Medicine"],
}

department_translations = {
    "General Medicine": {"en": "General Medicine", "hi": "सामान्य चिकित्सा", "es": "Medicina General", "de": "Allgemeinmedizin"},
    "Neurology": {"en": "Neurology", "hi": "तंत्रिका-বিজ্ঞান", "es": "Neurología", "de": "Neurologie"},
    "Pulmonology": {"en": "Pulmonology", "hi": "फेफড়া বিজ্ঞান", "es": "Neumología", "de": "Pneumologie"},
    "Orthopedics": {"en": "Orthopedics", "hi": "हड्डी रोग", "es": "Ortopedia", "de": "Orthopädie"},
    "Emergency": {"en": "Emergency", "hi": "आपातकालीन", "es": "Emergencia", "de": "Notaufnahme"},
    "Gastroenterology": {"en": "Gastroenterology", "hi": "জठरांत्र विज्ञान", "es": "Gastroenterología", "de": "Gastroenterologie"},
    "ENT": {"en": "ENT", "hi": "ईएनटी", "es": "Otorrinolaringología", "de": "HNO"},
    "Cardiology": {"en": "Cardiology", "hi": "হৃदय রোগ বিজ্ঞান", "es": "Cardiología", "de": "Kardiologie"},
    "Oncology": {"en": "Oncology", "hi": "ক্যান্সার বিজ্ঞান", "es": "Oncología", "de": "Onkologie"},
    "Endocrinology": {"en": "Endocrinology", "hi": "অন্তঃस्त्राবिका", "es": "Endocrinología", "de": "Endokrinologie"},
    "Allergy & Immunology": {"en": "Allergy & Immunology", "hi": "एलर्जी এবং इम्यूनोलॉजी", "es": "Alergia e Inmunología", "de": "Allergologie und Immunologie"},
    "Infectious Disease": {"en": "Infectious Disease", "hi": "সংক্রামক রোগ", "es": "Enfermedades Infecciosas", "de": "Infektionskrankheiten"},
}

# --- Keyword to Visual Aid Mapping ---
keyword_to_visual = {
    "headache": "http://localhost:5001/static/images/headache.jpg",
    "fever": "https://i.imgur.com/sC207aF.png",
    "cough": "https://i.imgur.com/JOLi9i6.png",
    "heart attack": "https://i.imgur.com/wS3gD3R.png",
    "stroke": "https://i.imgur.com/c3eLg6E.png",
    "fracture": "https://i.imgur.com/sXvjX3f.png",
    "pain": "https://i.imgur.com/Y3hI8fD.png",
    "stomach": "https://i.imgur.com/Y3hI8fD.png", 
}

def find_medical_keywords(text, source_lang):
    """
    Finds medical terms in the text and returns their English equivalents.
    """
    found_keywords = []
    lower_text = " " + text.lower() + " "
    sorted_glossary = sorted(medical_glossary.items(), key=lambda item: len(item[0]), reverse=True)
    
    for english_term, translations in sorted_glossary:
        if source_lang in translations:
            term_to_find = " " + translations[source_lang].lower() + " "
            if term_to_find in lower_text:
                found_keywords.append(english_term)
                lower_text = lower_text.replace(term_to_find, " ")

    return list(set(found_keywords))

@app.route('/detect', methods=['POST'])
def detect_language_route():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    
    text_to_detect = data.get('text')
    try:
        detected_data = lt.detect(text_to_detect)
        if detected_data and detected_data[0]['confidence'] > 30: 
            lang_code = detected_data[0]['language']
            return jsonify({"language": lang_code})
        return jsonify({"language": "en"}) 
    except Exception as e:
        print(f"Detection error: {e}")
        return jsonify({"error": "Language detection failed"}), 500

@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "No JSON payload found"}), 400

    text_to_translate = data.get('text')
    source_lang = data.get('source', 'en')
    target_lang = data.get('target', 'es')

    if not text_to_translate:
        return jsonify({"translatedText": "", "keywords": [], "recommendations": [], "visualAid": None})

    try:
        keywords_in_english = find_medical_keywords(text_to_translate, source_lang)
        translated_text = lt.translate(text_to_translate, source=source_lang, target=target_lang)
        
        keywords_data = []
        if keywords_in_english:
            for english_keyword in keywords_in_english:
                if target_lang in medical_glossary.get(english_keyword, {}):
                    translated_term = medical_glossary[english_keyword][target_lang]
                    keywords_data.append({
                        "term": translated_term,
                        "english": english_keyword
                    })
        
        recommendations = []
        if keywords_in_english:
            departments = set()
            for keyword in keywords_in_english:
                if keyword in symptom_to_department:
                    for dept in symptom_to_department[keyword]:
                        departments.add(dept)
            
            for dept in departments:
                if target_lang in department_translations.get(dept, {}):
                    recommendations.append(department_translations[dept][target_lang])

        visual_aid_url = None
        if keywords_in_english:
            for keyword in keywords_in_english:
                if keyword in keyword_to_visual:
                    visual_aid_url = keyword_to_visual[keyword]
                    break # Show the first relevant image found

        unique_keywords_data = [dict(t) for t in {tuple(d.items()) for d in keywords_data}]

        return jsonify({
            "translatedText": translated_text,
            "keywords": unique_keywords_data,
            "recommendations": recommendations,
            "visualAid": visual_aid_url
        })

    except Exception as e:
        print(f"Translation error: {e}")
        return jsonify({"error": "Translation service failed."}), 500

# Endpoint to process image using Tesseract
@app.route('/process_image', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    try:
        # Use Tesseract for actual OCR
        image = Image.open(file.stream)
        extracted_text = pytesseract.image_to_string(image)
        
        if not extracted_text.strip():
            return jsonify({"error": "Could not extract text from the image."}), 400
        
        # Return the extracted text to the frontend
        return jsonify({"extractedText": extracted_text})

    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({"error": f"Failed to process image: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)

