"""Compare Large Language Models' capabilities.

Compare the answering capabilities of different LLMs - for example LlaMa, ChatGPT,
Cohere, Falcon - against user provided document(s) and questions.

LLMs, embeddings and other settings can be specified in configuration files.
"""
from collections import namedtuple
from enum import Enum


class DatabaseAction(Enum):
    """Enum for vectorstore write action.

    Value to be specified in config file.

    Action is performed at folder level. For example, if set to OVERWRITE the
    existing folder will be completely deleted before creating a new vector store.
    """

    NO_OVERWRITE = 0
    APPEND = 1
    OVERWRITE = 2


ClassImportDefinition = namedtuple(
    "ClassImportDefinition", ["module_name", "class_name"]
)
ClassRateLimit = namedtuple("ClassRateLimit", ["count_limit", "delay"])
