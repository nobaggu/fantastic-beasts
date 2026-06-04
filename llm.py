import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_prompt(query: str, context_beasts: list[dict]) -> str:
    context_blocks = []
    for b in context_beasts:
        block = f"""
[{b['name']}]
출처: {b.get('source', '')}
동물 구성: {', '.join(b.get('animals', []))}
원문: {b.get('original', '')}
번역: {b.get('translated', '')}
""".strip()
        context_blocks.append(block)

    context_str = "\n\n".join(context_blocks)

    return f"""당신은 고대 동양 신화의 신비한 동물들을 소개하는 동물사전입니다.
아래 고문헌 자료를 바탕으로 사용자의 질문에 한국어로 답하세요.
자료에 없는 내용은 추측하지 말고, 출처를 언급해 주세요.

[참고 자료]
{context_str}

[사용자 질문]
{query}"""


def ask_llm(query: str, context_beasts: list[dict]) -> str:
    prompt = build_prompt(query, context_beasts)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content
