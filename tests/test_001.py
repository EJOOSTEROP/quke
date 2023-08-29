import os
from pathlib import Path

import pytest
from hydra import compose, initialize
from omegaconf import DictConfig

from quke.embed import embed, get_chunks_from_pages, get_pages_from_document
from quke.llm_chat import chat, dict_crosstab
from quke.quke import ConfigParser

OUTPUT_FILE = "chat_session.md"
INTERNAL_DATA_FOLDER = "./tests/data/idata/"
SRC_DATA_FOLDER = "./tests/data/src_doc/"
TEXT_FILE = "test.txt"


@pytest.fixture(scope="session")
def GetConfigEmbedOnly():
    with initialize(version_base=None, config_path="./conf"):
        return compose(
            config_name="config",
            overrides=[
                "embed_only=True",
                f"experiment_summary_file={OUTPUT_FILE}",
                f"internal_data_folder={INTERNAL_DATA_FOLDER}",
                "embedding.vectordb.vectorstore_write_mode=overwrite",
            ],
        )


@pytest.fixture(scope="session")
def GetConfigLLMOnly(tmp_path_factory: pytest.TempPathFactory):
    folder = tmp_path_factory.mktemp("output")
    output_file = Path(folder) / OUTPUT_FILE
    with initialize(version_base=None, config_path="./conf"):
        return compose(
            config_name="config",
            overrides=[
                "embed_only=False",
                f"experiment_summary_file={output_file}",
                f"internal_data_folder={INTERNAL_DATA_FOLDER}",
                "embedding.vectordb.vectorstore_write_mode=no_overwrite",
            ],
        )


@pytest.fixture(scope="session")
def GetPages() -> list:
    return get_pages_from_document(SRC_DATA_FOLDER)


@pytest.fixture(scope="session")
def GetChunks(GetPages: list, GetConfigEmbedOnly: DictConfig) -> list:
    return get_chunks_from_pages(
        GetPages, ConfigParser(GetConfigEmbedOnly).get_splitter_params()
    )


@pytest.fixture(scope="session")
def GetCrossTabDicts() -> list:
    a = {"name": "a", "number": 2}
    b = {"name": "a", "number": 3, "number_2": 3}
    c = {"name": "a", "number": 2}
    d = {"name": "d", "number": 1}
    e = {"name": "e", "number_3": 2}

    return [e, b, c, d, a]


def test_documentloader(GetPages: list):
    assert len(GetPages) > 0

    text_file_found = False
    for item in GetPages:
        if TEXT_FILE in item.metadata["source"]:
            text_file_found = True
    assert text_file_found


def test_getchunks(GetChunks: list):
    assert len(GetChunks) == 1  # with current basic test just equals 1


def test_config():
    with initialize(version_base=None, config_path="./conf"):
        cfg = compose(config_name="config", overrides=["embed_only=True"])
        assert cfg.source_document_folder == "./tests/data/src_doc/"
        assert cfg.embed_only is True
        assert (
            len(os.listdir(cfg.source_document_folder)) == 1
        )  # only 1 file for the moment


@pytest.mark.expensive()
# Do the following to exlude this
# poetry run pytest -m 'not expensive'
def test_embed(GetConfigEmbedOnly: DictConfig):
    chunks_embedded = embed(**ConfigParser(GetConfigEmbedOnly).get_embed_params())
    assert chunks_embedded == 1


@pytest.mark.expensive()
# @pytest.mark.skipif(not os.path.exists(os.path.dirname(OUTPUT_FILE)),
# reason=f"Output folder {os.path.dirname(OUTPUT_FILE)} should exist before running test.")
def test_chat(GetConfigLLMOnly: DictConfig):
    from langchain.chains import ConversationalRetrievalChain

    chat_result = chat(**ConfigParser(GetConfigLLMOnly).get_chat_params())
    assert isinstance(chat_result, ConversationalRetrievalChain)
    assert Path(ConfigParser(GetConfigLLMOnly).output_file).is_file()


def test_crosstab_dict(GetCrossTabDicts: list):
    x_result = dict_crosstab(GetCrossTabDicts, "name", "number")
    assert x_result == {"e": ["NA"], "a": [2, 3], "d": [1]}
