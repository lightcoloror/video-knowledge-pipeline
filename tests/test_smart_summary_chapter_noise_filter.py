from video_knowledge_pipeline.smart_summary_chapters import (
    _chapter_title,
    _is_non_topic_noise,
    _ranked_sentences,
)


def test_meeting_ui_and_host_transitions_are_not_reader_summary_sentences() -> None:
    bucket = [
        {"raw_text": "您已静音。下面有请王老师分享。客户沟通要先确认真实需求。"}
    ]

    sentences = _ranked_sentences(bucket)

    assert sentences == ["客户沟通要先确认真实需求"]


def test_genuine_long_business_statement_is_not_removed_by_keyword() -> None:
    sentence = "这次会议的核心不是排名播报，而是解释如何根据客户需求设计保障方案"

    assert _is_non_topic_noise(sentence) is False


def test_chapter_title_never_uses_filtered_ui_text() -> None:
    title = _chapter_title(
        2,
        ["解除静音", "先确认客户需求，再讨论预算与方案"],
        [{"text": "共享屏幕"}],
    )

    assert title == "先确认客户需求，再讨论预算与方案"
