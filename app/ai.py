from __future__ import annotations

import re
from collections import Counter
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

STOP_WORDS = {
    "och",
    "det",
    "att",
    "i",
    "en",
    "jag",
    "på",
    "är",
    "som",
    "för",
    "med",
    "till",
    "den",
    "han",
    "av",
    "inte",
    "ett",
    "har",
    "om",
    "vi",
    "kan",
    "från",
    "men",
    "så",
    "de",
}

_WORD_PATTERN = re.compile(r"[\wåäöÅÄÖ]+", re.UNICODE)


def split_into_sentences(text: str) -> List[str]:
    sentences: List[str] = []
    buffer = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        buffer.append(stripped)
    joined = " ".join(buffer)
    raw_sentences = re.split(r"(?<=[.!?])\s+", joined)
    for sentence in raw_sentences:
        clean = sentence.strip()
        if clean:
            sentences.append(clean)
    return sentences


def summarize_text(text: str, max_sentences: int = 3) -> str:
    sentences = split_into_sentences(text)
    if not sentences:
        return ""
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    word_frequencies = Counter()
    for sentence in sentences:
        words = [w.lower() for w in _WORD_PATTERN.findall(sentence)]
        for word in words:
            if word in STOP_WORDS:
                continue
            word_frequencies[word] += 1

    if not word_frequencies:
        return " ".join(sentences[:max_sentences])

    max_freq = max(word_frequencies.values())
    for word in list(word_frequencies):
        word_frequencies[word] /= max_freq

    scored_sentences = []
    for sentence in sentences:
        words = [w.lower() for w in _WORD_PATTERN.findall(sentence)]
        if not words:
            continue
        score = sum(word_frequencies.get(word, 0.0) for word in words)
        scored_sentences.append((sentence, score / len(words)))

    top_sentences = sorted(scored_sentences, key=lambda s: s[1], reverse=True)[:max_sentences]
    # Preserve original order
    ordered = sorted(top_sentences, key=lambda s: sentences.index(s[0]))
    return " ".join(sentence for sentence, _ in ordered)


def extract_questions(text: str, max_questions: int = 20) -> List[str]:
    candidates: List[str] = []
    sentences = split_into_sentences(text)
    for sentence in sentences:
        if sentence.endswith("?"):
            candidates.append(sentence.strip())
    if len(candidates) < max_questions:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.endswith("?") and stripped not in candidates:
                candidates.append(stripped)
    # Deduplicate while preserving order
    seen = set()
    unique_questions = []
    for question in candidates:
        if question not in seen:
            unique_questions.append(question)
            seen.add(question)
        if len(unique_questions) >= max_questions:
            break
    return unique_questions


def answer_question(question: str, context: str) -> tuple[str, str | None]:
    sentences = split_into_sentences(context)
    if not sentences:
        return "Det finns inget innehåll att svara på.", None

    corpus = sentences + [question]
    vectorizer = TfidfVectorizer(stop_words=list(STOP_WORDS))
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        return (
            "Texten var för kort för att analysera. Försök att lägga till mer innehåll i dokumentet.",
            None,
        )
    question_vector = tfidf_matrix[-1]
    sentence_vectors = tfidf_matrix[:-1]

    similarities = cosine_similarity(question_vector, sentence_vectors)[0]
    if similarities.size == 0 or similarities.max() == 0:
        return (
            "Jag kunde inte hitta ett direkt svar. Fundera på att omformulera frågan eller läs sammanfattningen.",
            None,
        )

    best_index = int(similarities.argmax())
    supporting_sentence = sentences[best_index]
    answer = supporting_sentence
    return answer, supporting_sentence
