"""
RAG 파이프라인
- 각 동물 데이터를 텍스트로 변환 → 임베딩 벡터 생성
- 쿼리 임베딩과 코사인 유사도로 관련 동물 검색
- LLM에 컨텍스트로 전달
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

DB_PATH = Path(__file__).parent / "db.json"
INDEX_PATH = Path(__file__).parent / "index.npy"
META_PATH = Path(__file__).parent / "index_meta.json"

# 다국어(한국어/한자) 지원 임베딩 모델
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

_model = None
_embeddings = None
_meta = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def beast_to_text(beast: dict) -> str:
    """동물 데이터를 임베딩용 텍스트로 변환"""
    parts = [
        beast.get("name", ""),
        "구성: " + ", ".join(beast.get("animals", [])),
        beast.get("translated", ""),
        beast.get("comment", ""),
        "출처: " + beast.get("source", ""),
    ]
    return " ".join(p for p in parts if p.strip())


def build_index():
    """db.json을 읽어 임베딩 인덱스를 생성하고 저장"""
    with open(DB_PATH, encoding="utf-8") as f:
        db = json.load(f)

    beasts = db["beasts"]
    texts = [beast_to_text(b) for b in beasts]

    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)

    np.save(INDEX_PATH, embeddings)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(beasts, f, ensure_ascii=False, indent=2)

    print(f"인덱스 빌드 완료: {len(beasts)}개 동물")
    return beasts, embeddings


def load_index():
    """저장된 인덱스 로드 (없으면 빌드)"""
    global _embeddings, _meta
    if _embeddings is not None:
        return _meta, _embeddings

    if not INDEX_PATH.exists() or not META_PATH.exists():
        _meta, _embeddings = build_index()
        return _meta, _embeddings

    _embeddings = np.load(INDEX_PATH)
    with open(META_PATH, encoding="utf-8") as f:
        _meta = json.load(f)
    return _meta, _embeddings


def retrieve(query: str, top_k: int = 2) -> list[dict]:
    """쿼리와 코사인 유사도가 높은 동물 top_k개 반환"""
    beasts, embeddings = load_index()
    model = _get_model()

    query_vec = model.encode([query], normalize_embeddings=True)[0]
    # 코사인 유사도 = 정규화된 벡터의 내적
    scores = embeddings @ query_vec
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        beast = dict(beasts[idx])
        beast["_score"] = float(scores[idx])
        results.append(beast)
    return results
