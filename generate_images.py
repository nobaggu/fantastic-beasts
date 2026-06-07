"""
DALL-E 3 이미지 생성 스크립트

image 필드가 비어있는 동물들에 대해 이미지를 생성하고
images/ 폴더에 저장한 뒤 db.json을 업데이트합니다.

사용법: python generate_images.py
예상 비용: 52개 × 약 40원 = 약 2,000원
"""

import json
import os
import time
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_PATH = "db.json"
IMAGES_DIR = "images"


def build_prompt(beast: dict) -> str:
    """동물 데이터로 DALL-E 프롬프트 생성"""
    name = beast.get("name", "")
    animals = ", ".join(beast.get("animals", []))
    translated = beast.get("translated", "")[:200]  # 너무 길면 자름

    return (
        f"An ancient East Asian mythical creature called '{name}'. "
        f"Body composed of: {animals}. "
        f"Description: {translated} "
        f"Style: traditional East Asian ink painting, detailed illustration, "
        f"mystical atmosphere, on a light parchment background. "
        f"No text, no labels."
    )


def generate_and_save(beast: dict) -> str | None:
    """DALL-E 3로 이미지 생성 후 저장, 저장 경로 반환"""
    name = beast["name"]
    prompt = build_prompt(beast)

    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="medium",
            n=1,
        )
        # gpt-image-1은 b64_json으로 반환
        import base64
        img_data = base64.b64decode(response.data[0].b64_json)

        # images/ 폴더에 저장
        os.makedirs(IMAGES_DIR, exist_ok=True)
        filename = f"{name}.png"
        filepath = os.path.join(IMAGES_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(img_data)

        return f"images/{filename}"

    except Exception as e:
        print(f"  ✗ 오류: {name} - {e}")
        return None


def main():
    with open(DB_PATH, encoding="utf-8") as f:
        db = json.load(f)

    beasts = db["beasts"]
    targets = [b for b in beasts if not b.get("image")]
    print(f"이미지 없는 동물: {len(targets)}개\n")
    print(f"예상 비용: {len(targets) * 40:,}원 수준\n")

    updated = 0
    for i, beast in enumerate(targets):
        name = beast["name"]
        print(f"[{i+1}/{len(targets)}] 생성 중: {name}")

        image_path = generate_and_save(beast)
        if image_path:
            # db.json의 해당 항목 업데이트
            for b in beasts:
                if b["id"] == beast["id"]:
                    b["image"] = image_path
                    b["image_prompt"] = build_prompt(beast)
                    break
            updated += 1
            print(f"  ✓ 저장: {image_path}")

        # DALL-E API 속도 제한 (분당 5회)
        if i < len(targets) - 1:
            time.sleep(13)

    # db.json 저장
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump({"beasts": beasts}, f, ensure_ascii=False, indent=4)

    print(f"\n완료! {updated}개 이미지 생성됨")
    print("이제 'python build_index.py'를 실행해서 인덱스를 갱신하세요.")


if __name__ == "__main__":
    main()
