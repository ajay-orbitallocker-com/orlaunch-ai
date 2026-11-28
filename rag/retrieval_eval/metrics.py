import math
import statistics


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Computes recall at rank k.

    Args:
        retrieved_ids: The retrieved document ids, in rank order.
        relevant_ids: The set of ground-truth-relevant document ids.
        k: The rank cutoff.

    Returns:
        The fraction of relevant_ids found in the top k retrieved_ids,
        or 0.0 if relevant_ids is empty.
    """
    if not relevant_ids:
        return 0.0
    hits = len(relevant_ids & set(retrieved_ids[:k]))
    return hits / len(relevant_ids)


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Computes precision at rank k.

    Args:
        retrieved_ids: The retrieved document ids, in rank order.
        relevant_ids: The set of ground-truth-relevant document ids.
        k: The rank cutoff.

    Returns:
        The fraction of the top k retrieved_ids that are relevant, or
        0.0 if no documents were retrieved. Divides by the actual number
        retrieved (capped at k), not k unconditionally.
    """
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = len(relevant_ids & set(top_k))
    return hits / min(k, len(retrieved_ids))


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Computes the reciprocal rank of the first relevant document.

    Args:
        retrieved_ids: The retrieved document ids, in rank order.
        relevant_ids: The set of ground-truth-relevant document ids.

    Returns:
        1 / rank of the first relevant document found, or 0.0 if none of
        retrieved_ids are relevant.
    """
    for i, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / i
    return 0.0


def mean_reciprocal_rank(retrieved_ids_per_query: list[list[str]], relevant_ids_per_query: list[set[str]]) -> float:
    """Computes the mean reciprocal rank across queries.

    Args:
        retrieved_ids_per_query: One retrieved id list per query, in
            rank order.
        relevant_ids_per_query: One relevant id set per query, aligned
            by position with retrieved_ids_per_query.

    Returns:
        The mean of reciprocal_rank() across all queries, or 0.0 if
        retrieved_ids_per_query is empty.
    """
    if not retrieved_ids_per_query:
        return 0.0
    scores = [
        reciprocal_rank(retrieved, relevant)
        for retrieved, relevant in zip(retrieved_ids_per_query, relevant_ids_per_query)
    ]
    return statistics.mean(scores)


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Computes binary-relevance NDCG at rank k.

    Args:
        retrieved_ids: The retrieved document ids, in rank order.
        relevant_ids: The set of ground-truth-relevant document ids.
        k: The rank cutoff.

    Returns:
        The normalized discounted cumulative gain over the top k
        retrieved_ids, using binary (not graded) relevance, or 0.0 if
        the ideal DCG is 0.
    """
    top_k = retrieved_ids[:k]

    dcg = sum(
        1.0 / math.log2(i + 1)
        for i, doc_id in enumerate(top_k, start=1)
        if doc_id in relevant_ids
    )

    ideal_hits = min(k, len(relevant_ids))
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))

    return dcg / idcg if idcg > 0 else 0.0


def average_precision(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Computes average precision over the full retrieved list.

    Args:
        retrieved_ids: The retrieved document ids, in rank order.
        relevant_ids: The set of ground-truth-relevant document ids.

    Returns:
        The mean of precision-at-rank over each relevant document's
        rank, divided by len(relevant_ids), or 0.0 if relevant_ids is
        empty.
    """
    if not relevant_ids:
        return 0.0

    hits = 0
    precision_sum = 0.0
    for i, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            hits += 1
            precision_sum += hits / i

    return precision_sum / len(relevant_ids)


def mean_average_precision(retrieved_ids_per_query: list[list[str]], relevant_ids_per_query: list[set[str]]) -> float:
    """Computes mean average precision across queries.

    Args:
        retrieved_ids_per_query: One retrieved id list per query, in
            rank order.
        relevant_ids_per_query: One relevant id set per query, aligned
            by position with retrieved_ids_per_query.

    Returns:
        The mean of average_precision() across all queries, or 0.0 if
        retrieved_ids_per_query is empty.
    """
    if not retrieved_ids_per_query:
        return 0.0
    scores = [
        average_precision(retrieved, relevant)
        for retrieved, relevant in zip(retrieved_ids_per_query, relevant_ids_per_query)
    ]
    return statistics.mean(scores)


def context_precision(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Computes RAGAS-style Context Precision.

    Args:
        retrieved_ids: The retrieved document ids, in rank order.
        relevant_ids: The set of ground-truth-relevant document ids.

    Returns:
        The mean of precision-at-rank over each relevant document's
        rank, divided by the number of relevant documents actually
        found (not len(relevant_ids) — this is what distinguishes it
        from average_precision), or 0.0 if none were found.
    """
    hits = 0
    precision_sum = 0.0
    for i, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            hits += 1
            precision_sum += hits / i

    return precision_sum / hits if hits > 0 else 0.0


def context_recall(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Computes recall over the full retrieved set.

    Args:
        retrieved_ids: The retrieved document ids.
        relevant_ids: The set of ground-truth-relevant document ids.

    Returns:
        recall_at_k() evaluated with k set to the full length of
        retrieved_ids.
    """
    return recall_at_k(retrieved_ids, relevant_ids, k=len(retrieved_ids))
