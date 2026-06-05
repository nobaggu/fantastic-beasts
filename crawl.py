"""
나무위키 크롤러 + GPT 구조화 파이프라인

동아시아 신화 동물 50~60개를 크롤링해서 db.json에 추가합니다.

사용법: python crawl.py
"""

import requests
import json
import time
import os
import random
import string
from datetime import datetime
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── 이미 존재하는 동물 (중복 방지) ──────────────────────────────
EXISTING = {"궁기", "구미호", "예조", "금충", "대청사", "마팍고왕", "등룡", "록촉", "선구", "능어"}

# ── 크롤링 대상 목록 (동아시아 공통 + 중화권 산해경 위주) ─────────
TARGETS = [
    # 동아시아 공통
    "봉황", "기린", "청룡", "백호", "주작", "현무", "해태", "삼족오",
    "교인", "맥", "달토끼", "용",
    # 한반도
    "이무기", "도깨비", "불가사리", "불개", "삼족섬", "영노",
    # 중화권 - 산해경/신화
    "치우", "백택", "도철", "혼돈", "붕", "응룡", "기",
    "짐새", "알유", "상류", "시랑", "팽후", "천호",
    "착치", "화사", "도견", "무지기", "치조", "청조",
    "상양", "백악", "규룡", "창귀", "비두만", "식양",
    "비", "박", "추이", "천구", "폐폐", "나찰",
    "강시", "후", "년", "분운", "수호",
]

DB_PATH = "db.json"
DATA_DIR = "data"


def gen_id(n=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def fetch_namu(name: str) -> str | None:
    """나무위키 페이지에서 본문 텍스트 추출"""
    url = f"https://namu.wiki/w/{requests.utils.quote(name)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
       


        if res.status_code != 200:
            print(f"  ✗ HTTP {res.status_code}: {name}")
            return None
        soup = BeautifulSoup(res.text, "html.parser")
        # 본문 영역 추출 (나무위키 구조)
        article = soup.find("article")

        if not article:
            candidates = soup.find_all("div")
            longest = ""

            for div in candidates:
                text = div.get_text(separator="\n", strip=True)
                if len(text) > len(longest):
                    longest = text

            if len(longest) < 100:
                print(f"  ✗ 본문 없음: {name}")
                return None

            return longest[:2000]
         
        # 불필요한 태그 제거
        for tag in article.find_all(["script", "style", "table"]):
            tag.decompose()
        text = article.get_text(separator="\n", strip=True)
        # 너무 짧으면 패스
        if len(text) < 100:
            print(f"  ✗ 내용 부족: {name}")
            return None
        # 앞 2000자만 사용 (GPT 비용 절감)
        return text[:2000]
    except Exception as e:
        print(f"  ✗ 오류: {name} - {e}")
        return None


def gpt_extract(name: str, raw_text: str) -> dict | None:
    """GPT로 텍스트를 JSON 스키마에 맞게 구조화"""
    prompt = f"""다음은 나무위키의 '{name}' 문서 내용입니다.
이 내용을 바탕으로 아래 JSON 형식으로 정리해주세요.

규칙:
- animals: 이 동물의 신체를 구성하는 동물 요소들 (예: ["뱀", "새", "물고기"])
- original: 고문헌 원문이 있으면 한자로, 없으면 빈 문자열
- translated: 이 동물에 대한 한국어 설명 (2~4문장, 나무위키 내용 기반)
- source: 출처 (예: "산해경", "한국 민간신화", "나무위키" 등)
- comment: 이 동물에 대한 짧고 흥미로운 한 줄 감상

반드시 JSON만 반환하고, 다른 텍스트는 포함하지 마세요.

{{
  "animals": [],
  "original": "",
  "translated": "",
  "source": "",
  "comment": ""
}}

문서 내용:
{raw_text}"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",  # 비용 절감용 mini 모델
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            response_format={"type": "json_object"},
        )
        data = json.loads(res.choices[0].message.content)
        return data
    except Exception as e:
        print(f"  ✗ GPT 오류: {name} - {e}")
        return None


def save_to_data_dir(beast: dict):
    """data/ 폴더에 개별 JSON 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    safe_name = beast["name"].replace("/", "_")
    path = os.path.join(DATA_DIR, f"crawled_{safe_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(beast, f, ensure_ascii=False, indent=4)


def load_db() -> list:
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f).get("beasts", [])


def save_db(beasts: list):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump({"beasts": beasts}, f, ensure_ascii=False, indent=4)


def main():
    beasts = load_db()
    existing_names = {b["name"] for b in beasts} | EXISTING
    print(f"기존 동물 수: {len(beasts)}개\n")

    added = 0
    for name in TARGETS:
        if name in existing_names:
            print(f"  → 스킵 (이미 존재): {name}")
            continue

        print(f"크롤링 중: {name}")

        # 1. 나무위키 텍스트 수집
        raw = fetch_namu(name)
        if not raw:
            time.sleep(1)
            continue

        # 2. GPT로 구조화
        extracted = gpt_extract(name, raw)
        if not extracted:
            time.sleep(1)
            continue

        # 3. 최종 beast 객체 조립
        beast = {
            "student_id": "crawled",
            "name": name,
            "image": "",
            "image_prompt": "",
            "animals": extracted.get("animals", []),
            "original": extracted.get("original", ""),
            "translated": extracted.get("translated", ""),
            "source": extracted.get("source", "나무위키"),
            "comment": extracted.get("comment", ""),
            "id": gen_id(),
            "created_at": datetime.now().isoformat(),
        }

        # 4. 저장
        save_to_data_dir(beast)
        beasts.append(beast)
        existing_names.add(name)
        added += 1
        print(f"  ✓ 완료: {name} ({added}개 추가됨)")

        # 나무위키 서버 부하 방지 (1~2초 간격)
        time.sleep(random.uniform(1.0, 2.0))

    save_db(beasts)
    print(f"\n완료! 총 {added}개 추가 → 전체 {len(beasts)}개")
    print("이제 'python build_index.py'를 실행해서 인덱스를 갱신하세요.")


if __name__ == "__main__":
    main()
