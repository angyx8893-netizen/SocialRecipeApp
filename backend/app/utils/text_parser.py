"""
Recipe-focused cleaning and parsing layer (V5).
- Split text into ingredients_section and steps_section by headers before parsing.
- Parse ingredients only from ingredients_section; steps only from steps_section.
- Never copy ingredient lines into steps; deduplicate. If no procedure section, detect steps by cooking verbs.
"""
from __future__ import annotations

import re
import logging
from typing import List, Tuple, Optional, Set

logger = logging.getLogger(__name__)

# --- Italian + English units for ingredient parsing (shopping list) ---
# g, kg, gr | ml, l | cucchiaio, cucchiai | cucchiaino, cucchiaini | cup, cups | tsp, tbsp | fetta, fette | noce, noci | spicchio, spicchi | pizzico
_KNOWN_UNITS = {
    "g", "kg", "gr", "grammi", "grammo", "ml", "l", "litri", "litro", "cl",
    "oz", "lb", "cup", "cups", "tbsp", "tsp", "tb", "ts",
    "cucchiaio", "cucchiai", "cucchiaino", "cucchiaini", "cucchiaiate", "cucchiaiata",
    "tazze", "tazza", "pizzico", "pizzichi", "spicchi", "spicchio",
    "fetta", "fette", "fogli", "foglio", "rametti", "rametto", "pezzi", "pezzo",
    "noce", "noci", "dose", "dosi", "bustine", "bustina", "etto", "etti",
}
# Ordered for regex: longer units first so "cucchiaini" matches before "cucchiaino"
_UNITS_SORTED = sorted(_KNOWN_UNITS, key=len, reverse=True)

# Social and promotional phrases to strip (recipe-focused cleaning)
_SOCIAL_PHRASES = re.compile(
    r"\b("
    r"follow\s+me|follow\s+us|follow\s+for\s+more|"
    r"save\s+this|save\s+for\s+later|save\s+this\s+post|"
    r"link\s+in\s+bio|link\s+in\s+description|"
    r"viral|fyp|for\s+you\s+page|for\s+you|"
    r"subscribe|subscribes|subscribed|"
    r"like\s+and\s+subscribe|like\s+comment\s+share|"
    r"comment\s+below|comment\s+down\s+below|"
    r"share\s+with\s+someone|share\s+this|"
    r"tap\s+to\s+see|swipe\s+left|swipe\s+right|"
    r"don't\s+forget\s+to\s+follow|don't\s+forget\s+to\s+like|"
    r"let\s+me\s+know\s+in\s+the\s+comments|"
    r"tag\s+someone|tag\s+a\s+friend|"
    r"credits\s+to|credit\s+to|recipe\s+by\s+@|made\s+by\s+@|"
    r"dm\s+for\s+recipe|repost|reposted|"
    r"try\s+this\s+and\s+thank\s+me\s+later|"
    r"drop\s+a\s+heart|double\s+tap"
    r")\b",
    re.I
)
_HASHTAG_AT = re.compile(r"#\w+|@\w+")
_EMOJI_BLOCK = re.compile(r"[\U0001F300-\U0001F9FF\U00002700-\U000027BF]{2,}")

_MAX_INGREDIENT_LENGTH = 100
_LIST_LIKE = re.compile(r"^[\s]*[\d]+[.)]\s+|^[\s]*[-*•·]\s+|^[\s]*\d+\s*[x×]\s+", re.I)

# Section headers (Italian + English). Header lines are never included in output.
# Ingredienti / Ingredients
_INGREDIENT_HEADERS = (
    "ingredienti", "ingredients", "ingredient", "ingredienci", "ingrédients",
    "what you need", "occorrente", "serve", "per la ricetta", "lista ingredienti",
)
# Procedimento / Preparazione / Instructions / Steps / Method
_STEP_HEADERS = (
    "procedimento", "preparazione", "instructions", "steps", "method",
    "instruction", "step", "directions", "procedura", "how to", "preparation",
    "methodology", "come fare", "direzioni",
)

# Cooking verbs for step inference when no explicit steps section exists
# Includes: cuoci, taglia, aggiungi, mescola, versa, frulla, rosola, scola, inforna, mix, cook, stir, add, bake, fry, boil, etc.
_COOKING_VERBS = re.compile(
    r"\b("
    r"cuoci|taglia|aggiungi|mescola|versa|frulla|rosola|scola|inforna|mix|"
    r"cook|stir|add|bake|fry|boil|combine|heat|pour|cut|chop|slice|dice|mince|"
    r"sauté|simmer|preheat|whisk|beat|fold|"
    r"place|put|transfer|remove|cover|uncover|season|salt|"
    r"combina|scaldare|trita|friggi|lessa|soffriggi|batti|incorpora|"
    r"metti|trasferisci|togli|copri|condisci|sala"
    r")\b",
    re.I
)
_IMPERATIVE_PATTERN = _COOKING_VERBS  # same set for step-like lines
_NUMBERED_STEP = re.compile(r"^\d+[.)]\s*.+")


def clean_recipe_text(text: str) -> str:
    """
    Recipe-focused text cleaning:
    - Remove hashtags and @mentions
    - Remove repeated emojis; remove social phrases
    - Collapse duplicated spaces and newlines
    """
    if not text or not text.strip():
        return ""
    out = text
    out = _HASHTAG_AT.sub(" ", out)
    out = _SOCIAL_PHRASES.sub(" ", out)
    out = _EMOJI_BLOCK.sub(" ", out)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n\s*\n+", "\n", out)
    out = re.sub(r"\n+", "\n", out)
    return out.strip()


def clean_line_for_parsing(line: str) -> str:
    """Strip and remove inline hashtags/mentions from a single line."""
    s = line.strip()
    s = _HASHTAG_AT.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _normalize_line_for_dedup(line: str) -> str:
    """Normalize line for deduplication (lowercase, single spaces)."""
    return " ".join(clean_line_for_parsing(line).lower().split())


def _is_ingredient_header_line(line: str) -> bool:
    """True if line looks like an ingredient section header (whole line or line starts with)."""
    s = clean_line_for_parsing(line).lower()
    if not s:
        return False
    for h in _INGREDIENT_HEADERS:
        if s == h or s.startswith(h + " ") or s.startswith(h + ":") or s.startswith(h + "\n"):
            return True
    return False


def _is_step_header_line(line: str) -> bool:
    """True if line looks like a steps/procedure section header."""
    s = clean_line_for_parsing(line).lower()
    if not s:
        return False
    for h in _STEP_HEADERS:
        if s == h or s.startswith(h + " ") or s.startswith(h + ":") or s.startswith(h + "\n"):
            return True
    return False


def split_into_sections(text: str) -> dict:
    """
    Split cleaned text into ingredients_section and steps_section (and optional title).
    Returns dict: title, ingredients_section (str), steps_section (str).
    Sections are raw text blocks; header lines are not included in the section content.
    """
    out = {
        "title": "",
        "ingredients_section": "",
        "steps_section": "",
    }
    cleaned = clean_recipe_text(text)
    lines = cleaned.splitlines()
    if not lines:
        return out

    # Detect positions of first ingredient header and first step header
    first_ing_idx: Optional[int] = None
    first_step_idx: Optional[int] = None
    for i, raw_line in enumerate(lines):
        line = clean_line_for_parsing(raw_line)
        if not line:
            continue
        if _is_ingredient_header_line(line) and first_ing_idx is None:
            first_ing_idx = i
        if _is_step_header_line(line) and first_step_idx is None:
            first_step_idx = i

    # Build title: first non-empty line before any section (or first line)
    for raw_line in lines:
        line = clean_line_for_parsing(raw_line)
        if line and not _is_ingredient_header_line(line) and not _is_step_header_line(line):
            out["title"] = line
            break

    # Ingredients section: from line after first ingredient header until (excl) step header or end. No header lines included.
    if first_ing_idx is not None:
        end_ing = len(lines)
        if first_step_idx is not None and first_step_idx > first_ing_idx:
            end_ing = first_step_idx
        ing_lines = []
        for j in range(first_ing_idx + 1, end_ing):
            line = clean_line_for_parsing(lines[j])
            if line and not _is_ingredient_header_line(line) and not _is_step_header_line(line):
                ing_lines.append(line)
        out["ingredients_section"] = "\n".join(ing_lines)

    # Steps section: from line after first step header until (excl) ingredient header or end. No header lines included.
    if first_step_idx is not None:
        end_step = len(lines)
        if first_ing_idx is not None and first_ing_idx > first_step_idx:
            end_step = first_ing_idx
        step_lines = []
        for j in range(first_step_idx + 1, end_step):
            line = clean_line_for_parsing(lines[j])
            if line and not _is_ingredient_header_line(line) and not _is_step_header_line(line):
                step_lines.append(line)
        out["steps_section"] = "\n".join(step_lines)

    logger.info("[parser] detected_ingredients_section length=%d snippet=%s", len(out["ingredients_section"]), (out["ingredients_section"][:200] + "..." if len(out["ingredients_section"]) > 200 else out["ingredients_section"]))
    logger.info("[parser] detected_steps_section length=%d snippet=%s", len(out["steps_section"]), (out["steps_section"][:200] + "..." if len(out["steps_section"]) > 200 else out["steps_section"]))
    return out


def rank_text_sources(sources: List[Tuple[str, str]]) -> str:
    """Rank text sources by usefulness. Returns single merged or best text (cleaned)."""
    order = {"caption": 0, "metadata": 1, "transcript": 2, "ocr": 3, "body": 4}
    by_rank: List[Tuple[int, str]] = []
    for text, source_type in sources:
        if not (text and text.strip()):
            continue
        t = clean_recipe_text(text)
        if not t:
            continue
        rank = order.get(source_type, 5)
        by_rank.append((rank, t))
    by_rank.sort(key=lambda x: x[0])
    if not by_rank:
        return ""
    best_rank = by_rank[0][0]
    best_only = [t for r, t in by_rank if r == best_rank]
    return "\n".join(best_only)


def _has_quantity_or_unit(line: str) -> bool:
    """Prefer lines that contain a number (quantity) or known unit."""
    s = clean_line_for_parsing(line)
    if re.match(r"^[\d.,/\s]+", s):
        return True
    words = set(re.findall(r"[a-zA-ZÀ-ÿ]+", s.lower()))
    return bool(words & _KNOWN_UNITS)


def _is_list_like(line: str) -> bool:
    """Detect list-like patterns: "1. ", "- ", "• ", "2x "."""
    return _LIST_LIKE.match(line.strip()) is not None


def _looks_like_narration(line: str) -> bool:
    """Reject long lines that look like sentences/narration, not ingredients."""
    s = clean_line_for_parsing(line)
    if len(s) > _MAX_INGREDIENT_LENGTH:
        return True
    if re.search(r"[.!?]\s*$", s) and len(s) > 60:
        return True
    return False


def is_likely_ingredient_line(line: str) -> bool:
    """
    Ingredient candidate detection:
    - Prefer lines with quantities or measurement units
    - Accept list-like patterns
    - Reject long narration-like lines and social noise
    """
    s = clean_line_for_parsing(line)
    if len(s) < 2:
        return False
    if len(s) > _MAX_INGREDIENT_LENGTH:
        return False
    if _looks_like_narration(s):
        return False
    if _SOCIAL_PHRASES.search(s):
        return False
    if s.startswith("#") or s.startswith("@"):
        return False
    if _has_quantity_or_unit(s):
        return True
    if _is_list_like(line):
        return True
    words = set(re.findall(r"[a-zA-ZÀ-ÿ]+", s.lower()))
    if words & _KNOWN_UNITS:
        return True
    if re.match(r"^[a-zA-ZÀ-ÿ\s,]+$", s) and not re.search(r"[.!?]\s*$", s):
        if 1 <= len(words) <= 6:
            return True
    return False


def parse_ingredient_line(line: str) -> Tuple[str, str, str, str, float]:
    """
    Parse a single ingredient line into quantity, unit, name, original_text, and confidence [0..1].
    Preserves original_text for fallback display. Supports Italian "di" (e.g. "200 g di pasta").
    Examples:
      "200 g di pasta tipo calamarata" -> ("200", "g", "pasta tipo calamarata", original_text="200 g di pasta tipo calamarata", 0.95)
      "2 patate" -> ("2", "", "patate", original_text="2 patate", 0.85)
      "Sale" -> ("", "", "sale", original_text="Sale", 0.6)
    """
    s = clean_line_for_parsing(line)
    original_text = s
    if not s:
        return "", "", "", "", 0.0
    confidence = 0.5
    quantity, unit, name = "", "", s

    # Pattern 1: number + known unit (optional "di ") + name
    for u in _UNITS_SORTED:
        escaped = re.escape(u)
        m = re.match(r"^(\d+[\d./,\s]*)\s+" + escaped + r"\s+(?:di\s+)?(.+)$", s, re.I)
        if m:
            quantity = m.group(1).strip()
            unit = u
            name = m.group(2).strip()
            confidence = 0.92
            return quantity, unit, name, original_text, min(confidence, 1.0)

    # Pattern 2: number + unit (any) + name (generic)
    m = re.match(r"^(\d+[\d./,\s]*)\s+([a-zA-ZÀ-ÿ°]+)\s+(?:di\s+)?(.+)$", s)
    if m:
        quantity = m.group(1).strip()
        u2 = m.group(2).strip().lower()
        name = m.group(3).strip()
        if u2 in _KNOWN_UNITS:
            unit = u2
            confidence = 0.92
        else:
            unit = u2
            confidence = 0.72
        return quantity, unit, name, original_text, min(confidence, 1.0)

    # Pattern 3: number + name (no unit), e.g. "2 patate"
    m = re.match(r"^(\d+[\d./,\s]*)\s+(.+)$", s)
    if m:
        quantity = m.group(1).strip()
        name = m.group(2).strip()
        confidence = 0.85
        return quantity, "", name, original_text, min(confidence, 1.0)

    # Pattern 4: name only, e.g. "Sale", "Olio" -> preserve originalText; name normalized to lowercase
    if is_likely_ingredient_line(s):
        confidence = 0.6
        return "", "", s.strip().lower(), original_text, confidence
    return "", "", s, original_text, confidence


def filter_ingredients_by_confidence(
    lines: List[str],
    min_confidence: float = 0.55,
) -> List[Tuple[str, float]]:
    """Return (line, confidence) for lines that pass ingredient heuristics."""
    result = []
    for line in lines:
        s = clean_line_for_parsing(line)
        if not s:
            continue
        if not is_likely_ingredient_line(s):
            continue
        _, _, _, _, conf = parse_ingredient_line(s)
        if conf >= min_confidence:
            result.append((s, conf))
    return result


def _is_likely_step_line(line: str, exclude_ingredient_normalized: Optional[Set[str]] = None) -> bool:
    """
    Step candidate: numbered steps, or lines with cooking verbs.
    Reject ingredient-like lines and lines in exclude set (e.g. ingredient list).
    """
    s = clean_line_for_parsing(line)
    if len(s) < 8:
        return False
    if is_likely_ingredient_line(s):
        return False
    if exclude_ingredient_normalized:
        norm = _normalize_line_for_dedup(s)
        if norm in exclude_ingredient_normalized:
            return False
    if _NUMBERED_STEP.match(s):
        return True
    if _COOKING_VERBS.search(s):
        return True
    return False


def extract_ordered_steps(
    lines: List[str],
    exclude_ingredient_lines: Optional[List[str]] = None,
) -> List[str]:
    """
    From step-like lines, return ordered steps (strip leading numbers/bullets).
    - Do NOT copy ingredient lines into steps: exclude exact match and any step that is a short substring of an ingredient.
    - When uncertain, return fewer but cleaner steps (reject ingredient-like and duplicate lines).
    """
    exclude_set: Set[str] = set()
    if exclude_ingredient_lines:
        for ln in exclude_ingredient_lines:
            norm = _normalize_line_for_dedup(ln)
            if norm:
                exclude_set.add(norm)
    steps = []
    for line in lines:
        s = clean_line_for_parsing(line)
        if not s or len(s) < 5:
            continue
        norm = _normalize_line_for_dedup(s)
        if norm in exclude_set:
            continue
        m = re.match(r"^\d+[.)]\s*", s)
        if m:
            s = s[m.end():].strip()
        if not s or len(s) < 5:
            continue
        if is_likely_ingredient_line(s):
            continue
        if norm in exclude_set:
            continue
        # Reject short lines that are substring of an ingredient (avoids "pasta", "olio" as steps)
        if len(norm) <= 25 and any(norm in ing_norm for ing_norm in exclude_set):
            continue
        steps.append(s)
    return steps


def _steps_from_text_by_verbs(text: str, exclude_ingredient_lines: List[str]) -> List[str]:
    """
    When no procedure section exists: detect step lines by cooking verbs and numbered lines.
    Only from text; exclude any line that is in the ingredient set.
    """
    exclude_set = {_normalize_line_for_dedup(ln) for ln in exclude_ingredient_lines if ln}
    lines = [clean_line_for_parsing(ln) for ln in text.splitlines() if clean_line_for_parsing(ln)]
    step_lines = [ln for ln in lines if _is_likely_step_line(ln, exclude_set)]
    return extract_ordered_steps(step_lines, exclude_ingredient_lines=exclude_ingredient_lines)


def extract_recipe_sections(text: str) -> dict:
    """
    Split text into ingredients_section and steps_section, then parse each separately.
    - Ingredients: only from ingredients_section; heuristic filter.
    - Steps: only from steps_section; if steps_section is empty, detect steps by cooking verbs from rest of text.
    - Never put ingredient lines into steps; remove duplicates.
    Returns dict: title, ingredients, steps, ingredients_section, steps_section, raw_lines.
    """
    cleaned = clean_recipe_text(text)
    logger.info("[parser] cleaned_text length=%d snippet=%s", len(cleaned), (cleaned[:300] + "..." if len(cleaned) > 300 else cleaned))
    split = split_into_sections(cleaned)
    title = split.get("title") or ""
    ingredients_section = split.get("ingredients_section") or ""
    steps_section = split.get("steps_section") or ""

    # Parse ingredients only from ingredients_section; ignore section header lines
    ing_lines = [clean_line_for_parsing(ln) for ln in ingredients_section.splitlines() if clean_line_for_parsing(ln)]
    ing_lines = [ln for ln in ing_lines if not _is_ingredient_header_line(ln) and not _is_step_header_line(ln)]
    raw_ingredient_lines = [ln for ln in ing_lines if is_likely_ingredient_line(ln)]

    # Parse steps only from steps_section; exclude header lines and any line that matches an ingredient
    step_lines_raw = [clean_line_for_parsing(ln) for ln in steps_section.splitlines() if clean_line_for_parsing(ln)]
    step_lines_raw = [ln for ln in step_lines_raw if not _is_ingredient_header_line(ln) and not _is_step_header_line(ln)]
    steps = extract_ordered_steps(step_lines_raw, exclude_ingredient_lines=raw_ingredient_lines)

    # If no procedure section existed but we have step headers, steps_section might be empty; then use cooking-verb detection on full text (excluding ingredient block)
    if not steps and raw_ingredient_lines:
        # Fallback: find steps in the rest of the text (everything that is not in ingredients_section)
        rest_text = cleaned
        if ingredients_section:
            rest_text = rest_text.replace(ingredients_section, "\n", 1)
        steps = _steps_from_text_by_verbs(rest_text, raw_ingredient_lines)
    elif not steps and not steps_section and cleaned:
        steps = _steps_from_text_by_verbs(cleaned, raw_ingredient_lines)

    logger.info("[parser] parsed_ingredients count=%d list=%s", len(raw_ingredient_lines), raw_ingredient_lines[:12])
    logger.info("[parser] parsed_steps count=%d list=%s", len(steps), [s[:50] for s in steps[:8]])
    return {
        "title": title,
        "ingredients": raw_ingredient_lines,
        "steps": steps,
        "ingredients_section": ingredients_section,
        "steps_section": steps_section,
        "raw_lines": cleaned.splitlines(),
    }


def infer_tags(text: str) -> List[str]:
    """Infer tags from cleaned recipe text."""
    tags = []
    cleaned = clean_recipe_text(text).lower()
    if any(w in cleaned for w in ("vegetarian", "vegan", "vegetariano")):
        tags.append("vegetarian")
    if any(w in cleaned for w in ("spicy", "pepper", "chili", "picante", "peperoncino")):
        tags.append("spicy")
    if any(w in cleaned for w in ("oven", "bake", "forno", "in forno")):
        tags.append("oven")
    if any(w in cleaned for w in ("pan", "fry", "padella", "skillet", "friggere")):
        tags.append("pan")
    if any(w in cleaned for w in ("cold", "freddo", "salad", "insalata")):
        tags.append("cold")
    if any(w in cleaned for w in ("quick", "fast", "veloce", "5 min", "10 min", "rapido")):
        tags.append("quick")
    return tags


def recipe_cleaning_and_parsing(
    text: str,
    min_ingredient_confidence: float = 0.55,
) -> dict:
    """
    Single entry point: split into sections, then parse ingredients and steps separately.
    Returns dict: cleaned_text, ingredients_raw, ingredients_structured, steps, title,
    ingredients_section, steps_section.
    """
    cleaned = clean_recipe_text(text)
    sections = extract_recipe_sections(cleaned)
    title = sections.get("title") or ""
    raw_ingredient_lines = sections.get("ingredients") or []
    steps = sections.get("steps") or []

    filtered = filter_ingredients_by_confidence(raw_ingredient_lines, min_confidence=min_ingredient_confidence)
    ingredients_raw = [line for line, _ in filtered]
    ingredients_structured: List[dict] = []
    for line in ingredients_raw:
        q, u, n, orig, _ = parse_ingredient_line(line)
        ingredients_structured.append({"quantity": q or "", "unit": u or "", "name": n or line, "original_text": orig or line})

    return {
        "cleaned_text": cleaned,
        "title": title,
        "ingredients_raw": ingredients_raw,
        "ingredients_structured": ingredients_structured,
        "steps": steps,
        "ingredients_section": sections.get("ingredients_section", ""),
        "steps_section": sections.get("steps_section", ""),
    }
