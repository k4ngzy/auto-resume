from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import chromadb
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

DEFAULT_COLLECTION = "offline_jobs"
DEFAULT_MODEL = "Qwen/Qwen3-Embedding-0.6B"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "backend" / "chromadb_data"
DEFAULT_SOURCE_PATH = Path(__file__).resolve().parent.parent / "backend" / "data" / "offline_jobs.jsonl"


def load_jobs_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    # 加载数据
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def count_jsonl_lines(path: Path) -> int:
    count = 0
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def _safe_text(value: Any) -> str:
    # 清洗文本
    if value is None:
        return ""
    return str(value).strip()


def make_job_id(job: Dict[str, Any]) -> str:
    # 生成唯一ID
    key = "|".join(
        [
            _safe_text(job.get("公司名称")),
            _safe_text(job.get("职位名称")),
            _safe_text(job.get("岗位描述")),
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def build_job_document(job: Dict[str, Any]) -> str:
    # 构建embedding文本内容
    fields = [
        ("职位名称", job.get("职位名称")),
        ("所需技能", job.get("所需技能")),
        ("岗位描述", job.get("岗位描述")),
    ]
    parts = [f"{label}: {_safe_text(value)}" for label, value in fields if _safe_text(value)]
    return "\n".join(parts)


def build_job_metadata(job: Dict[str, Any]) -> Dict[str, str]:
    # 构建metadata
    metadata = {
        "公司名称": _safe_text(job.get("公司名称")),
        "职位名称": _safe_text(job.get("职位名称")),
        "工作地点": _safe_text(job.get("工作地点")),
        "薪资范围": _safe_text(job.get("薪资范围")),
        "工作经验": _safe_text(job.get("工作经验")),
        "学历要求": _safe_text(job.get("学历要求")),
        "职位标签": _safe_text(job.get("职位标签")),
        "所需技能": _safe_text(job.get("所需技能")),
        "公司规模": _safe_text(job.get("公司规模")),
        "公司阶段": _safe_text(job.get("公司阶段")),
        "所属行业": _safe_text(job.get("所属行业")),
        "岗位描述": _safe_text(job.get("岗位描述")),
        "job_category": _safe_text(job.get("job_category")),
        "job_code": _safe_text(job.get("job_code")),
    }
    return metadata


def load_embedding_model(
    model_name: str = DEFAULT_MODEL,
    device: str = "cuda",
    local_only: bool = True,
) -> SentenceTransformer:
    # 加载embedding模型
    return SentenceTransformer(
        model_name,
        device=device,
        trust_remote_code=True,
        local_files_only=local_only,
    )


def get_collection(
    db_path: Path,
    collection_name: str,
    reset: bool = False,
) -> chromadb.Collection:
    # 获取或创建ChromaDB集合
    client = chromadb.PersistentClient(path=str(db_path))
    if reset:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
    return client.get_or_create_collection(
        collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def add_job_batch(
    collection: chromadb.Collection,
    model: SentenceTransformer,
    documents: List[str],
    metadatas: List[Dict[str, str]],
    ids: List[str],
    batch_size: int,
) -> None:
    # 批量添加数据到集合
    with torch.no_grad():
        embeddings = model.encode(
            documents,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings.tolist(),
    )


def build_job_index(
    source_path: Path = DEFAULT_SOURCE_PATH,
    db_path: Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION,
    model_name: str = DEFAULT_MODEL,
    device: str = "cuda",
    batch_size: int = 32,
    max_items: Optional[int] = None,
    reset: bool = False,
    local_only: bool = True,
) -> int:
    # 构建职位数据索引
    collection = get_collection(db_path, collection_name, reset=reset)
    model = load_embedding_model(model_name=model_name, device=device, local_only=local_only)

    seen_ids: set[str] = set()
    docs_batch: List[str] = []
    metas_batch: List[Dict[str, str]] = []
    ids_batch: List[str] = []
    total = 0

    total_lines = count_jsonl_lines(source_path)
    if max_items:
        total_lines = min(total_lines, max_items)
    progress = tqdm(total=total_lines, desc="Indexing jobs", unit="job")
    for job in load_jobs_jsonl(source_path):
        job_id = make_job_id(job)
        if job_id in seen_ids:
            progress.update(1)
            continue
        seen_ids.add(job_id)

        document = build_job_document(job)
        if not document:
            progress.update(1)
            continue

        docs_batch.append(document)
        metas_batch.append(build_job_metadata(job))
        ids_batch.append(job_id)
        total += 1

        if max_items and total >= max_items:
            progress.update(1)
            break

        if len(docs_batch) >= batch_size:
            add_job_batch(collection, model, docs_batch, metas_batch, ids_batch, batch_size=batch_size)
            docs_batch = []
            metas_batch = []
            ids_batch = []
        progress.update(1)

    if docs_batch:
        add_job_batch(collection, model, docs_batch, metas_batch, ids_batch, batch_size=batch_size)
    progress.close()

    return total


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Chroma index from offline jobs JSONL.")
    parser.add_argument("--source-path", default=str(DEFAULT_SOURCE_PATH))
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-items", type=int, default=None)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--allow-remote", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    total = build_job_index(
        source_path=Path(args.source_path),
        db_path=Path(args.db_path),
        collection_name=args.collection,
        model_name=args.model,
        device=args.device,
        batch_size=args.batch_size,
        max_items=args.max_items,
        reset=args.reset,
        local_only=not args.allow_remote,
    )

    print(f"Indexed {total} jobs into {args.collection} at {args.db_path}")


if __name__ == "__main__":
    main()
