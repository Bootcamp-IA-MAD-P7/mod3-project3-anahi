from enum import Enum


class Platform(str, Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    MEDIUM = "medium"
    SUBSTACK = "substack"


class Provider(str, Enum):
    GROQ = "groq"
    OPENROUTER = "openrouter"
