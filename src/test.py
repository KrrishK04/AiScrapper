import google.generativeai as genai

genai.configure(api_key="AIzaSyC32Crt1UatpRmXlmV2Xgz7Npp-eYfYH2A")
model = genai.GenerativeModel("gemini-1.5-pro")
try:
    response = model.generate_content("Hello, gemini!")
    print(response)
except Exception as e:
    print("Error:", e)