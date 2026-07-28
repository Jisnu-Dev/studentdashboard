from google import genai
from google.genai import types

API_KEY = "AIzaSyAqYtT3sRnzhdFCGAObyL2NxhhmV4piMLc"
client = genai.Client(api_key=API_KEY)

# Test newer 3.x models with streaming (as required by some models)
candidates = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]

for model in candidates:
    try:
        # Try streaming (required by some newer models)
        chunks = []
        for chunk in client.models.generate_content_stream(
            model=model,
            contents="Say hello in one sentence.",
        ):
            if chunk.text:
                chunks.append(chunk.text)
        text = "".join(chunks)
        if text:
            print(f"[OK] {model}: {text[:100]}")
            break
        else:
            print(f"[EMPTY] {model}: no text returned")
    except Exception as e:
        msg = str(e)[:120]
        print(f"[FAIL] {model}: {msg}")
