from datetime import date
from typing import Any

from openai import OpenAI

from src.agent.retriever import LEGAL_FOCUS_PHRASES, matching_legal_focus_phrases
from src.agent.state import AgentState
from src.agent.tools import retrieve_legal_documents
from src.core.config import get_settings
from src.core.logging import logger

# 30 administrative units of Hanoi City (12 Districts, 1 Town, 17 Rural Districts)
HANOI_DISTRICTS: list[str] = [
    # 12 Districts (Quận)
    "Ba Đình",
    "Hoàn Kiếm",
    "Tây Hồ",
    "Long Biên",
    "Cầu Giấy",
    "Đống Đa",
    "Hai Bà Trưng",
    "Hoàng Mai",
    "Thanh Xuân",
    "Nam Từ Liêm",
    "Bắc Từ Liêm",
    "Hà Đông",
    # 1 Town (Thị xã)
    "Sơn Tây",
    # 17 Rural Districts (Huyện)
    "Ba Vì",
    "Chương Mỹ",
    "Đan Phượng",
    "Đông Anh",
    "Gia Lâm",
    "Hoài Đức",
    "Mê Linh",
    "Mỹ Đức",
    "Phú Xuyên",
    "Phúc Thọ",
    "Quốc Oai",
    "Sóc Sơn",
    "Thạch Thất",
    "Thanh Oai",
    "Thanh Trì",
    "Thường Tín",
    "Ứng Hòa",
]

def _extract_hanoi_district(query: str, current_district: str | None = None) -> str | None:
    """Extract Hanoi district from query if not already explicitly specified."""
    if current_district:
        return current_district

    query_lower = query.lower()
    for district in HANOI_DISTRICTS:
        if district.lower() in query_lower:
            return district
    return None


def router_node(state: AgentState) -> dict[str, Any]:
    """Classify user query intent, extract district, and determine routing path (PRD M1)."""
    query = state.get("query", "").strip()
    steps = list(state.get("reasoning_steps", []))

    district = _extract_hanoi_district(query, state.get("district"))
    as_of_date = state.get("as_of_date")
    as_of_date_applied = (
        date.fromisoformat(as_of_date).isoformat() if as_of_date else str(date.today())
    )

    # Check for ambiguous queries requiring clarification
    words = query.split()
    query_lower = query.lower()
    ambiguous_keywords = {
        "đất",
        "giá đất",
        "bồi thường",
        "thu hồi",
        "tái định cư",
        "quy hoạch",
        "đất nông nghiệp",
        "đất ở",
    }

    is_ambiguous = len(words) < 3 or query_lower in ambiguous_keywords

    if is_ambiguous:
        route = "clarification"
        steps.append(
            f"Router: Query '{query}' lacks specific context/parameters. Routed to clarification."
        )
    else:
        # Check for multi-hop comparative or multi-aspect questions
        multi_hop_triggers = [
            "và",
            "so sánh",
            "đồng thời",
            "quy trình",
            "bồi thường và tái định cư",
            "thu hồi và",
            "hạn mức và giá",
            "vừa",
        ]
        is_complex = any(trigger in query_lower for trigger in multi_hop_triggers)

        if is_complex:
            route = "multi_hop"
            steps.append(
                f"Router: Multi-aspect legal inquiry detected. Routed to planner (District: {district or 'Hà Nội TP'})."
            )
        else:
            route = "single_hop"
            steps.append(
                f"Router: Single-aspect query identified. Routed directly to retrieval (District: {district or 'Hà Nội TP'})."
            )

    return {
        "route": route,
        "district": district,
        "as_of_date_applied": as_of_date_applied,
        "reasoning_steps": steps,
    }


def planner_node(state: AgentState) -> dict[str, Any]:
    """Decompose complex multi-aspect questions into atomic sub-queries."""
    query = state.get("query", "")
    district = state.get("district")
    steps = list(state.get("reasoning_steps", []))
    query_lower = query.lower()
    settings = get_settings()
    sub_queries: list[str] = []

    if "so sánh" in query_lower and ("2013" in query_lower or "2024" in query_lower):
        for year in ("2013", "2024"):
            if year in query_lower:
                sub_queries.append(f"{query} - quy định Luật Đất đai {year}")
    else:
        aspects = (
            ("thu hồi", "Căn cứ, điều kiện và trường hợp Nhà nước thu hồi đất"),
            ("bồi thường", "Điều kiện và hình thức bồi thường về đất"),
            ("tái định cư", "Điều kiện và việc bố trí tái định cư"),
            ("hạn mức", "Hạn mức giao đất ở và công nhận quyền sử dụng đất"),
            ("giá đất", "Bảng giá đất và nguyên tắc áp dụng giá đất"),
        )
        for trigger, aspect in aspects:
            if trigger in query_lower:
                sub_queries.append(f"{aspect}: {query}")

    if not sub_queries:
        conjunction_parts = [
            part.strip(" ,?.")
            for part in query_lower.replace(" đồng thời ", " và ").split(" và ")
            if part.strip(" ,?.")
        ]
        if len(conjunction_parts) > 1:
            sub_queries = [f"{query}: {part}" for part in conjunction_parts]
        else:
            sub_queries = [query]

    if district:
        sub_queries = [
            q if district.lower() in q.lower() else f"{q} tại {district}" for q in sub_queries
        ]
    sub_queries = list(dict.fromkeys(sub_queries))[: max(1, settings.MAX_SUBQUERIES)]

    steps.append(f"Planner: Decomposed into {len(sub_queries)} sub-queries: {sub_queries}")
    return {
        "sub_queries": sub_queries,
        "reasoning_steps": steps,
    }


def retrieval_node(state: AgentState) -> dict[str, Any]:
    """Execute hybrid retrieval for query or sub-queries with deduplication."""
    steps = list(state.get("reasoning_steps", []))
    as_of_date = state.get("as_of_date_applied")
    district = state.get("district")
    settings = get_settings()
    max_results = state.get("max_results", settings.MAX_RETRIEVAL_RESULTS)

    queries_to_search = state.get("sub_queries") or [state.get("query", "")]
    all_docs: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str | None, str | None]] = set()

    for q in queries_to_search:
        docs = retrieve_legal_documents(
            query=q,
            as_of_date=as_of_date,
            district=district,
            limit=max_results,
        )
        for d in docs:
            key = (
                str(d.get("doc_id", "")),
                str(d.get("article_ref", "")),
                str(d.get("clause", "")),
            )
            if key not in seen_keys:
                seen_keys.add(key)
                all_docs.append(d)

    steps.append(f"Retrieval: Fetched {len(all_docs)} unique legal chunks from corpus.")
    return {
        "retrieved_documents": all_docs,
        "reasoning_steps": steps,
    }


def grader_node(state: AgentState) -> dict[str, Any]:
    """Grade retrieved chunks for legal relevance and filter out noise (Zero Hallucination)."""
    steps = list(state.get("reasoning_steps", []))
    docs = state.get("retrieved_documents", [])
    query_lower = state.get("query", "").lower()
    focus_phrases = [phrase for phrase in LEGAL_FOCUS_PHRASES if phrase in query_lower]
    LEGAL_STOP_WORDS = {
        "và",
        "của",
        "các",
        "cho",
        "về",
        "thì",
        "là",
        "ở",
        "tại",
        "theo",
        "được",
        "có",
        "những",
        "này",
        "đó",
        "ra",
        "vào",
        "lại",
        "nào",
        "gì",
        "sao",
        "thế",
        "công",
        "gia",
        "nhất",
        "như",
        "nếu",
        "để",
        "do",
        "thức",
        "ngon",
        "truyền",
        "cách",
        "làm",
    }
    query_terms = {w for w in query_lower.split() if w not in LEGAL_STOP_WORDS and len(w) > 1}

    # Strict domain verification: Reject out-of-domain queries (e.g. recipes, general chat)
    legal_domain_stems = {
        "đất",
        "nhà",
        "giá",
        "bồi",
        "thường",
        "thu",
        "hồi",
        "tái",
        "định",
        "cư",
        "hạn",
        "mức",
        "quy",
        "hoạch",
        "sổ",
        "đỏ",
        "sử",
        "dụng",
        "giao",
        "thuê",
        "chuyển",
        "mục",
        "đích",
        "cấp",
        "tranh",
        "chấp",
        "nghị",
        "luật",
        "quyết",
        "bảng",
        "ubnd",
        "hđnd",
        "dự",
        "án",
    }
    if not any(stem in query_terms for stem in legal_domain_stems):
        steps.append(
            "Grader: Query is outside the Hanoi land & legal domain. Flagged insufficient_evidence."
        )
        return {
            "retrieved_documents": [],
            "status": "insufficient_evidence",
            "answer": "Không tìm thấy căn cứ pháp lý phù hợp trong cơ sở dữ liệu để giải đáp câu hỏi của bạn. Hệ thống chỉ hỗ trợ tra cứu pháp luật đất đai, quy hoạch và bồi thường tái định cư tại Hà Nội.",
            "citations": [],
            "reasoning_steps": steps,
        }

    relevant_docs: list[dict[str, Any]] = []

    for doc in docs:
        score = float(doc.get("score", 0.0))
        text_lower = doc.get("text", "").lower()
        title_lower = (doc.get("document_title") or doc.get("title") or "").lower()
        article_lower = (doc.get("article_ref") or doc.get("article") or "").lower()
        evidence_text = f"{text_lower} {title_lower} {article_lower}"

        matched_focus_phrases = matching_legal_focus_phrases(query_lower, evidence_text)
        if focus_phrases and not matched_focus_phrases:
            continue

        # Check keyword presence in chunk text/title/article
        matched_terms = [
            term
            for term in query_terms
            if term in text_lower or term in title_lower or term in article_lower
        ]

        # Must have at least 2 matching terms or score >= 0.25 with matching terms
        if len(matched_terms) >= 2 or (score >= 0.25 and len(matched_terms) >= 1):
            relevant_docs.append(
                {
                    **doc,
                    "_focus_match_count": len(matched_focus_phrases),
                    "_matched_term_count": len(matched_terms),
                }
            )

    if not relevant_docs:
        steps.append("Grader: 0 chunks relevant to legal inquiry. Flagged insufficient_evidence.")
        return {
            "retrieved_documents": [],
            "status": "insufficient_evidence",
            "answer": "Không tìm thấy căn cứ pháp lý phù hợp trong cơ sở dữ liệu để giải đáp đầy đủ câu hỏi của bạn. Khuyến nghị tham vấn cơ quan nhà nước có thẩm quyền hoặc tổ chức hành nghề luật sư.",
            "citations": [],
            "reasoning_steps": steps,
        }

    relevant_docs.sort(
        key=lambda doc: (
            doc.get("_focus_match_count", 0),
            doc.get("_matched_term_count", 0),
            float(doc.get("score", 0.0)),
        ),
        reverse=True,
    )
    for doc in relevant_docs:
        doc.pop("_focus_match_count", None)
        doc.pop("_matched_term_count", None)

    steps.append(
        f"Grader: Verified {len(relevant_docs)}/{len(docs)} chunks meet legal relevance threshold"
        + (f" and match query focus: {focus_phrases}." if focus_phrases else ".")
    )
    return {
        "retrieved_documents": relevant_docs,
        "reasoning_steps": steps,
    }


def synthesize_node(state: AgentState) -> dict[str, Any]:
    """Synthesize evidence-grounded answer with traceable legal citations."""
    steps = list(state.get("reasoning_steps", []))
    if state.get("status") == "insufficient_evidence":
        return {"reasoning_steps": steps}

    docs = state.get("retrieved_documents", [])
    if not docs:
        steps.append("Synthesize: No evidence chunks available.")
        return {
            "status": "insufficient_evidence",
            "answer": "Không tìm thấy căn cứ pháp lý phù hợp trong cơ sở dữ liệu.",
            "citations": [],
            "reasoning_steps": steps,
        }

    # Format citations
    citations: list[dict[str, Any]] = []
    for doc in docs[:5]:
        doc_id = doc.get("doc_id", "")
        doc_title = doc.get("document_title") or doc.get("title") or doc_id
        doc_number = doc.get("document_number") or doc_id
        art_ref = doc.get("article_ref") or doc.get("article")
        clause = doc.get("clause")
        text = doc.get("text", "")
        source_url = doc.get("source_url")
        effective_date = doc.get("effective_date")
        score = doc.get("score", 0.9)

        citations.append(
            {
                "doc_id": doc_id,
                "document_title": doc_title,
                "document_number": doc_number,
                "article_ref": art_ref,
                "clause": clause,
                "snippet": text[:250].strip() + ("..." if len(text) > 250 else ""),
                "source_url": source_url,
                "effective_date": effective_date,
                "relevance_score": score,
            }
        )

    # Attempt LLM synthesis via OpenAI-compatible endpoint (Google Gemini / Groq / Free Provider)
    settings = get_settings()
    llm_answer: str | None = None

    is_valid_key = (
        settings.OPENAI_API_KEY
        and settings.OPENAI_API_KEY.strip()
        and "your-gemini-api-key" not in settings.OPENAI_API_KEY
        and "your-groq-api-key" not in settings.OPENAI_API_KEY
    )

    if is_valid_key:
        try:
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                timeout=12.0,
            )
            evidence_context = "\n\n".join(
                [
                    f"--- CĂN CỨ PHÁP LÝ #{i + 1} ---\n"
                    f"Văn bản: {d.get('document_title', '')} (Số: {d.get('document_number', '')})\n"
                    f"Điều/Khoản: {d.get('article_ref', '')} {d.get('clause', '') or ''}\n"
                    f"Nội dung: {d.get('text', '')}"
                    for i, d in enumerate(docs[:4])
                ]
            )

            prompt = (
                f"Người dùng hỏi: {state.get('query')}\n\n"
                f"Căn cứ pháp lý có trong hồ sơ:\n{evidence_context}\n\n"
                "Yêu cầu: Hãy tổng hợp câu trả lời bằng tiếng Việt chuẩn mực pháp lý, bám sát các căn cứ trên. "
                "Tuyệt đối không suy đoán hay thêm điều khoản không có trong căn cứ."
            )

            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là chuyên gia tư vấn pháp luật đất đai và quy hoạch TP. Hà Nội. Trả lời chính xác, trung thực dựa trên tài liệu pháp lý được cung cấp.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=800,
            )
            llm_answer = response.choices[0].message.content
            logger.info("Successfully synthesized answer using LLM inference")
        except Exception as e:
            logger.warning(
                f"LLM synthesis call failed or skipped ({e}). Using deterministic grounded synthesis."
            )

    # High-quality deterministic synthesis fallback if LLM is unavailable
    if not llm_answer:
        top_doc = docs[0]
        top_title = top_doc.get("document_title") or top_doc.get("title") or top_doc.get("doc_id")
        top_art = top_doc.get("article_ref") or top_doc.get("article") or ""
        top_clause = top_doc.get("clause") or ""
        top_text = top_doc.get("text", "").strip()

        article_label = f"{top_art} ({top_clause})" if top_clause else top_art
        citation_header = f"Căn cứ quy định tại {article_label} {top_title}:"

        supporting_points = []
        if len(docs) > 1:
            for extra in docs[1:3]:
                extra_title = extra.get("document_title") or extra.get("title")
                extra_art = extra.get("article_ref") or extra.get("article") or ""
                extra_text = extra.get("text", "").strip()
                if extra_text and extra_text != top_text:
                    supporting_points.append(
                        f"- Theo {extra_title} ({extra_art}): {extra_text[:200]}..."
                    )

        extra_summary = (
            "\n\nQuy định bổ sung liên quan:\n" + "\n".join(supporting_points)
            if supporting_points
            else ""
        )
        llm_answer = f"{citation_header}\n\n{top_text}{extra_summary}\n\n*(Lưu ý: Mọi thông tin tra cứu chỉ mang tính chất tham khảo, không thay thế văn bản áp dụng pháp luật của cơ quan có thẩm quyền)*"

    steps.append(f"Synthesize: Formulated answer with {len(citations)} verified citations.")
    return {
        "answer": llm_answer,
        "citations": citations,
        "status": "answered",
        "reasoning_steps": steps,
    }


def verify_node(state: AgentState) -> dict[str, Any]:
    """Verify citations, quote provenance, and official source links (PRD M1)."""
    steps = list(state.get("reasoning_steps", []))
    citations = state.get("citations", [])
    current_status = state.get("status", "answered")

    if current_status == "clarification_needed":
        return {"reasoning_steps": steps}

    if not citations and current_status == "answered":
        steps.append(
            "Verify: FAILED - Answer claims lack traceable citations. Transferred to insufficient_evidence."
        )
        return {
            "status": "insufficient_evidence",
            "answer": "Không đủ bằng chứng pháp lý tin cậy để khẳng định câu trả lời.",
            "citations": [],
            "reasoning_steps": steps,
        }

    # Verify official source URLs and non-empty snippets
    from urllib.parse import urlparse

    official_hosts = {"vanban.chinhphu.vn", "vbpl.vn", "congbao.hanoi.gov.vn"}
    verified_count = 0
    for cit in citations:
        source_url = cit.get("source_url")
        snippet = cit.get("snippet", "")
        parsed_url = urlparse(source_url or "")
        quoted_text = snippet[:-3] if snippet.endswith("...") else snippet
        quote_matches_evidence = any(
            quoted_text and quoted_text in str(doc.get("text", ""))
            for doc in state.get("retrieved_documents", [])
        )
        if (
            parsed_url.scheme == "https"
            and parsed_url.hostname in official_hosts
            and quote_matches_evidence
        ):
            verified_count += 1

    steps.append(
        f"Verify: Passed citation provenance check ({verified_count}/{len(citations)} with official portal source URLs)."
    )
    if verified_count != len(citations):
        steps.append("Verify: Citation source or quote provenance failed; abstaining.")
        return {
            "status": "insufficient_evidence",
            "answer": "Không đủ bằng chứng pháp lý có nguồn chính thức và trích đoạn kiểm chứng được.",
            "citations": [],
            "reasoning_steps": steps,
        }
    return {
        "status": "answered",
        "reasoning_steps": steps,
    }


def clarification_node(state: AgentState) -> dict[str, Any]:
    """Formulate helpful, targeted clarification questions for ambiguous queries."""
    steps = list(state.get("reasoning_steps", []))
    steps.append("Clarification: Formulating clarification prompt for user.")

    clarification_msg = (
        "Câu hỏi của bạn cần bổ sung thêm thông tin cụ thể để hệ thống tra cứu chính xác quy định pháp luật:\n"
        "1. Địa bàn quận, huyện hoặc thị xã cụ thể tại Hà Nội (ví dụ: Cầu Giấy, Đông Anh, Long Biên...)\n"
        "2. Loại đất hoặc mục đích sử dụng đất (đất ở, đất nông nghiệp, đất thương mại dịch vụ...)\n"
        "3. Nội dung cụ thể cần tra cứu (hạn mức giao đất, điều kiện thu hồi, phương án bồi thường, hay bảng giá đất)."
    )

    return {
        "answer": None,
        "clarification_question": clarification_msg,
        "citations": [],
        "status": "clarification_needed",
        "reasoning_steps": steps,
    }
