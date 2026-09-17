from __future__ import annotations

import core.synthesize as syn


# One representative topic from each of the 9 curriculum domains
_SAMPLE_TOPICS = [
    "Chunking Strategies",           # Retrieval and Knowledge
    "The Agent Loop",                # Agents and Autonomy
    "LLM as Judge and Rubric Design",  # Evaluation and Quality
    "Reranking",                     # Retrieval and Knowledge
    "Prompt Injection, Direct and Indirect",  # Security and Governance
    "Latency Engineering",           # Platform and Operations
    "Supervised Learning Workflow",  # Classical ML and Deep Learning
    "Prompting and Context Discipline",  # Gen AI Fundamentals
    "Fine-Tuning and PEFT",          # Models: Capability and Adaptation
]


def test_source_prompt_contains_curriculum_topics():
    for topic in _SAMPLE_TOPICS:
        assert topic in syn._SOURCE_SYSTEM, (
            f"_SOURCE_SYSTEM missing curriculum topic: {topic!r}"
        )


def test_term_prompt_contains_curriculum_topics():
    for topic in _SAMPLE_TOPICS:
        assert topic in syn._TERM_SYSTEM, (
            f"_TERM_SYSTEM missing curriculum topic: {topic!r}"
        )


def test_curriculum_topics_list_is_non_empty():
    assert len(syn._CURRICULUM_TOPICS) > 0, "No curriculum topics were loaded"
