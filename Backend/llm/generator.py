import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-3.8-flash")


def generate_answer(query, context, citations):
    """
    Generate grounded answer with Gemini.
    Includes page citations.
    """

    prompt = f"""
    You are an AI assistant answering from a PDF.

    Context (retrieved from PDF):
    {context}

    Question:
    {query}

    Rules:
    - Answer only from context
    - Mention page citations at end

    Citations: {citations}
    """

    response = model.generate_content(prompt)

    return response.text
