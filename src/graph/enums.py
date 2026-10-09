from enum import Enum


class Platform(str, Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    MEDIUM = "medium"
    SUBSTACK = "substack"


class Provider(str, Enum):
    GROQ = "groq"
    OPENROUTER = "openrouter"


class Tone(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    INSPIRATIONAL = "inspirational"
    TECHNICAL = "technical"
