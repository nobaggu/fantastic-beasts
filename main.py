"""
신비한 동물사전 RAG API 서버

실행: uvicorn main:app --reload

엔드포인트:
  POST /ask         - 질문하면 RAG로 답변
  GET  /beasts      - 전체 동물 목록
  GET  /beasts/{name} - 특정 동물 상세
"""

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

import rag
from llm import ask_llm

DB_PATH = Path(__file__).parent / "db.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 인덱스 미리 로드
    rag.load_index()
    yield


app = FastAPI(
    title="신비한 동물사전 API",
    description="산해경 기반 신비한 동물 RAG 검색 API",
    version="1.0.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    query: str
    top_k: int = 2  # 검색할 유사 동물 수


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """
    자연어 질문을 받아 관련 동물 데이터를 검색하고 LLM으로 답변합니다.

    - **query**: 질문 (예: "날개 달린 동물 알려줘", "구미호가 뭐야?")
    - **top_k**: 참고할 동물 수 (기본값 2)
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query가 비어있습니다.")

    # 1. 벡터 검색으로 관련 동물 retrieve
    retrieved = rag.retrieve(req.query, top_k=req.top_k)

    # 2. LLM으로 답변 생성
    answer = ask_llm(req.query, retrieved)

    # 3. sources에서 내부 필드 제거
    sources = [{k: v for k, v in b.items() if not k.startswith("_")} for b in retrieved]

    return AskResponse(answer=answer, sources=sources)


@app.get("/beasts")
def list_beasts():
    """전체 동물 목록을 반환합니다."""
    with open(DB_PATH, encoding="utf-8") as f:
        db = json.load(f)
    return {"total": len(db["beasts"]), "beasts": db["beasts"]}


@app.get("/beasts/{name}")
def get_beast(name: str):
    """
    이름으로 특정 동물을 조회합니다.

    - **name**: 동물 이름 (예: 구미호, 궁기)
    """
    with open(DB_PATH, encoding="utf-8") as f:
        db = json.load(f)

    for beast in db["beasts"]:
        if beast["name"] == name:
            return beast

    raise HTTPException(status_code=404, detail=f"'{name}' 동물을 찾을 수 없습니다.")


@app.get("/")
def root():
    return {"message": "신비한 동물사전 API. /docs 에서 API 문서를 확인하세요."}
