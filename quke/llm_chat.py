"""Sets up all elements required for a chat session."""
import importlib
import logging  # functionality managed by Hydra
import os
from collections import defaultdict
from datetime import datetime

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from mdutils.fileutils import MarkDownFile
from mdutils.mdutils import MdUtils

from . import ClassImportDefinition


def chat(
    vectordb_location: str,
    embedding_import: ClassImportDefinition,
    vectordb_import: ClassImportDefinition,
    llm_import: ClassImportDefinition,
    llm_parameters,
    prompt_parameters,
    output_file,
) -> object:
    """Initiates a chat with an LLM.

    Sets up all components required for the chat including the LLM,
    embedding model, vector store, chat memory, retriever and actual
    questions.
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

        # print(qa({"question": question}))

        # erik = source_documents
        # print(f"==============={erik}")

        chat_output(question, result)
        chat_output_to_file(result, output_file)

    logging.info("=======================")

    return qa


def chat_output(question: str, result: dict) -> None:
    """Logs a chat question and anwer."""
    logging.info("=======================")
    logging.info(f"Q: {question}")
    logging.info(f"A: {result['answer']}")

    src_docs = [doc.metadata for doc in result["source_documents"]]
    src_docs = dict_crosstab(src_docs, "source", "page")
    for key, value in src_docs.items():
        logging.info(f"Source document: {key}, Pages used: {value}")


# TODO: Either I do not understand mdutils or it is an unfriendly package when trying to append.
def chat_output_to_file(result: dict, output_file) -> None:
    """Populates a record of the chat with the LLM into a markdown file."""
    first_write = not os.path.isfile(output_file["path"])

    mdFile = MdUtils(file_name="tmp.md")

    if first_write:
        mdFile.new_header(1, "LLM Chat Session with quke")
        mdFile.write(
            datetime.now().astimezone().strftime("%a %d-%b-%Y %H:%M %Z"), align="center"
        )
        mdFile.new_paragraph("")
        mdFile.new_header(2, "Experiment settings", header_id="settings")
        mdFile.insert_code(output_file["conf_yaml"], language="yaml")
        mdFile.new_header(2, "Chat", header_id="chat")
    else:
        existing_text = MarkDownFile().read_file(file_name=output_file["path"])
        mdFile.new_paragraph(existing_text)

    mdFile.new_paragraph(f"Q: {result['question']}")
    mdFile.new_paragraph(f"A: {result['answer']}")

    src_docs = [doc.metadata for doc in result["source_documents"]]
    src_docs = dict_crosstab(src_docs, "source", "page")
    for key, value in src_docs.items():
        mdFile.new_paragraph(f"Source document: {key}, Pages used: {value}")

    new = MarkDownFile(name=output_file["path"])

    new.append_end((mdFile.get_md_text()).strip())


def dict_crosstab(source, key, listed, missing="NA"):
    """Limited and simple version of a crosstab query on a dict."""
    dict_subs = []
    for d in source:
        dict_subs.append({key: d[key], listed: d.get(listed, missing)}.values())

    d = defaultdict(list)
    for k, v in dict_subs:
        d[k].append(v)
        d[k] = list(set(d[k]))

    return dict(d)  # TODO: consider sorted(d.items())
