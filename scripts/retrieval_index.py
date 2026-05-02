#!/usr/bin/env python3
from __future__ import annotations

import re
import sqlite3
from typing import Any


def normalize_query_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def unique_items(items: list[str], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if limit is not None and len(result) >= limit:
            break
    return result


def extract_query_terms(text: Any, limit: int = 32) -> list[str]:
    normalized = normalize_query_text(text)
    terms: set[str] = set()
    for segment in re.findall(r"[a-z0-9_+-]+|[\u4e00-\u9fff]+", normalized):
        if not segment:
            continue
        if re.fullmatch(r"[a-z0-9_+-]+", segment):
            if len(segment) >= 2:
                terms.add(segment)
            continue
        terms.add(segment)
        for size in (4, 3, 2):
            if len(segment) < size:
                continue
            for index in range(len(segment) - size + 1):
                terms.add(segment[index : index + size])
    return sorted(terms, key=lambda item: (-len(item), item))[:limit]


def field_values(entry: dict[str, Any], field_weights: dict[str, float]) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for field in field_weights:
        raw_value = entry.get(field)
        if isinstance(raw_value, list):
            values[field] = [normalize_query_text(item) for item in raw_value if normalize_query_text(item)]
        else:
            text = normalize_query_text(raw_value)
            values[field] = [text] if text else []
    return values


def build_document_text(entry: dict[str, Any], field_weights: dict[str, float]) -> str:
    chunks: list[str] = []
    for values in field_values(entry, field_weights).values():
        chunks.extend(values)
        for value in values:
            chunks.extend(extract_query_terms(value, limit=64))
    return " ".join(unique_items(chunks))


def quote_fts_term(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def sqlite_fts_scores(
    catalog: list[dict[str, Any]],
    query_text: str,
    field_weights: dict[str, float],
) -> dict[str, dict[str, float]]:
    terms = extract_query_terms(query_text, limit=16)
    if not terms:
        return {}
    match_query = " OR ".join(quote_fts_term(term) for term in terms)

    try:
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE VIRTUAL TABLE entries USING fts5(case_id UNINDEXED, content)")
    except sqlite3.Error:
        return {}

    try:
        rows = [
            (str(entry.get("caseId") or "").strip(), build_document_text(entry, field_weights))
            for entry in catalog
            if str(entry.get("caseId") or "").strip()
        ]
        connection.executemany("INSERT INTO entries(case_id, content) VALUES (?, ?)", rows)
        cursor = connection.execute(
            "SELECT case_id, bm25(entries) AS rank FROM entries WHERE entries MATCH ?",
            (match_query,),
        )
        scores: dict[str, dict[str, float]] = {}
        for case_id, rank in cursor.fetchall():
            raw_rank = float(rank or 0.0)
            scores[str(case_id)] = {
                "bm25Score": round(max(0.0, -raw_rank), 6),
                "ftsBonus": 2.0,
            }
        return scores
    except sqlite3.Error:
        return {}
    finally:
        connection.close()


def field_match_evidence(
    entry: dict[str, Any],
    query_text: str,
    terms: list[str],
    field_weights: dict[str, float],
) -> dict[str, Any]:
    normalized_query = normalize_query_text(query_text)
    values_by_field = field_values(entry, field_weights)
    field_hits: list[dict[str, Any]] = []
    matched_terms: list[str] = []
    why_matched: list[str] = []
    score = 0.0

    keywords = [normalize_query_text(item) for item in ensure_list(entry.get("keywords"))]
    exact_keyword_hits = [
        keyword
        for keyword in keywords
        if keyword and (keyword in normalized_query or normalized_query in keyword or keyword in terms)
    ]
    for keyword in exact_keyword_hits:
        why_matched.append(f"exact_keyword:{keyword}")
        matched_terms.append(keyword)
        score += 5.0

    for field, weight in field_weights.items():
        values = values_by_field.get(field, [])
        if not values:
            continue
        query_hit = any(normalized_query and normalized_query in value for value in values)
        term_hits = [term for term in terms if any(term in value for value in values)]
        if not query_hit and not term_hits:
            continue
        field_score = weight * (1.6 if query_hit else 1.0 + 0.15 * min(len(term_hits), 3))
        score += field_score
        hit = {
            "field": field,
            "queryHit": query_hit,
            "terms": unique_items(term_hits, limit=6),
            "weight": weight,
            "score": round(field_score, 4),
        }
        field_hits.append(hit)
        if query_hit:
            why_matched.append(f"{field}:query")
            matched_terms.append(normalized_query)
        if term_hits:
            why_matched.append(f"{field}:{','.join(term_hits[:3])}")
            matched_terms.extend(term_hits[:4])

    return {
        "score": score,
        "fieldHits": field_hits,
        "exactKeywordHits": unique_items(exact_keyword_hits, limit=8),
        "matchedTerms": unique_items(matched_terms, limit=16),
        "whyMatched": unique_items(why_matched, limit=12),
    }


def estimate_false_positive_risk(score: float, why_matched: list[str], matched_terms: list[str]) -> str:
    if score <= 0:
        return "none"
    exact = any(reason.startswith("exact_keyword:") for reason in why_matched)
    direct = any(reason.endswith(":query") for reason in why_matched)
    if score >= 12.0 and (exact or direct) and len(matched_terms) >= 2:
        return "low"
    if score >= 7.0 and (exact or direct or len(why_matched) >= 2):
        return "medium"
    return "high"


def build_retrieval_evidence(
    catalog: list[dict[str, Any]],
    query_text: str,
    store_scope: str,
    field_weights: dict[str, float],
) -> dict[str, dict[str, Any]]:
    terms = extract_query_terms(query_text)
    fts_scores = sqlite_fts_scores(catalog, query_text, field_weights)
    fts_available = bool(fts_scores)
    evidence_by_case: dict[str, dict[str, Any]] = {}

    for entry in catalog:
        case_id = str(entry.get("caseId") or "").strip()
        if not case_id:
            continue
        field_evidence = field_match_evidence(entry, query_text, terms, field_weights)
        fts = fts_scores.get(case_id, {"bm25Score": 0.0, "ftsBonus": 0.0})
        fts_matched = case_id in fts_scores
        retrieval_score = field_evidence["score"] + float(fts.get("ftsBonus", 0.0))
        why_matched = list(field_evidence["whyMatched"])
        if fts_matched:
            why_matched.append("sqlite_fts5:bm25")

        matched_terms = field_evidence["matchedTerms"]
        risk = estimate_false_positive_risk(retrieval_score, why_matched, matched_terms)
        method = "sqlite_fts5" if fts_available else "lexical_fallback"
        evidence_by_case[case_id] = {
            "storeScope": store_scope,
            "caseId": case_id,
            "matched": retrieval_score > 0.0,
            "retrievalMethod": method,
            "retrievalScore": round(retrieval_score, 4),
            "bm25Score": fts["bm25Score"],
            "fieldHits": field_evidence["fieldHits"],
            "exactKeywordHits": field_evidence["exactKeywordHits"],
            "matchedTerms": matched_terms,
            "whyMatched": unique_items(why_matched, limit=12),
            "riskOfFalsePositive": risk,
        }

    return evidence_by_case
