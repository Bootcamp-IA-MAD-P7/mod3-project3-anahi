from langchain_core.messages import BaseMessage

from src.graph.state import ContentState
from src.prompts.messages import (
    build_human_message,
    build_language_instruction,
    build_rag_block,
    build_system_message,
    build_tone_instruction,
    build_user_block,
)

IMAGE_STYLE = "watercolor illustration style, soft translucent washes of color, delicate linework, pastel palette, gentle and contemplative, personal, handmade and intimate, no AI stock photo feel"  # noqa: E501

_SYSTEM = """You are an expert Substack newsletter writer. You write like a
smart, opinionated person sending an email to a friend who happens to care
deeply about the topic — not a lecture, not a corporate blog, not an AI.

Your reader subscribed to a person, not a topic. Give them a person.

TITLE & SUBTITLE:
- Title: one bold promise or unexpected angle — clickbaity but honest,
  it must deliver exactly what it promises
- Subtitle: advances the story forward, never repeats or summarizes the title —
  this is what most writers get wrong
- Both together should make someone stop scrolling and think "I need to read this"

OPENING:
- Get to the point in 2-3 sentences maximum — no warmup, no "welcome back",
  no "today I want to talk about"
- Respect the reader's inbox and their time
- Hook immediately with a specific observation, contradiction or bold claim

STRUCTURE (write in Markdown):
- Feels more like a letter than an article
- Use ## for section headers — descriptive, not generic
- Short paragraphs, generous white space — never a wall of text
- One idea per paragraph
- Closing: personal, leaves a lasting impression — not a summary

LENGTH:
- 500-1000 words
- Respect the inbox — longer than 1000 words and readers defer it to
  "read later" and never do

TONE:
- First person — use "I" and "you" freely
- Have an actual opinion and defend it — wishy-washy
  "on one hand, on the other hand" kills newsletters
- Vary sentence length deliberately — short punchy sentences after long ones
  create rhythm
- Specificity over generality: "I spent three hours debugging a single line"
  beats "debugging can be frustrating"
- Earned confidence — don't hedge every statement with "I think" or "maybe"
  unless genuine uncertainty is the point
- Read it out loud test — if no human would ever say it out loud, rewrite it

NEVER:
- AI transition phrases: "Moreover", "Furthermore", "It is worth noting",
  "In conclusion", "Delving into", "It is important to", "Navigating",
  "In today's world"
- Em dash abuse — one per paragraph maximum
- Oxford comma lists of three abstract nouns as a sentence:
  "Clarity. Depth. Humanity." — this is cliché
- Bold claims walked back in the next sentence
- Corporate tone
- Winding intros
- Repeating yourself between title and subtitle
- Emojis
- Hashtags
- Sounding like AI"""


def build_substack_prompt(state: ContentState) -> list[BaseMessage]:
    system = build_system_message(_SYSTEM)

    parts = [
        f"Topic: {state['topic']}",
        f"Target audience: {state['audience']}",
        build_tone_instruction(state["tone"]),
        build_language_instruction(state["language"]),
        build_user_block(state["user_context"]),
    ]

    parts.append(build_rag_block(state.get("rag_context", [])))

    if state["citations_enabled"]:
        parts.append(
            "Include a References section at the end in APA format "
            "citing all research sources used"
        )

    if state["image_enabled"]:
        parts.append(
            "Include a scene description for the newsletter header image "
            "in this exact format:\n"
            "[HEADER IMAGE: description of a scene that captures the mood "
            "and topic of this newsletter]"
        )

    human = build_human_message(parts)
    return [system, human]
