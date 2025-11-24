import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load env vars from .env
load_dotenv()

API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_AI_API_KEY environment variable is not set")

client = genai.Client(api_key=API_KEY)

SYSTEM_INSTRUCTION = """
You are PinkCycle's friendly menstrual health assistant.

Your job:
- Answer FAQs about menstruation, cycles, PMS, period tracking, fertility windows,
  and how to use the PinkCycle app.
- Be gentle, non-judgmental, and clear.
- You are NOT a doctor and you MUST NOT diagnose or prescribe treatment.
- For anything serious, irregular, painful, or worrying, always recommend that the
  user talk to a qualified healthcare professional in their country.

Tone:
- Calm, supportive, and empowering.
- Aimed at young women and people who menstruate.
"""


def answer_faq(question: str, app_context: str | None = None) -> str:
    """
    Call Gemini 2.5 Flash to answer a single FAQ-style question.
    """

    prompt = f"""
{SYSTEM_INSTRUCTION}

App context:
{app_context or "PinkCycle is a menstrual cycle tracking app with predictions and a pink, butterfly-themed UI."}

User question:
{question}

Now give a friendly, clear answer in a few short paragraphs.
Do not give medical diagnoses or prescriptions. Encourage the user to see a doctor for anything severe or worrying.
""".strip()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=512,
        ),
    )

    # 1) First try the convenience .text accessor
    text = getattr(response, "text", None)
    if text:
        text = text.strip()
        if text:
            return text

    # 2) Fallback: manually stitch together candidate parts, if present
    try:
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            parts = getattr(candidates[0].content, "parts", [])
            collected = []
            for p in parts:
                # part.text exists for normal text output
                pt = getattr(p, "text", None)
                if pt:
                    collected.append(pt)
            text = "\n".join(collected).strip()
            if text:
                return text
    except Exception as e:
        print("Error extracting text from Gemini response:", e)

    # 3) If still nothing, return a short generic message.
    return (
        "I’m having trouble forming a helpful answer right now. "
        "Please try asking in a slightly different way, or talk to a healthcare professional "
        "for personalised advice. 💕"
    )
