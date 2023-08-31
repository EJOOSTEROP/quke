"""Sets up all elements required for a chat session."""
import importlib
import logging  # functionality managed by Hydra
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Literal

from jinja2 import Environment, PackageLoader, select_autoescape
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

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

    results = [qa({"question": question}) for question in prompt_parameters]
    chat_output_to_html(results, output_file)
    chat_output_to_html(results, output_file, output_extension="logging")

    logging.info("=======================")

    return qa


def chat_output_to_html(
    results: list[dict],
    output_file: dict,
    output_extension: Literal[".html", ".md", "logging"] = ".html",
) -> None:
    """Write summary of chat experiment into HTML file.

    Args:
        results: list of dicts with the answer from the LLM. Expects 'question', 'answer'
        and 'source' keys; 'page' key optionally.
        output_file: path and other information regarding the output file.
        output_extension: .html or .md. Alteratively logging for python logging.
    """
    env = Environment(loader=PackageLoader("quke"), autoescape=select_autoescape())

    if output_extension.lower() == ".html":
        template_name = "chat_session.html.jinja"
    elif output_extension.lower() == ".md":
        template_name = "chat_session.md.jinja"
    elif output_extension.lower() == "logging":
        template_name = "chat_session.logging.jinja"
    else:
        template_name = "chat_session.html.jinja"

    template = env.get_template(template_name)
    func_dict = {"dict_crosstab": _dict_crosstab_for_jinja}
    template.globals.update(func_dict)

    output = template.render(
        chat_time=datetime.now().astimezone().strftime("%a %d-%b-%Y %H:%M %Z"),
        llm_results=results,
        config=output_file["conf_yaml"],
    )

    if output_extension.lower() == "logging":
        logging.info(output)
    else:
        file_path = Path(output_file["path"]).with_suffix(output_extension)
        with file_path.open("w") as fp:
            fp.write(output)


def _dict_crosstab_for_jinja(sources: list) -> dict:
    """Wrapper around dict_crostab for use from within Jinja.

    Args:
        sources (list): _description_

    Returns:
        dict: _description_
    """
    src_docs = [doc.metadata for doc in sources]
    return dict_crosstab(src_docs, "source", "page")


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
