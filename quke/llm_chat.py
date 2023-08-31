"""Sets up all elements required for a chat session."""
import importlib
import logging  # functionality managed by Hydra
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from mdutils.fileutils import MarkDownFile  # type: ignore
from mdutils.mdutils import MdUtils  # type: ignore

from . import ClassImportDefinition


def chat(
    vectordb_location: str,
    embedding_import: ClassImportDefinition,
    vectordb_import: ClassImportDefinition,
    llm_import: ClassImportDefinition,
    llm_parameters: dict,
    prompt_parameters: dict,
    output_file: dict,
) -> object:
    """Initiates a chat with an LLM.

    Sets up all components required for the chat including the LLM,
    embedding model, vector store, chat memory, retriever and actual
    questions.

    Args:
        vectordb_location: Folder of vector store.
        embedding_import: Definition of embedding model.
        vectordb_import: Definition of vector store.
        llm_import: Definition of LLM.
        llm_parameters: dict provided as **kwargs to LLM model class.
        prompt_parameters: List of questions to ask the LLM.
        output_file: Folder where result file will be saved.

    Returns:
        Object containing chat history.
    """
    module = importlib.import_module(embedding_import.module_name)
    class_ = getattr(module, embedding_import.class_name)
    embedding = class_()

    logging.warning(
        "CAUTION: This function uses external compute services "
        "(like OpenAI or HuggingFace). This is likely to cost money."
    )
    module = importlib.import_module(vectordb_import.module_name)
    class_ = getattr(module, vectordb_import.class_name)
    vectordb = class_(embedding_function=embedding, persist_directory=vectordb_location)

    module = importlib.import_module(llm_import.module_name)
    class_ = getattr(module, llm_import.class_name)
    llm = class_(**llm_parameters)

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    qa = ConversationalRetrievalChain.from_llm(
        llm,
        retriever=vectordb.as_retriever(),
        memory=memory,
        return_source_documents=True,
    )

    # NOTE: trial API keys may have very restrictive rules. It is plausible that you run into
    # constraints after the 2nd question.
    for question in prompt_parameters:
        result = qa({"question": question})

        chat_output(result)
        chat_output_to_file(result, output_file)

    logging.info("=======================")

    return qa


def chat_output(result: dict) -> None:
    """Logs a chat question and anwer.

    Args:
        result: dict with the answer from the LLM. Expects 'question', 'answer' and 'source' keys,
        'page' key optionally.
    """
    logging.info("=======================")
    logging.info(f"Q: {result['question']}")
    logging.info(f"A: {result['answer']}")

    src_docs = [doc.metadata for doc in result["source_documents"]]
    src_docs_pages_used = dict_crosstab(src_docs, "source", "page")
    for key, value in src_docs_pages_used.items():
        logging.info(f"Source document: {key}, Pages used: {value}")


# TODO: Either I do not understand mdutils or it is an unfriendly package when trying to append.
def chat_output_to_file(result: dict, output_file: dict) -> None:
    """Populates a record of the chat with the LLM into a markdown file.

    Args:
        result: dict with the answer from the LLM. Expects 'question', 'answer' and 'source' keys,
        'page' key optionally.
        output_file: File name to which the record is saved.
    """
    first_write = not Path(output_file["path"]).is_file()

    md_file = MdUtils(file_name="tmp.md")

    if first_write:
        md_file.new_header(1, "LLM Chat Session with quke")
        md_file.write(
            datetime.now().astimezone().strftime("%a %d-%b-%Y %H:%M %Z"), align="center"
        )
        md_file.new_paragraph("")
        md_file.new_header(2, "Experiment settings", header_id="settings")
        md_file.insert_code(output_file["conf_yaml"], language="yaml")
        md_file.new_header(2, "Chat", header_id="chat")
    else:
        existing_text = MarkDownFile().read_file(file_name=output_file["path"])
        md_file.new_paragraph(existing_text)

    md_file.new_paragraph(f"Q: {result['question']}")
    md_file.new_paragraph(f"A: {result['answer']}")

    src_docs = [doc.metadata for doc in result["source_documents"]]
    src_docs_pages_used = dict_crosstab(src_docs, "source", "page")
    for key, value in src_docs_pages_used.items():
        md_file.new_paragraph(f"Source document: {key}, Pages used: {value}")

    new = MarkDownFile(name=output_file["path"])

    new.append_end((md_file.get_md_text()).strip())


def dict_crosstab(source: list, key: str, listed: str, missing: str = "NA") -> dict:
    """Limited and simple version of a crosstab query on a dict.

    Args:
        source: List of dicts. Two elements per dict will be considered: 'key' and 'listed'.
        key: Every dict should contain an entry for 'key'.
        listed: The key for the element in the dict considered to contain the value.
        missing: Value to be used if dict has no key for 'listed'.

    Returns:
        A dictionary containing 'keys' and a list of values for each 'key'.

    >>> a = {'name': 'a', 'number': 2}
    >>> b = {'name': 'a', 'number': 3, 'number_2': 3}
    >>> c = {'name': 'a', 'number': 2}
    >>> d = {'name': 'd', 'number': 1}
    >>> e = {'name': 'e', 'number_3': 2}
    >>> dict_crosstab([e, b, c, d, a], 'name', 'number')
    {'e': ['NA'], 'a': [2, 3], 'd': [1]}
    """
    dict_subs = [{key: d[key], listed: d.get(listed, missing)}.values() for d in source]

    d = defaultdict(list)
    for k, v in dict_subs:
        d[k].append(v)
        d[k] = list(set(d[k]))

    return dict(d)  # TODO: consider sorted(d.items())
