from transformers import pipeline

# Load model kecil (otomatis download pertama kali)
generator = pipeline(
    "text-generation",
    model="gpt2"
)

prompt = """
Buat analisis kondisi ketenagakerjaan di Indonesia berdasarkan 5 berita prioritas tinggi terkait PHK dan konflik industri.
"""

result = generator(
    prompt,
    max_length=200,
    num_return_sequences=1
)

print(result[0]["generated_text"])