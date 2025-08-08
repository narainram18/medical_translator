from libre_translate_api import LibreTranslateAPI

lt = LibreTranslateAPI("http://localhost:5000/")  # Replace if your server runs on another port
text = "i have cancer"

languages = {
    "Arabic": "ar",
    "Bengali": "bn",
    "Chinese": "zh",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es"
}


for lang_name, lang_code in languages.items():
    try:
        translated = lt.translate(text, source="en", target=lang_code)
        print(f"{lang_name}: {translated}")
    except Exception as e:
        print(f"{lang_name} failed: {e}")
