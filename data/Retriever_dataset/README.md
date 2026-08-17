# Retriever Dataset

## Project

다국어 금융 상황 이해 AI Agent

## Retriever Corpus Summary

### Documents

- Total : 21
- PDF : 8
- WEB : 13

### Language

- KO : 15
- EN : 6

### Categories

general_finance, bank_account, credit_card, remittance, foreign_exchange, financial_fraud, smishing, fraud_response

## Chunk Versions

| Version | Chunk Size | Overlap | Chunk Count |
|---|---|---|---|
| 300 / 50 | 300 tokens | 50 tokens | 1,096 |
| **400 / 60 (Recommended)** | 400 tokens | 60 tokens | 824 |
| 500 / 80 | 500 tokens | 80 tokens | 674 |

Token counts are measured with the `cl100k_base` tokenizer (tiktoken). Chunking was performed with a `RecursiveCharacterTextSplitter` (token-based, separators `["\n\n", "\n", ". ", "。", " ", ""]`) to preserve paragraph, FAQ Q/A, and table structure as much as possible.

## Folder Structure

```
Retriever_dataset/
├── README.md
├── documents/
│   └── documents.jsonl              (21 documents, full corpus)
├── chunks/
│   ├── chunk_300_50/chunks.jsonl    (1,096 chunks)
│   ├── chunk_400_60/chunks.jsonl    (824 chunks, recommended)
│   └── chunk_500_80/chunks.jsonl    (674 chunks)
└── metadata/
    ├── corpus_statistics.json
    ├── duplicate_report.json
    ├── chunk_statistics_300_50.json
    ├── chunk_statistics_400_60.json
    └── chunk_statistics_500_80.json
```

## Recommended Retriever Input

`documents/documents.jsonl`

## Recommended Chunk

`chunks/chunk_400_60/chunks.jsonl`

## Chunk Metadata Schema

Every chunk record has the following fields, in this order:

```json
{
  "chunk_id": "WEB009_0001",
  "doc_id": "WEB009",
  "title": "...",
  "organization": "...",
  "language": "...",
  "category": "...",
  "source_type": "...",
  "source_url": "...",
  "text": "..."
}
```

`chunk_id` = `{doc_id}_{sequence number, 4-digit zero-padded}`. All other fields except `text` are copied unchanged from the parent document.

## Notes

- PDF/Web schema unified (10-field common schema: id, title, organization, language, category, source_type, source_url, source_file, retrieved_at, text)
- UTF-8
- Valid JSON (all documents and all chunks)
- No duplicate `chunk_id` across any chunk version
- No empty `text` fields
- Hybrid Retrieval ready (BM25 / Dense / Hybrid / Hybrid + Reranker)

### Known minor limitation

A very small fraction of chunks (<1% in every version) consist only of a page marker or section-title line (e.g. `[Page 74]`) with no other content, produced where a PDF page break falls on its own paragraph. These are low-information chunks and are expected to rarely surface in retrieval results; they were not removed so that chunk boundaries stay a direct, unmodified function of the source text.
