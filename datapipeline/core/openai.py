import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_keywords(text):
    prompt = f"Extract key phrases and keywords from the following text:\n{text[:1000]}"
    response = openai.Completion.create(
        engine="gpt-4",
        prompt=prompt,
        max_tokens=100
    )
    return response["choices"][0]["text"].strip()

def generate_embedding(text):
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    return response['data'][0]['embedding']
