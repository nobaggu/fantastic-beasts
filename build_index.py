"""
임베딩 인덱스 사전 빌드 스크립트
서버 실행 전에 한 번 실행하면 빠르게 로드됩니다.

사용법: python build_index.py
"""

from rag import build_index

if __name__ == "__main__":
    build_index()
