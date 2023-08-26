"""Reads documents from a provided directory, performs embedding and captures the embeddings in a vector store."""
import importlib
import logging  # functionality managed by Hydra
import os
import shutil
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# [ ] TODO: PyMU is faster, PyPDF more accurate: https://github.com/py-pdf/benchmarks
from langchain.document_loaders import CSVLoader, PyMuPDFLoader, TextLoader

from . import ClassImportDefinition, ClassRateLimit, DatabaseAction


@dataclass
class DocumentLoaderDef:
    """Definition for LangChain document loaders."""

    ext: str = "pdf"
    loader: object = PyMuPDFLoader
    kwargs: defaultdict[dict] = field(default_factory=dict)  # empty dict


DOC_LOADERS = [
    DocumentLoaderDef(ext="pdf", loader=PyMuPDFLoader),
    DocumentLoaderDef(ext="txt", loader=TextLoader, kwargs={"encoding": "utf8"}),
    DocumentLoaderDef(ext="csv", loader=CSVLoader),
]
"""Defines the kind of source documents to be searched (specifically to be embedded into the vector store)."""


def get_loaders(src_doc_folder: str, loader: DocumentLoaderDef) -> list:
    """Returns loaders for each relevant file in the provided folder.

    LangChain loaders are used to load various types of documents in preparation
    of embedding and persisting in vector stores.

    Args:
        src_doc_folder: The folder of the source files.
        loader: Definition of the loader. Loaders exist for example for
        pdf, text and csv files.

    Returns:
        A list of loaders to be used to read the text from source documents.
    """
    ext = loader.ext

    # to make ext case insensitive
    ext = "".join([f"[{ch}{ch.swapcase()}]" for ch in ext])

    src_file_names = Path(src_doc_folder).rglob(f"**/*.{ext}")

    # TODO: Problem with embedding more than 2 files at once, or some number of pages/chunks (using HF)?
    # Error message does not really help. Appending in steps does work.
    loaders = [
        loader.loader(str(pdf_name), **loader.kwargs) for pdf_name in src_file_names
    ]

    return loaders


def get_pages_from_document(src_doc_folder: str) -> list:
    """Reads documents from the directory/folder provided and returns a list of pages and metadata.

    Args:
        src_doc_folder: Folder containing the source documents.

    Returns:
        List containing one page per list item, as text.
    """
    pages = []
    for docloader in DOC_LOADERS:
        for loader in get_loaders(src_doc_folder, docloader):
            pages.extend(loader.load())

    try:
        logging.info(
            f"Document loaded: {len(pages)} pages, last one {pages[-1].metadata}"
        )
    except Exception:
        logging.warning(
            f"No source documents loaded. No valid files found in {src_doc_folder}. "
            "Must be .pdf, .txt or .csv."
        )

    return pages


def get_chunks_from_pages(pages: list, splitter_params: dict) -> list:
    """Splits pages into smaller chunks used for embedding.

    Args:
        pages: List with page text of a document(s).
        splitter_params: Dictionary with settings for splitting logic, having
        keys splitter_args and splitter_import.
        splitter_args are provided to the splitter function as **kwargs. Note that if a keyword
        contains 'func' the value will be evaluated as a python function (only 'len' allowed).

    Returns:
        A list of smaller text chunks from the pages. In a next step to be used for embedding.
    """
    # TODO: eval() is a security risk. Hence a safe_list of functions is provided; severely
    # limiting risk and flexibility.
    # TODO: The other limiting factor: any parameter containing 'func' is eval()-ed into a function reference;
    # also no other parameter is.
    safe_function_list = ["len"]
    for key in splitter_params["splitter_args"]:
        if ("func".lower() in key.lower()) and splitter_params["splitter_args"][
            key
        ] in safe_function_list:
            splitter_params["splitter_args"][key] = eval(  # noqa: S307
                splitter_params["splitter_args"][key]
            )

    module = importlib.import_module(splitter_params["splitter_import"].module_name)
    class_ = getattr(module, splitter_params["splitter_import"].class_name)
    splitter = class_

    text_splitter = splitter(**splitter_params["splitter_args"])

    chunks = text_splitter.split_documents(pages)

    logging.info(f"Documents split. {len(chunks)} chunks from {len(pages)} pages.")
    return chunks


def embed(
    src_doc_folder: str,
    vectordb_location: str,
    embedding_import: ClassImportDefinition,
    embedding_kwargs: dict,
    vectordb_import: ClassImportDefinition,
    rate_limit: ClassRateLimit,
    splitter_params: dict,
    write_mode: DatabaseAction = DatabaseAction.NO_OVERWRITE,
) -> int:
    """Reads documents from a provided directory, performs embedding and captures the embeddings in a vector store.

    Args:
        src_doc_folder: Folder containing the source documents.
        vectordb_location (str): Folder of vector store database.
        embedding_import: Definition for embedding model.
        embedding_kwargs: **kwargs to be provided to embedding class.
        vectordb_import: Definition of vector store.
        rate_limit: Rate limiting info. Used as a basic limiter dealing with 3rd party API limits.
        splitter_params: Specifications for text splitting logic.
        write_mode: Wether to OVERWRITE, APPEND or NO_OVERWRITE the vector store. NO_OVERWRITE will
        not embed anything if a vector store exists at the vectordb_location.

    Returns:
        The number of text chunks embedded.
    """
    logging.info(f"Starting to embed into VectorDB: {vectordb_location}")

    # if folder does not exist, or write_mode is APPEND no need to do anything here.
    if (
        Path(vectordb_location).exists()
        and (not Path(vectordb_location).is_file())
        and os.listdir(vectordb_location)
    ):
        # path exists and is not empty - assumed to contain vectordb
        if write_mode == DatabaseAction.NO_OVERWRITE:  # skip embedding
            logging.info(
                f"No new embeddings created. Embedding database already exists at "
                f"{vectordb_location!r}. Remove database folder, or change embedding config "
                "vectorstore_write_mode to OVERWRITE or APPEND."
            )
            return
        if (
            write_mode == DatabaseAction.OVERWRITE
        ):  # remove exising database before embedding
            # TODO: Is this too harsh to delete the full folder? At least create a backup?
            logging.warning(
                f"The folder containing the embedding database ({vectordb_location}) and all its contents "
                "about to be overwritten."
            )
            shutil.rmtree(vectordb_location)

    # get bite sized chunks from source documents
    chunks = get_chunks_from_pages(
        get_pages_from_document(src_doc_folder), splitter_params
    )

    logging.warning(
        "CAUTION: This function uses external compute services (like OpenAI or HuggingFace). "
        "This is likely to cost money."
    )

    # Use chunker to embed in chunks with a wait time in between. As a basic way to deal with some rate limiting.
    def chunker(seq: list, size: int) -> list:
        return (seq[pos : pos + size] for pos in range(0, len(seq), size))

    c = 0
    for fewer_chunks in chunker(chunks, rate_limit.count_limit):
        if c > 0:
            delay = rate_limit.delay
            logging.info(f"Sleeping for {delay} seconds due to rate limiter.")
            time.sleep(delay)

        c += embed_these_chunks(
            fewer_chunks,
            vectordb_location,
            embedding_import,
            embedding_kwargs,
            vectordb_import,
        )

    return c


def embed_these_chunks(
    chunks: list,
    vectordb_location: str,
    embedding_import: ClassImportDefinition,
    embedding_kwargs: dict,
    vectordb_import: ClassImportDefinition,
) -> int:
    """Embed the provided chunks and capture into a vector store.

    Args:
        chunks: List of text chunks to be embedded.
        vectordb_location: Location of the folder containing the embedding database.
        embedding_import: Definition of embedding model ('to build Python import statement').
        embedding_kwargs: Dictionary provided as **kwargs for embedding class.
        vectordb_import: Definition of vector store ('to build Python import statement').

    Returns:
        Number of chunks embedded and captured in vector store.
    """
    module = importlib.import_module(embedding_import.module_name)
    class_ = getattr(module, embedding_import.class_name)
    embedding = class_(**embedding_kwargs)

    module = importlib.import_module(vectordb_import.module_name)
    class_ = getattr(module, vectordb_import.class_name)
    vectordb_type = class_()

    vectordb = vectordb_type.from_documents(
        documents=chunks, embedding=embedding, persist_directory=vectordb_location
    )

    vectordb.persist()

    logging.info(f"{len(chunks)} chunks persisted into database at {vectordb_location}")

    return len(chunks)
