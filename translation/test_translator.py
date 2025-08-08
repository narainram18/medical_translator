import speech_recognition as sr
import argostranslate.package
import argostranslate.translate
from gtts import gTTS
import os
import sys

# Supported output languages
LANGUAGES = {
    "hi": "Hindi",
    "es": "Spanish",
    "de": "German"
}

FROM_LANGUAGE_CODE = "en"

# Expanded medical glossary
medical_glossary = {
    "fever": {"hi": "बुखार", "es": "fiebre", "de": "Fieber"},
    "cough": {"hi": "खांसी", "es": "tos", "de": "Husten"},
    "headache": {"hi": "सिरदर्द", "es": "dolor de cabeza", "de": "Kopfschmerzen"},
    "vomiting": {"hi": "उल्टी", "es": "vómito", "de": "Erbrechen"},
    "blood pressure": {"hi": "रक्तचाप", "es": "presión arterial", "de": "Blutdruck"},
    "diabetes": {"hi": "मधुमेह", "es": "diabetes", "de": "Diabetes"},
    "chest pain": {"hi": "सीने में दर्द", "es": "dolor en el pecho", "de": "Brustschmerzen"},
    "cold": {"hi": "सर्दी", "es": "resfriado", "de": "Erkältung"},
    "asthma": {"hi": "दमा", "es": "asma", "de": "Asthma"},
    "infection": {"hi": "संक्रमण", "es": "infección", "de": "Infektion"},
    "injury": {"hi": "चोट", "es": "lesión", "de": "Verletzung"},
    "fracture": {"hi": "फ्रैक्चर", "es": "fractura", "de": "Fraktur"},
    "burn": {"hi": "जलना", "es": "quemadura", "de": "Verbrennung"},
    "allergy": {"hi": "एलर्जी", "es": "alergia", "de": "Allergie"},
    "high temperature": {"hi": "तेज़ बुखार", "es": "alta temperatura", "de": "hohes Fieber"},
    "low blood pressure": {"hi": "कम रक्तचाप", "es": "presión baja", "de": "niedriger Blutdruck"},
    "heart attack": {"hi": "दिल का दौरा", "es": "ataque al corazón", "de": "Herzinfarkt"},
    "stroke": {"hi": "स्ट्रोक", "es": "derrame cerebral", "de": "Schlaganfall"},
    "cancer": {"hi": "कैंसर", "es": "cáncer", "de": "Krebs"},
    "tumor": {"hi": "गांठ", "es": "tumor", "de": "Tumor"},
    "pregnancy": {"hi": "गर्भावस्था", "es": "embarazo", "de": "Schwangerschaft"},
    "labor pain": {"hi": "प्रसव पीड़ा", "es": "dolor de parto", "de": "Wehenschmerz"},
    "delivery": {"hi": "प्रसव", "es": "parto", "de": "Entbindung"},
    "urine infection": {"hi": "मूत्र संक्रमण", "es": "infección urinaria", "de": "Harnwegsinfektion"},
    "painkiller": {"hi": "दर्द निवारक", "es": "analgésico", "de": "Schmerzmittel"},
    "surgery": {"hi": "सर्जरी", "es": "cirugía", "de": "Operation"},
    "operation": {"hi": "ऑपरेशन", "es": "operación", "de": "Operation"},
    "oxygen": {"hi": "ऑक्सीजन", "es": "oxígeno", "de": "Sauerstoff"},
    "anemia": {"hi": "खून की कमी", "es": "anemia", "de": "Anämie"},
    "jaundice": {"hi": "पीलिया", "es": "ictericia", "de": "Gelbsucht"},
    "diarrhea": {"hi": "दस्त", "es": "diarrea", "de": "Durchfall"},
    "constipation": {"hi": "कब्ज", "es": "estreñimiento", "de": "Verstopfung"},
    "medicine": {"hi": "दवा", "es": "medicina", "de": "Medikament"},
    "doctor": {"hi": "डॉक्टर", "es": "médico", "de": "Arzt"},
    "nurse": {"hi": "नर्स", "es": "enfermera", "de": "Krankenschwester"},
    "hospital": {"hi": "अस्पताल", "es": "hospital", "de": "Krankenhaus"},
}

def setup_translation_models():
    print("🔧 Checking/installing translation models...")
    argostranslate.package.update_package_index()
    installed = argostranslate.package.get_installed_packages()
    available = argostranslate.package.get_available_packages()

    for to_lang in LANGUAGES.keys():
        if not any(p.from_code == FROM_LANGUAGE_CODE and p.to_code == to_lang for p in installed):
            pkg = next((p for p in available if p.from_code == FROM_LANGUAGE_CODE and p.to_code == to_lang), None)
            if pkg:
                print(f"⬇️ Installing model: {FROM_LANGUAGE_CODE} → {to_lang}")
                pkg.install()
            else:
                print(f"❌ Model for {FROM_LANGUAGE_CODE} → {to_lang} not found")

def enhance_with_medical_terms(text, lang_code):
    for term, translations in medical_glossary.items():
        if term.lower() in text.lower() and lang_code in translations:
            text = text.replace(term.lower(), translations[lang_code])
    return text

def speak_text(text, lang_code):
    try:
        tts = gTTS(text=text, lang=lang_code)
        filename = f"speech_{lang_code}.mp3"
        tts.save(filename)
        os.system(f"start {filename}" if sys.platform == "win32" else f"xdg-open {filename}")
    except Exception as e:
        print(f"❌ TTS Error: {e}")

def main():
    setup_translation_models()
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("\n🎙️ Speak in English...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            print("🧠 Recognizing using Whisper...")
            text = recognizer.recognize_whisper(audio, language="english")
            print(f"\n🗣️ You said: {text}")

            # Translate and speak in each language
            for lang_code, lang_name in LANGUAGES.items():
                translated = argostranslate.translate.translate(text, FROM_LANGUAGE_CODE, lang_code)
                translated = enhance_with_medical_terms(translated, lang_code)

                print(f"\n🌍 Translated to {lang_name}: {translated}")
                speak_text(translated, lang_code)

    except sr.UnknownValueError:
        print("❌ Could not understand audio. Please try again.")
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
