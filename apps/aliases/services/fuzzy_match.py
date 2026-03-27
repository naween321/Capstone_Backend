"""Multi-tier alias resolution with fuzzy matching via PostgreSQL pg_trgm.

Lookup tiers (first match wins):
  1. Exact match on global alias table
  2. Fuzzy match on global alias table (trigram similarity)
  3. Store-level category fallback

The user-alias tier (per-install corrections) lives exclusively in local
SQLite on-device and is applied by the Flutter client before calling this
service, so it is intentionally absent here.
"""

from django.contrib.postgres.search import TrigramSimilarity

from apps.aliases.models import GlobalProductAlias, StoreAlias


def _normalize(text):
    return text.strip().upper() if text else ''


def lookup_alias(receipt_text, *, vendor_name=None,
                 similarity_threshold=0.3, max_results=5):
    """Resolve a single receipt line-item string to a display name and category.

    Returns a dict with keys: match_type, decoded_name, category,
    similarity, alternatives.
    """
    normalized = _normalize(receipt_text)
    if not normalized:
        return _empty_result()

    # ── 1. Exact match: global alias ────────────────────────────────
    global_exact = (
        GlobalProductAlias.objects
        .filter(alias_text_upper=normalized)
        .values('canonical_name', 'category')
        .first()
    )
    if global_exact:
        return {
            'match_type': 'exact_global',
            'decoded_name': global_exact['canonical_name'],
            'category': global_exact['category'],
            'similarity': 1.0,
            'alternatives': [],
        }

    # ── 2. Fuzzy match: global alias (trigram) ──────────────────────
    fuzzy_qs = (
        GlobalProductAlias.objects
        .annotate(similarity=TrigramSimilarity('alias_text_upper', normalized))
        .filter(similarity__gte=similarity_threshold)
        .order_by('-similarity')
        .values('canonical_name', 'category', 'similarity')
        [:max_results]
    )
    fuzzy_hits = list(fuzzy_qs)

    if fuzzy_hits:
        best = fuzzy_hits[0]
        return {
            'match_type': 'fuzzy_global',
            'decoded_name': best['canonical_name'],
            'category': best['category'],
            'similarity': round(best['similarity'], 4),
            'alternatives': [
                {
                    'decodedName': h['canonical_name'],
                    'category': h['category'],
                    'similarity': round(h['similarity'], 4),
                }
                for h in fuzzy_hits[1:]
            ],
        }

    # ── 3. Store alias fallback ─────────────────────────────────────
    if vendor_name:
        vendor_upper = _normalize(vendor_name)
        try:
            sa = StoreAlias.objects.get(vendor_name_upper=vendor_upper)
            return {
                'match_type': 'store',
                'decoded_name': None,
                'category': sa.category,
                'similarity': None,
                'alternatives': [],
            }
        except StoreAlias.DoesNotExist:
            pass

    return _empty_result()


def _empty_result():
    return {
        'match_type': None,
        'decoded_name': None,
        'category': None,
        'similarity': None,
        'alternatives': [],
    }


def lookup_aliases_batch(line_items, *, vendor_name=None,
                         similarity_threshold=0.3, max_results=5):
    """Resolve a list of line-item dicts, each having a 'receiptAcronym' key.

    Returns a list of result dicts in the same order as the input.
    """
    results = []
    for item in line_items:
        receipt_text = item.get('receiptAcronym', '')
        result = lookup_alias(
            receipt_text,
            vendor_name=vendor_name,
            similarity_threshold=similarity_threshold,
            max_results=max_results,
        )
        result['receiptAcronym'] = receipt_text
        results.append(result)
    return results
