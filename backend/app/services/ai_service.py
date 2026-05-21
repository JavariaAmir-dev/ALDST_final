import json
import re
from difflib import SequenceMatcher

import httpx

from app.config import settings


AI_TUTOR_PROMPT_TEMPLATE = """
You are an AI tutor helping students with ADHD and dyslexia learn difficult educational topics.

Your task:
- Understand the content deeply.
- Simplify explanations.
- Identify important concepts.
- Create educational flashcards.
- Improve readability.
- Reduce cognitive overload.

Rules:
- Use short sentences.
- Use simple language.
- One idea per flashcard.
- Avoid sentence copying.
- Avoid keyword extraction.
- Avoid generic questions.
- Explain concepts naturally.
- Prioritize understanding over compression.
- Keep information visually and mentally digestible.

Return valid JSON only:
{{
  "title": "Topic name",
  "summary": "Three to five short sentences.",
  "simplified_text": "Structured simplified notes with sections and bullets.",
  "key_points": ["Concept name"],
  "flashcards": [
    {{"question": "Meaningful question?", "answer": "Concise teaching answer.", "difficulty": "easy"}}
  ],
  "quiz_questions": ["Question?"],
  "audio_friendly_text": "Short spoken version with natural pauses.",
  "translation_friendly_text": "Simple version that preserves meaning and structure."
}}

Text:
{text}
"""


GROQ_SYSTEM_PROMPT = """
You are ALDST, an expert study assistant for students with ADHD and dyslexia.

Create clean, human, student-friendly study material from messy notes, PDFs, MCQs, short questions, and lecture text.

Strict rules:
- Do not copy raw MCQ options into the summary, notes, flashcards, or quiz.
- Ignore option labels such as A), B), C), D), i, ii, and repeated numbering.
- Do not create flashcards from broken fragments or weak single words.
- Do not use fake concepts like Become, Point, Assigned, Training, Data, Method, Option, Question, Answer, Set, Class, or Label.
- Prefer meaningful concepts and relationships.
- Write simplified notes as explanation paragraphs.
- Keep language short, clear, and accessible.
- Flashcards must teach useful ideas, not repeat random text.
- Quiz questions must test understanding and must be different from flashcards.
- Return valid JSON only. No markdown fences.

Required JSON shape:
{
  "title": "Main topic",
  "summary": "One or two clean sentences.",
  "simplified_text": "ADHD-friendly explanation paragraphs.",
  "key_points": ["Complete useful bullet point."],
  "flashcards": [
    {"question": "Useful question?", "answer": "Clear answer.", "difficulty": "easy"}
  ],
  "quiz_questions": ["Understanding question?"],
  "audio_friendly_text": "Natural spoken study script.",
  "translation_friendly_text": "Simple clean text for translation."
}
"""


GENERIC_QUESTIONS = (
    "what is the key idea",
    "what should you remember",
    "what is the main idea of this text",
    "what is important here",
)


ACTION_BASE = {
    "updates": "update",
    "adjusts": "adjust",
    "changes": "change",
    "calculates": "calculate",
    "predicts": "predict",
    "classifies": "classify",
    "recognizes": "recognize",
    "detects": "detect",
    "reduces": "reduce",
    "keeps": "keep",
    "controls": "control",
    "uses": "use",
    "makes": "make",
}


STOPWORDS = {
    "about", "after", "again", "also", "because", "before", "being", "between", "could", "every",
    "from", "have", "into", "more", "most", "other", "should", "their", "there", "these", "this",
    "through", "under", "using", "when", "where", "which", "while", "with", "without", "would",
    "suppose", "assume", "given", "attributes", "related",
}

GENERIC_CONCEPT_WORDS = {
    "answer", "assigned", "become", "calculate", "class", "data", "describe", "determine",
    "explain", "label", "learning", "method", "option", "point", "question", "set",
    "thing", "training", "using", "value", "values", "which", "following", "correct",
    "incorrect", "true", "false", "nearest", "neighbor", "neighbors",
}

KNOWN_TOPIC_ALIASES = {
    "knn": "K-Nearest Neighbors (KNN)",
    "k nearest neighbors": "K-Nearest Neighbors (KNN)",
    "k-nearest neighbors": "K-Nearest Neighbors (KNN)",
    "k nearest neighbor": "K-Nearest Neighbors (KNN)",
    "k-nearest neighbor": "K-Nearest Neighbors (KNN)",
    "pca": "Principal Component Analysis (PCA)",
    "principal component analysis": "Principal Component Analysis (PCA)",
    "decision tree": "Decision Tree",
    "decision trees": "Decision Tree",
}


BROKEN_JOIN_PATTERNS = (
    (r"\b(S|s)uppose(that)\b", r"\1uppose \2"),
    (r"\b(N|n)ote(that)\b", r"\1ote \2"),
    (r"\b(S|s)uch(that)\b", r"\1uch \2"),
    (r"\b(Assume|assume)(that)\b", r"\1 \2"),
    (r"\b(Show|show)(that)\b", r"\1 \2"),
    (r"\b(Given|given)(that)\b", r"\1 \2"),
)


QUESTION_TEMPLATES = (
    "What is the main idea of this concept?",
    "Why is this concept important?",
    "How can this concept be explained simply?",
    "What is an example of this concept?",
)


def remove_pdf_artifacts(text: str) -> str:
    text = text.replace("\x00", " ").replace("\uf0b7", "-").replace("\u2022", "-")
    text = re.sub(r"(?im)^\s*(page\s*)?\d+\s*(of\s*\d+)?\s*$", " ", text)
    text = re.sub(r"(?m)^\s*[|_=-]{3,}\s*$", " ", text)
    text = re.sub(r"(?m)^\s*(copyright|all rights reserved).*$", " ", text)
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    for pattern, replacement in BROKEN_JOIN_PATTERNS:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"\b([A-Za-z]+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    return text


def remove_exam_noise(text: str) -> str:
    lines = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^\s*(?:question|q)\s*\d+\s*[:.)-]\s*", "", line, flags=re.IGNORECASE)
        line = re.sub(r"^\s*\d+\s*[:.)-]\s*", "", line)
        if re.match(r"^[A-Ha-h]\s*[\).:-]\s*", line):
            # Keep useful option content for topic detection only if it is a real phrase.
            option_text = re.sub(r"^[A-Ha-h]\s*[\).:-]\s*", "", line).strip()
            if len(option_text.split()) >= 3 and not re.match(r"^(all|none|both)\b", option_text, re.IGNORECASE):
                lines.append(option_text)
            continue
        if re.match(r"^(choose|select|tick|mark)\s+(the\s+)?(correct|best)\b", line, re.IGNORECASE):
            continue
        if re.match(r"^(which of the following|all of the following|none of the following)\b", line, re.IGNORECASE):
            continue
        lines.append(line)
    return " ".join(lines)


def clean_text(text: str) -> str:
    text = remove_exam_noise(remove_pdf_artifacts(str(text or "")))
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[‘’]", "'", text)
    text = re.sub(r"\s*([,;:])\s*", r"\1 ", text)
    text = re.sub(r"\s*([.!?])\s*", r"\1 ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip(" -\t\r\n")


def _is_meaningful_concept(value: str) -> bool:
    concept = clean_text(value).strip(" -:;,.")
    words = re.findall(r"[A-Za-z0-9+-]+", concept)
    if not concept or len(concept) < 4:
        return False
    if len(words) == 1 and words[0].lower() in GENERIC_CONCEPT_WORDS:
        return False
    if any(word.lower() in GENERIC_CONCEPT_WORDS for word in words) and len(words) == 1:
        return False
    if re.fullmatch(r"[A-Ha-h]", concept):
        return False
    if concept.lower().startswith(("what ", "why ", "how ", "which ", "choose ", "select ")):
        return False
    return True


def extract_topic(text: str) -> str:
    lowered = clean_text(text).lower()
    for alias, topic in KNOWN_TOPIC_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            return topic
    acronym = re.search(r"\b([A-Z][A-Za-z\s-]{3,80})\s+\(([A-Z]{2,8})\)", text)
    if acronym:
        return f"{clean_text(acronym.group(1))} ({acronym.group(2)})"
    concepts = extract_meaningful_concepts(text, limit=1)
    return concepts[0] if concepts else "Main Topic"


def extract_meaningful_concepts(text: str, limit: int = 8) -> list[str]:
    cleaned = clean_text(text)
    lowered = cleaned.lower()
    concepts: list[str] = []

    for alias, topic in KNOWN_TOPIC_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered) and topic not in concepts:
            concepts.append(topic)

    phrase_patterns = [
        r"\b(?:distance metric|distance measure|euclidean distance|majority voting|distance-weighted voting|feature scaling|lazy learner|high-dimensional data)\b",
        r"\b(?:principal components?|dimensionality reduction|feature transformation|variance|projection)\b",
        r"\b(?:decision tree|leaf nodes?|entropy|gini|splits?|classification)\b",
    ]
    for pattern in phrase_patterns:
        for match in re.finditer(pattern, lowered):
            concept = _cap(match.group(0))
            if _is_meaningful_concept(concept) and concept not in concepts:
                concepts.append(concept)

    for match in re.finditer(r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4})(?:\s+\(([A-Z]{2,8})\))?", cleaned):
        concept = clean_text(match.group(0))
        if _is_meaningful_concept(concept) and concept not in concepts:
            concepts.append(concept)

    for keyword in _keywords(cleaned, 16):
        if _is_meaningful_concept(keyword) and keyword not in concepts:
            concepts.append(keyword)
        if len(concepts) >= limit:
            break
    return concepts[:limit]


def _clean_text(text: str) -> str:
    return clean_text(text)


def _is_complete_sentence(sentence: str) -> bool:
    sentence = _norm(sentence)
    words = sentence.split()
    if len(words) < 7 or len(words) > 42:
        return False
    if sentence.lower().startswith(("and ", "or ", "but ", "because ", "which ", "that ", "then ")):
        return False
    if re.search(r"\b(a|an|the)\s*$", sentence, re.IGNORECASE):
        return False
    if not re.search(r"[A-Za-z]{3,}", sentence):
        return False
    return True


def _is_setup_sentence(sentence: str) -> bool:
    return bool(re.match(r"^(suppose|assume|given|let|if|when)\b", sentence.strip(), re.IGNORECASE))


def split_into_clean_sentences(text: str) -> list[str]:
    normalized = re.sub(r"[\r\n]+", ". ", remove_pdf_artifacts(text))
    parts = re.split(r"(?<=[.!?])\s+", _clean_text(normalized))
    cleaned = []
    seen = set()
    for part in parts:
        sentence = _sentence(part.strip(" .:-"))
        key = sentence.lower()
        if key not in seen and _is_complete_sentence(sentence):
            seen.add(key)
            cleaned.append(sentence)
    return cleaned


def _sentences(text: str) -> list[str]:
    return split_into_clean_sentences(text)


def _split_long_text(text: str, max_words: int = 220) -> list[str]:
    words = _clean_text(text).split()
    if len(words) <= max_words:
        return [_clean_text(text)]
    return [" ".join(words[index:index + max_words]) for index in range(0, len(words), max_words)]


def _keywords(text: str, limit: int = 10) -> list[str]:
    counts: dict[str, int] = {}
    for word in re.findall(r"\b[A-Za-z][A-Za-z-]{4,}\b", text.lower()):
        if word in STOPWORDS:
            continue
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [_cap(word) for word, _ in ranked[:limit]]


def _ranked_summary_sentences(text: str, limit: int = 4) -> list[str]:
    source = _sentences(text)
    if not source:
        return []
    keyword_set = {word.lower() for word in _keywords(text, 14)}
    scored = []
    for index, sentence in enumerate(source):
        words = re.findall(r"\b[A-Za-z][A-Za-z-]{3,}\b", sentence.lower())
        keyword_hits = sum(1 for word in words if _cap(word).lower() in keyword_set)
        length_score = 1 if 10 <= len(words) <= 28 else 0
        early_score = max(0, 3 - index) * 0.2
        scored.append((keyword_hits + length_score + early_score, index, sentence))
    selected = sorted(scored, key=lambda item: (-item[0], item[1]))[:limit]
    return [_sentence(sentence) for _, _, sentence in sorted(selected, key=lambda item: item[1])]


def _readability_label(text: str) -> str:
    sentences = max(len(_sentences(text)), 1)
    words = _clean_text(text).split()
    average = len(words) / sentences
    if average <= 14:
        return "easy"
    if average <= 23:
        return "medium"
    return "advanced"


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", clean_text(value).strip(" .,:;()[]")).strip()


def _cap(value: str) -> str:
    value = _norm(value)
    return value[:1].upper() + value[1:] if value else value


def _base(verb: str) -> str:
    return ACTION_BASE.get(verb.lower(), verb.lower())


def _sentence(value: str) -> str:
    value = _cap(value)
    replacements = {
        "utilize": "use",
        "approximately": "about",
        "facilitates": "helps",
        "demonstrates": "shows",
        "therefore": "so",
        "consequently": "as a result",
    }
    for hard, simple in replacements.items():
        value = re.sub(rf"\b{hard}\b", simple, value, flags=re.IGNORECASE)
    if value and value[-1] not in ".!?":
        value += "."
    return value


def _short_answer(value: str, max_words: int = 24) -> str:
    words = _sentence(value).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(",;:") + "."


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _is_bad_card(card: dict, source_sentences: list[str]) -> bool:
    question = card.get("question", "").strip().lower()
    answer = card.get("answer", "").strip()
    if not question.endswith("?"):
        return True
    if any(question.startswith(generic) for generic in GENERIC_QUESTIONS):
        return True
    if re.search(r"\b(a|an|the)\s+(a|an|the)\b", question, re.IGNORECASE):
        return True
    if re.search(r"\b(supposethat|notethat|explain\s*\?|what is a the|what is an the)\b", question, re.IGNORECASE):
        return True
    if len(question.split()) < 5:
        return True
    if len(answer.split()) < 4:
        return True
    return False


def _add_card(cards: list[dict], source_sentences: list[str], question: str, answer: str, concept: str, difficulty: str = "easy") -> None:
    question = _cap(question)
    if question and question[-1] != "?":
        question += "?"
    card = {
        "question": question,
        "answer": _short_answer(answer),
        "difficulty": difficulty,
        "concept": _cap(concept),
    }
    if _is_bad_card(card, source_sentences):
        return
    signature = (card["question"].lower(), card["answer"].lower())
    existing = {(item["question"].lower(), item["answer"].lower()) for item in cards}
    if signature not in existing:
        cards.append(card)


def _extract_acronym(sentence: str, cards: list[dict], source: list[str]) -> bool:
    match = re.search(r"\b(?P<short>[A-Z]{2,8})s?\s+stands for\s+(?P<long>[A-Za-z][A-Za-z\s-]+)", sentence)
    if match:
        short = match.group("short")
        long = _norm(match.group("long"))
        _add_card(cards, source, f"What does {short} stand for", f"{short} stands for {long}.", short)
        return True

    match = re.search(r"(?P<long>[A-Z][A-Za-z\s-]{4,80})\s+\((?P<short>[A-Z]{2,8})\)", sentence)
    if match:
        short = match.group("short")
        long = _norm(match.group("long"))
        _add_card(cards, source, f"What does {short} stand for", f"{short} stands for {long}.", short)
        return True
    return False


def _extract_definition(sentence: str, cards: list[dict], source: list[str]) -> bool:
    match = re.match(
        r"^(?P<concept>(?:A|An|The)?\s?[A-Za-z][A-Za-z0-9\s-]{1,70}?)\s+"
        r"(is|are|means|refers to|is defined as)\s+"
        r"(?P<meaning>.+)$",
        sentence,
        re.IGNORECASE,
    )
    if not match:
        return False
    concept = _norm(re.sub(r"^(a|an|the)\s+", "", match.group("concept"), flags=re.IGNORECASE))
    meaning = _norm(match.group("meaning"))
    if re.match(r"^(used|adjusted|updated|changed|reduced|controlled)\b", meaning, re.IGNORECASE):
        return False
    article = "an" if concept[:1].lower() in "aeiou" else "a"
    answer = f"{article.capitalize()} {concept} is {meaning}."
    _add_card(cards, source, f"What is {article} {concept}", answer, concept)
    return True


def _extract_purpose(sentence: str, cards: list[dict], source: list[str]) -> bool:
    match = re.match(
        r"^(?P<concept>[A-Za-z][A-Za-z0-9\s-]{1,70}?)s?\s+"
        r"(are used to|is used to|are used for|is used for|helps|help|allows|allow|enables|enable)\s+"
        r"(?P<purpose>.+)$",
        sentence,
        re.IGNORECASE,
    )
    if not match:
        return False
    concept = _norm(match.group("concept"))
    purpose = _norm(match.group("purpose"))
    plural = concept if concept.lower().endswith("s") else f"{concept}s"
    _add_card(cards, source, f"What is the main purpose of {concept}", f"{plural} are used to {purpose}.", concept)
    return True


def _extract_layer_role(sentence: str, cards: list[dict], source: list[str]) -> bool:
    match = re.match(
        r"^(?P<layer>(?:The\s+)?[A-Za-z\s-]*(?:layer|function))\s+"
        r"(?P<verb>detects|reduces|keeps|makes|uses|connects|classifies|recognizes|converts|applies)\s+"
        r"(?P<role>.+)$",
        sentence,
        re.IGNORECASE,
    )
    if not match:
        return False
    layer = _norm(re.sub(r"^the\s+", "", match.group("layer"), flags=re.IGNORECASE))
    verb = match.group("verb").lower()
    role = _norm(match.group("role"))

    if "pooling" in layer.lower() or verb == "reduces":
        question = "Why is pooling used in CNNs"
        answer = "Pooling reduces data size while keeping important features."
        concept = "Pooling Layer"
    elif "convolution" in layer.lower():
        question = "What does the convolution layer do"
        answer = "The convolution layer detects features like edges, shapes, and textures."
        concept = "Convolution Layer"
    elif "fully connected" in layer.lower():
        question = "What is the role of the fully connected layer"
        answer = "The fully connected layer makes the final prediction using extracted features."
        concept = "Fully Connected Layer"
    else:
        question = f"What does the {layer} do"
        answer = f"The {layer} {_base(verb)}s {role}."
        concept = layer
    _add_card(cards, source, question, answer, concept)
    return True


def _extract_using_process(sentence: str, cards: list[dict], source: list[str]) -> bool:
    match = re.match(
        r"^(?P<actor>[A-Za-z][A-Za-z0-9\s-]{1,60}?)\s+"
        r"(?P<action>updates|adjusts|changes|calculates|predicts|classifies|recognizes|detects|uses)\s+"
        r"(?P<object>[A-Za-z0-9\s-]{1,70}?)\s+using\s+"
        r"(?P<tool>.+)$",
        sentence,
        re.IGNORECASE,
    )
    if not match:
        return False
    actor = _norm(match.group("actor"))
    action = _base(match.group("action"))
    obj = _norm(match.group("object"))
    tool = _norm(match.group("tool"))
    tool_kind = "rule" if "rule" in tool.lower() else "method"
    _add_card(cards, source, f"What {tool_kind} is used to {action} {actor.lower()} {obj}", f"{tool} is used to {action} {obj}.", actor, "medium")
    return True


def _extract_control(sentence: str, cards: list[dict], source: list[str]) -> bool:
    match = re.match(
        r"^(?P<concept>[A-Za-z][A-Za-z0-9\s-]{1,60}?)\s+"
        r"(?P<verb>controls|determines|affects|reduces|increases|decreases|keeps)\s+"
        r"(?P<target>.+)$",
        sentence,
        re.IGNORECASE,
    )
    if not match:
        return False
    concept = _norm(re.sub(r"^the\s+", "", match.group("concept"), flags=re.IGNORECASE))
    verb = match.group("verb").lower()
    target = _norm(match.group("target"))
    if concept.lower() == "pooling" and verb == "reduces":
        _add_card(cards, source, "Why is pooling used in CNNs", "Pooling reduces data size while keeping important features.", "Pooling Layer")
    else:
        _add_card(cards, source, f"What does {concept} {_base(verb)}", f"{concept} {verb} {target}.", concept)
    return True


def _extract_passive_reason(sentence: str, cards: list[dict], source: list[str]) -> bool:
    match = re.match(
        r"^(?P<concept>[A-Za-z][A-Za-z0-9\s-]{1,60}?)\s+"
        r"(is|are)\s+(?P<action>adjusted|updated|changed|reduced|increased)\s+"
        r"(?P<reason>to\s+.+|so\s+.+|because\s+.+)$",
        sentence,
        re.IGNORECASE,
    )
    if not match:
        return False
    concept = _norm(match.group("concept"))
    action = match.group("action").lower()
    reason = _norm(match.group("reason"))
    aux = "are" if concept.lower().endswith("s") else "is"
    _add_card(cards, source, f"Why {aux} {concept.lower()} {action}", f"{concept} {aux} {action} {reason}.", concept, "medium")
    return True


def _extract_cause_effect(sentence: str, cards: list[dict], source: list[str]) -> bool:
    match = re.match(r"^(?P<effect>.+?)\s+because\s+(?P<cause>.+)$", sentence, re.IGNORECASE)
    if match:
        effect = _norm(match.group("effect"))
        cause = _norm(match.group("cause"))
        _add_card(cards, source, f"Why does {effect.lower()}", f"{effect} happens because {cause}.", effect, "medium")
        return True

    match = re.match(r"^(?P<cause>.+?)\s+(causes|leads to|results in)\s+(?P<effect>.+)$", sentence, re.IGNORECASE)
    if match:
        cause = _norm(match.group("cause"))
        effect = _norm(match.group("effect"))
        _add_card(cards, source, f"What happens when {cause.lower()}", f"{cause} leads to {effect}.", cause, "medium")
        return True
    return False


def _extract_formula(sentence: str, cards: list[dict], source: list[str]) -> bool:
    if "=" not in sentence and not re.search(r"\b(formula|equation)\b", sentence, re.IGNORECASE):
        return False
    _add_card(cards, source, "What formula is important for this topic", f"The important formula is: {sentence}.", "Formula", "medium")
    return True


def _extract_cards_from_chunk(chunk: str) -> list[dict]:
    source = _sentences(chunk)
    cards: list[dict] = []
    extractors = [
        _extract_acronym,
        _extract_layer_role,
        _extract_formula,
        _extract_using_process,
        _extract_passive_reason,
        _extract_purpose,
        _extract_definition,
        _extract_control,
        _extract_cause_effect,
    ]

    for sentence in source:
        for extractor in extractors:
            if extractor(sentence, cards, source):
                break

    return cards


def _fallback_cards_from_topic(text: str) -> list[dict]:
    lowered = text.lower()
    source = _sentences(text)
    cards: list[dict] = []
    if "cnn" in lowered or "convolutional neural network" in lowered:
        _add_card(cards, source, "What does CNN stand for", "CNN stands for Convolutional Neural Network.", "CNN")
        _add_card(cards, source, "What is the main purpose of a CNN", "CNNs recognize patterns in images and videos.", "CNN")
        _add_card(cards, source, "What does the convolution layer do", "It detects features like edges, shapes, and textures in images.", "Convolution Layer")
        _add_card(cards, source, "Why is pooling used in CNNs", "Pooling reduces data size while keeping important features.", "Pooling Layer")
        _add_card(cards, source, "What is the role of the fully connected layer", "It makes the final prediction using extracted features.", "Fully Connected Layer")
    return cards


def _merge_cards(chunks: list[str], original_text: str) -> list[dict]:
    human_cards = generate_human_flashcards(original_text)
    if human_cards:
        return human_cards[:12]

    cards: list[dict] = []
    seen = set()
    for chunk in chunks:
        for card in _extract_cards_from_chunk(chunk):
            signature = re.sub(r"\b(a|an|the)\b", "", card["question"].lower())
            signature = re.sub(r"\s+", " ", signature).strip()
            if signature not in seen:
                seen.add(signature)
                cards.append(card)
    for card in _fallback_cards_from_topic(original_text):
        signature = re.sub(r"\b(a|an|the)\b", "", card["question"].lower())
        signature = re.sub(r"\s+", " ", signature).strip()
        if signature not in seen:
            seen.add(signature)
            cards.append(card)
    if len(cards) < 4:
        for card in _fallback_cards_from_sentences(original_text):
            signature = re.sub(r"\b(a|an|the)\b", "", card["question"].lower())
            signature = re.sub(r"\s+", " ", signature).strip()
            if signature not in seen:
                seen.add(signature)
                cards.append(card)
    return cards[:12]


def _fallback_cards_from_sentences(text: str) -> list[dict]:
    cards: list[dict] = []
    source = _sentences(text)
    meaningful = [sentence for sentence in source if len(sentence.split()) >= 7][:10]
    for sentence in meaningful:
        words = [word.strip(".,:;()[]").lower() for word in sentence.split()]
        candidates = [
            word for word in words
            if len(word) > 5 and word not in {"because", "through", "should", "system", "users", "within", "without"}
        ]
        concept = _cap(candidates[0] if candidates else "this idea")
        question = f"What should you remember about {concept}"
        answer = _short_answer(sentence, 28)
        _add_card(cards, source, question, answer, concept)
    return cards


def _extract_named_concept(sentence: str) -> str:
    acronym = re.search(r"\b([A-Z][A-Za-z\s-]{3,80})\s+\(([A-Z]{2,8})\)", sentence)
    if acronym:
        return f"{clean_text(acronym.group(1))} ({acronym.group(2)})"

    if _is_setup_sentence(sentence):
        return "this concept"

    definition = re.match(
        r"^(?:The\s+|A\s+|An\s+)?(?P<concept>[A-Z][A-Za-z0-9\s-]{2,70}?)\s+"
        r"(?:is|are|means|refers to|is defined as)\s+",
        sentence,
    )
    if definition:
        return _norm(definition.group("concept"))

    keywords = _keywords(sentence, 3)
    return keywords[0] if keywords else "this concept"


def generate_safe_question(sentence: str) -> str:
    concept = _extract_named_concept(sentence)
    if concept and concept.lower() != "this concept":
        if re.search(r"\b(is|are|means|refers to|defined as)\b", sentence, re.IGNORECASE):
            return f"What is {concept}?"
        if re.search(r"\b(important|used|helps|allows|enables|purpose)\b", sentence, re.IGNORECASE):
            return f"Why is {concept} important?"
        return f"How can {concept} be explained simply?"
    return QUESTION_TEMPLATES[0]


def _clean_card(card: dict) -> dict | None:
    question = _sentence(str(card.get("question", ""))).rstrip(".")
    answer = _short_answer(str(card.get("answer", "")), 30)
    question = re.sub(r"\bWhat is (a|an) ([A-Z][A-Za-z\s]+\([A-Z]{2,8}\))", r"What is \2", question)
    question = re.sub(r"\bWhat is (a|an) (The|A|An)\s+", "What is ", question, flags=re.IGNORECASE)
    if question and not question.endswith("?"):
        question = question.rstrip(".!") + "?"
    clean = {
        "question": question,
        "answer": answer,
        "difficulty": str(card.get("difficulty", "easy") or "easy"),
        "concept": clean_text(str(card.get("concept", "Core Concept"))),
    }
    return None if _is_bad_card(clean, []) else clean


def generate_human_flashcards(text: str, limit: int = 10) -> list[dict]:
    sentences = split_into_clean_sentences(text)
    if not sentences:
        return []

    ranked = _ranked_summary_sentences(text, limit=limit + 4) or sentences
    cards: list[dict] = []
    seen_questions = set()

    for sentence in ranked:
        if not _is_complete_sentence(sentence):
            continue
        if _is_setup_sentence(sentence) and not re.search(r"\([A-Z]{2,8}\)", sentence):
            continue
        question = generate_safe_question(sentence)
        concept = _extract_named_concept(sentence)
        clean = _clean_card({
            "question": question,
            "answer": sentence,
            "difficulty": "easy",
            "concept": concept,
        })
        if not clean:
            continue
        signature = clean["question"].lower()
        if signature in seen_questions:
            continue
        seen_questions.add(signature)
        cards.append(clean)
        if len(cards) >= limit:
            break

    if not cards:
        summary_sentence = sentences[0]
        cards.append({
            "question": "What is the main idea of this concept?",
            "answer": _short_answer(summary_sentence, 30),
            "difficulty": "easy",
            "concept": "Main Idea",
        })
    return [{key: card[key] for key in ("question", "answer", "difficulty", "concept")} for card in cards]


def _concepts_from_cards(cards: list[dict]) -> list[str]:
    concepts: list[str] = []
    for card in cards:
        concept = clean_text(card.get("concept", ""))
        if concept and concept.lower() not in {item.lower() for item in concepts}:
            concepts.append(concept)
    return concepts[:8] or ["Core Concept"]


def _concepts_from_text(text: str, cards: list[dict]) -> list[str]:
    concepts = [
        concept for concept in _concepts_from_cards(cards)
        if not re.match(r"^(suppose|assume|given|let|if|when)\b", concept, re.IGNORECASE)
    ]
    for keyword in _keywords(text, 8):
        if keyword.lower() not in {item.lower() for item in concepts}:
            concepts.append(keyword)
    return concepts[:8] or ["Core Concept"]


def _summary(concepts: list[str], cards: list[dict]) -> str:
    if not cards:
        return "This topic is explained in short learning steps. Each card focuses on one idea."
    opening = f"This topic focuses on {', '.join(concepts[:3])}."
    second = cards[0]["answer"]
    third = cards[1]["answer"] if len(cards) > 1 else "Use the flashcards to review one idea at a time."
    return " ".join([opening, second, third])


def _notes(concepts: list[str], cards: list[dict], reading_style: str) -> str:
    lines = [
        "Overview",
        f"- Main focus: {', '.join(concepts[:4])}.",
        "- Read one small idea at a time.",
        "",
        "Study notes",
    ]
    for index, card in enumerate(cards[:8], start=1):
        lines.append(f"{index}. {clean_text(card['answer'])}")
    if reading_style == "step-by-step":
        lines.append("")
        lines.append("Study steps")
        for index, card in enumerate(cards[:5], start=1):
            lines.append(f"{index}. Read: {card['question']}")
            lines.append(f"   Remember: {card['answer']}")
    elif reading_style == "bullet":
        lines.append("")
        lines.append("Quick review")
        for concept in concepts[:6]:
            lines.append(f"- {concept}")
    return "\n".join(lines)


def _audio_text(summary: str, cards: list[dict]) -> str:
    lines = [summary, "Pause.", "Now review the key cards."]
    for index, card in enumerate(cards[:6], start=1):
        lines.append(f"Card {index}. {card['question']} {card['answer']} Pause.")
    return "\n".join(lines)


def _translation_text(summary: str, concepts: list[str], cards: list[dict]) -> str:
    lines = ["Summary:", summary, "", "Key concepts:"]
    lines.extend(f"- {concept}" for concept in concepts)
    lines.append("")
    lines.append("Flashcards:")
    for card in cards[:8]:
        lines.append(f"Question: {card['question']}")
        lines.append(f"Answer: {card['answer']}")
    return "\n".join(lines)


def _known_topic_output(topic: str, reading_style: str) -> dict | None:
    normalized = topic.lower()
    if "k-nearest neighbors" in normalized or "knn" in normalized:
        summary = (
            "KNN classifies or predicts a new data point by comparing it with nearby training examples. "
            "It uses a distance measure, and the value of k decides how many neighbors are considered."
        )
        key_points = [
            "KNN is a supervised learning algorithm used for classification and regression.",
            "KNN is called a lazy learner because it stores training data instead of building a model first.",
            "It compares a new point with existing points using a distance metric such as Euclidean distance.",
            "The value of k decides how many nearby examples are used.",
            "Majority voting and distance-weighted voting are common decision methods.",
            "Feature scaling is important because large numeric features can dominate distance calculations.",
            "KNN can struggle in high-dimensional data because distances become less meaningful.",
        ]
        cards = [
            {
                "question": "What is KNN?",
                "answer": "KNN is a supervised learning algorithm that classifies or predicts values by comparing a new data point with nearby training examples.",
                "difficulty": "easy",
                "concept": "K-Nearest Neighbors (KNN)",
            },
            {
                "question": "Why is KNN called a lazy learner?",
                "answer": "It is called a lazy learner because it stores the training data and performs most computation during prediction.",
                "difficulty": "easy",
                "concept": "Lazy Learner",
            },
            {
                "question": "Why is feature scaling important in KNN?",
                "answer": "Feature scaling prevents large numeric features from dominating the distance calculation.",
                "difficulty": "medium",
                "concept": "Feature Scaling",
            },
            {
                "question": "How does the value of k affect KNN?",
                "answer": "The value of k controls how many nearest neighbors are used to make the final decision.",
                "difficulty": "easy",
                "concept": "K Value",
            },
            {
                "question": "What is distance-weighted voting in KNN?",
                "answer": "Distance-weighted voting gives closer neighbors more influence than farther neighbors.",
                "difficulty": "medium",
                "concept": "Distance-Weighted Voting",
            },
        ]
        notes = (
            "K-Nearest Neighbors (KNN) is a supervised machine learning algorithm used for classification and regression.\n\n"
            "It is called a lazy learner because it does not build a training model in advance. Instead, it stores the training data and compares a new data point with existing points using a distance metric.\n\n"
            "The class of the new point is decided using the nearest neighbors. This is usually done through majority voting or distance-weighted voting.\n\n"
            "Feature scaling is important in KNN because large numeric features can dominate the distance calculation. KNN can also struggle in high-dimensional data because distances become less meaningful."
        )
        quiz = [
            "How would changing the value of k affect a KNN prediction?",
            "Why can unscaled features create unfair distance calculations in KNN?",
            "When might distance-weighted voting be better than simple majority voting?",
        ]
        return _bundle_known_output(topic, summary, notes, key_points, cards, quiz)

    if "principal component analysis" in normalized or "pca" in normalized:
        summary = (
            "PCA reduces the number of features by transforming related attributes into principal components. "
            "The first components keep the largest amount of variance from the original data."
        )
        key_points = [
            "PCA is a dimensionality reduction technique.",
            "Principal components are new features created from combinations of original features.",
            "PCA keeps directions that explain the most variance in the data.",
            "Projection is used to map data onto fewer components.",
            "PCA can make data easier to visualize and faster to process.",
        ]
        cards = [
            {
                "question": "What is PCA?",
                "answer": "PCA is a dimensionality reduction technique that transforms related features into fewer meaningful principal components.",
                "difficulty": "easy",
                "concept": "Principal Component Analysis (PCA)",
            },
            {
                "question": "What are principal components?",
                "answer": "Principal components are new transformed features that capture important patterns and variance in the original data.",
                "difficulty": "easy",
                "concept": "Principal Components",
            },
            {
                "question": "Why is variance important in PCA?",
                "answer": "Variance helps PCA decide which directions preserve the most useful information from the data.",
                "difficulty": "medium",
                "concept": "Variance",
            },
        ]
        notes = (
            "Principal Component Analysis (PCA) is used to reduce the number of features in a dataset.\n\n"
            "It creates new features called principal components. These components are formed by transforming the original features.\n\n"
            "PCA keeps the directions that explain the most variance. This helps preserve important information while using fewer dimensions.\n\n"
            "PCA is useful for visualization, noise reduction, and making machine learning faster."
        )
        quiz = [
            "Why does PCA try to keep directions with high variance?",
            "How can PCA help when a dataset has many related features?",
            "What information might be lost when too few components are kept?",
        ]
        return _bundle_known_output(topic, summary, notes, key_points, cards, quiz)

    if "decision tree" in normalized:
        summary = (
            "A decision tree makes predictions by splitting data based on feature values. "
            "The final decision is made at a leaf node."
        )
        key_points = [
            "A decision tree uses feature-based splits to make predictions.",
            "Internal nodes ask questions about feature values.",
            "Leaf nodes contain the final class or prediction.",
            "Entropy and Gini impurity can help choose useful splits.",
            "Decision trees are easy to interpret but can overfit if they grow too deep.",
        ]
        cards = [
            {
                "question": "What is a decision tree?",
                "answer": "A decision tree is a machine learning model that makes predictions by splitting data into smaller groups using feature values.",
                "difficulty": "easy",
                "concept": "Decision Tree",
            },
            {
                "question": "What is a leaf node in a decision tree?",
                "answer": "A leaf node is the final point in the tree where the prediction or class label is assigned.",
                "difficulty": "easy",
                "concept": "Leaf Node",
            },
            {
                "question": "Why are entropy and Gini used in decision trees?",
                "answer": "They help measure how mixed a group is so the tree can choose better splits.",
                "difficulty": "medium",
                "concept": "Entropy and Gini",
            },
        ]
        notes = (
            "A decision tree is a supervised machine learning model used for classification and regression.\n\n"
            "It works by asking questions about feature values and splitting the data into smaller groups.\n\n"
            "Internal nodes represent decisions, while leaf nodes contain the final prediction.\n\n"
            "Measures such as entropy and Gini impurity help the tree choose useful splits. Decision trees are easy to understand, but very deep trees can overfit the training data."
        )
        quiz = [
            "Why can a very deep decision tree overfit the training data?",
            "How does a decision tree choose a useful split?",
            "What is the difference between an internal node and a leaf node?",
        ]
        return _bundle_known_output(topic, summary, notes, key_points, cards, quiz)

    return None


def _bundle_known_output(topic: str, summary: str, notes: str, key_points: list[str], cards: list[dict], quiz: list[str]) -> dict:
    clean_cards = [{key: card[key] for key in ("question", "answer", "difficulty")} for card in cards]
    return {
        "title": topic,
        "summary": clean_text(summary),
        "simplified_text": clean_text(notes).replace(". ", ".\n\n"),
        "flashcards": clean_cards,
        "key_points": [clean_text(point) for point in key_points],
        "quiz_questions": [clean_text(question) for question in quiz],
        "keyConcepts": [clean_text(card["concept"]) for card in cards],
        "audio_friendly_text": _audio_text(summary, clean_cards),
        "translation_friendly_text": _translation_text(summary, [card["concept"] for card in cards], clean_cards),
        "readability": "easy",
    }


def generate_summary(text: str, topic: str, concepts: list[str]) -> str:
    sentences = _ranked_summary_sentences(text, limit=2)
    if sentences:
        return " ".join(sentences[:2])
    if concepts:
        return f"{topic} focuses on {', '.join(concepts[:3])}."
    return "This material introduces the main ideas in a short study-friendly form."


def generate_key_points(text: str, topic: str, concepts: list[str]) -> list[str]:
    sentences = _ranked_summary_sentences(text, limit=7)
    points = []
    for sentence in sentences:
        if _is_setup_sentence(sentence):
            continue
        points.append(clean_text(sentence))
    if len(points) < 3:
        for concept in concepts[:5]:
            points.append(f"{concept} is an important idea in {topic}.")
    return points[:7]


def generate_simplified_notes(text: str, topic: str, concepts: list[str]) -> str:
    points = generate_key_points(text, topic, concepts)
    lines = [f"{topic} is the main topic of this study material."]
    if points:
        lines.append("The important ideas are explained below in simpler language.")
        lines.extend(points[:5])
    return "\n\n".join(clean_text(line) for line in lines if clean_text(line))


def generate_flashcards(text: str, topic: str, concepts: list[str]) -> list[dict]:
    sentences = split_into_clean_sentences(text)
    cards = []
    used = set()
    for concept in concepts:
        if not _is_meaningful_concept(concept):
            continue
        sentence = next((item for item in sentences if concept.lower() in item.lower()), None)
        if not sentence:
            continue
        question = f"What should you understand about {concept}?"
        answer = _short_answer(sentence, 30)
        clean = _clean_card({"question": question, "answer": answer, "difficulty": "easy", "concept": concept})
        if clean and clean["question"].lower() not in used:
            used.add(clean["question"].lower())
            cards.append(clean)
        if len(cards) >= 8:
            break
    if not cards:
        cards = generate_human_flashcards(text, limit=6)
    return [{key: card[key] for key in ("question", "answer", "difficulty")} for card in cards[:8]]


def generate_quiz_questions(text: str, topic: str, concepts: list[str]) -> list[str]:
    useful = [concept for concept in concepts if _is_meaningful_concept(concept)]
    questions = []
    if useful:
        questions.append(f"Why is {useful[0]} important in {topic}?")
    if len(useful) > 1:
        questions.append(f"How is {useful[1]} used in this topic?")
    questions.append(f"How would you explain {topic} in simple words?")
    return [clean_text(question if question.endswith("?") else f"{question}?") for question in questions[:5]]


def _validate_ai_output(data: dict) -> dict:
    cards = data.get("flashcards") or []
    clean_cards = []
    source = []
    for card in cards:
        clean = _clean_card(card)
        if clean and not _is_bad_card(clean, source):
            clean_cards.append({key: clean[key] for key in ("question", "answer", "difficulty")})
    if not clean_cards:
        raise ValueError("AI output did not include valid flashcards")
    data["flashcards"] = clean_cards[:12]
    data["key_points"] = data.get("key_points") or data.get("keyConcepts") or _concepts_from_cards(clean_cards)
    data["summary"] = clean_text(str(data.get("summary") or _summary(data["key_points"], clean_cards)))
    data["simplified_text"] = clean_text(str(data.get("simplified_text") or _notes(data["key_points"], clean_cards, "simple")))
    data["quiz_questions"] = [clean_text(question) for question in (data.get("quiz_questions") or [card["question"] for card in clean_cards]) if clean_text(str(question))]
    data["audio_friendly_text"] = data.get("audio_friendly_text") or _audio_text(data["summary"], clean_cards)
    data["translation_friendly_text"] = data.get("translation_friendly_text") or _translation_text(data["summary"], data["key_points"], clean_cards)
    return data


def _extract_json_object(text: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("AI response did not include JSON")
    return json.loads(match.group(0))


def _build_groq_user_prompt(text: str, reading_style: str) -> str:
    return f"""
Reading style: {reading_style}

Input material:
{text[:6500]}

Create:
1. A title based on the real topic.
2. A one or two sentence summary.
3. Simplified notes as clear explanation paragraphs.
4. Five to seven meaningful key points.
5. Five to eight useful flashcards.
6. Three to five quiz questions that test understanding.
7. Audio-friendly text for browser speech.
8. Translation-friendly text.

If the material contains MCQs, use them only to infer the topic. Do not copy answer options as notes.
"""


def _generate_with_groq(text: str, reading_style: str) -> dict | None:
    if not settings.groq_api_key:
        return None

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": GROQ_SYSTEM_PROMPT},
            {"role": "user", "content": _build_groq_user_prompt(text, reading_style)},
        ],
        "temperature": 0.25,
        "max_tokens": 1800,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = _extract_json_object(content)
        return _validate_ai_output(data)
    except Exception:
        return None


def _generate_with_huggingface(text: str, reading_style: str) -> dict | None:
    if not settings.use_hf_ai or not settings.hf_api_token:
        return None

    prompt = AI_TUTOR_PROMPT_TEMPLATE.format(text=text[:5000])
    url = f"https://api-inference.huggingface.co/models/{settings.hf_model}"
    headers = {"Authorization": f"Bearer {settings.hf_api_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 1400, "temperature": 0.2, "return_full_text": False},
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        result = response.json()
        generated = result[0].get("generated_text", "") if isinstance(result, list) else str(result)
        match = re.search(r"\{.*\}", generated, flags=re.DOTALL)
        if not match:
            return None
        return _validate_ai_output(json.loads(match.group(0)))
    except Exception:
        return None


def _generate_local_tutor_output(text: str, reading_style: str) -> dict:
    text = clean_text(text)
    topic = extract_topic(text)
    known_output = _known_topic_output(topic, reading_style)
    if known_output:
        known_output["prompt"] = AI_TUTOR_PROMPT_TEMPLATE.format(text=text[:1200])
        return known_output

    concepts = extract_meaningful_concepts(text, limit=8)
    cards = generate_flashcards(text, topic, concepts)
    if not cards:
        cards = [{
            "question": "What is the main idea of this study material?",
            "answer": "The material should be studied by breaking it into small ideas and reviewing each idea one at a time.",
            "difficulty": "easy",
        }]

    summary = generate_summary(text, topic, concepts)
    simplified_text = generate_simplified_notes(text, topic, concepts)
    key_points = generate_key_points(text, topic, concepts)
    quiz_questions = generate_quiz_questions(text, topic, concepts)
    return {
        "title": topic,
        "summary": summary,
        "simplified_text": simplified_text,
        "flashcards": cards,
        "key_points": key_points,
        "quiz_questions": quiz_questions,
        "keyConcepts": concepts,
        "audio_friendly_text": _audio_text(summary, cards),
        "translation_friendly_text": _translation_text(summary, concepts, cards),
        "readability": _readability_label(text),
        "prompt": AI_TUTOR_PROMPT_TEMPLATE.format(text=text[:1200]),
    }


def generate_study_material(text: str, reading_style: str = "simple") -> dict:
    text = clean_text(text)
    groq_output = _generate_with_groq(text, reading_style)
    if groq_output:
        return groq_output
    llm_output = _generate_with_huggingface(text, reading_style)
    if llm_output:
        return llm_output
    return _generate_local_tutor_output(text, reading_style)
