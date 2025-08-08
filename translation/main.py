from libre_translate_api import LibreTranslateAPI

# Connect to your local LibreTranslate server
lt = LibreTranslateAPI("http://localhost:5000/")

text = "This is a test translation."

print("Original:", text)
print("Hindi:", lt.translate(text, source="en", target="hi"))
print("Spanish:", lt.translate(text, source="en", target="es"))
print("German:", lt.translate(text, source="en", target="de"))
