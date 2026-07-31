from __future__ import annotations
from openai import OpenAI
from .config import OPENAI_API_KEY, OPENAI_MODEL

_client = OpenAI(api_key=OPENAI_API_KEY or None)

def summarize(title: str, text: str) -> str:
    """
    Возвращает короткую выжимку. Использует OpenAI Responses API.
    """
    prompt = (
        "Кратко перескажи новость 2-3 предложениями на русском. "
        "Без кликбейта, без лишней воды. Укажи факт(ы) и контекст.\n\n"
        f"Заголовок: {title}\nТекст: {text}\n"
    )
    resp = _client.responses.create(
        model=OPENAI_MODEL,
        input=[{"role": "user", "content": prompt}],
        max_output_tokens=220
    )
    # В SDK есть удобное свойство output_text
    return getattr(resp, "output_text", "").strip() or str(resp)
