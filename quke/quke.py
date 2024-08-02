"""Main module to initiate quke, to compare chat results.

LLMs, embedding model, vector store and other components can be congfigured.
"""

import logging  # functionality managed by Hydra
from pathlib import Path

import hydra
from dotenv import find_dotenv, load_dotenv
from hydra.utils import to_absolute_path
from omegaconf import DictConfig, OmegaConf
from rich.console import Console

from quke import ClassImportDefinition, ClassRateLimit, DatabaseAction, embed, llm_chat
from quke import rate_limiter as qrate_limiter

_ = load_dotenv(find_dotenv())


class ConfigParser:
    """Turns config into a more programming friendly and consistent format.

    For core classes and functions groups configuration by
    class/function arguments for convenience.

    Provides an abstraction layer on top of the structure of the
    Hydra configuration files.
    """

    def __init__(self, cfg: DictConfig) -> None:
        """Creates configuration abstraction."""
        self.cfg = cfg

        # TODO: Read from cfg
        self.src_doc_folder = cfg.source_document_folder

        # TODO: Is this sufficiently robust? What if the user wants a folder not related to wcd/pwd?
        self.vectordb_location = str(
            Path.cwd()
            / cfg.internal_data_folder
            / cfg.embedding.vectordb.vectorstore_location
        )
        self.embedding_import = ClassImportDefinition(
            cfg.embedding.embedding.module_name, cfg.embedding.embedding.class_name
        )
        self.vectordb_import = ClassImportDefinition(
            cfg.embedding.vectordb.module_name, cfg.embedding.vectordb.class_name
        )
        self.llm_import = ClassImportDefinition(
            cfg.llm.module_name_llm, cfg.llm.class_name_llm
        )
        self.embedding_rate_limit = ClassRateLimit(
            cfg.embedding.embedding.rate_limit_chunks,
            cfg.embedding.embedding.rate_limit_delay,
        )
        self.embedding_kwargs = self.get_embedding_kwargs(cfg)

        self.splitter_import = ClassImportDefinition(
            cfg.embedding.splitter.module_name, cfg.embedding.splitter.class_name
        )
        self.splitter_args = self.get_args_dict(cfg.embedding.splitter.args)

        try:
            self.write_mode = DatabaseAction[
                (cfg.embedding.vectordb.vectorstore_write_mode).upper()
            ]
        except Exception:
            logging.warning(
                f"Invalid value configured for cfg.embedding.vectorstore_write_mode: "
                f"{cfg.embedding.vectordb.vectorstore_write_mode}. Using no_overwrite instead."
            )
            self.write_mode = DatabaseAction.NO_OVERWRITE

        self.questions = cfg.question.questions

        try:
            if not cfg.embed_only:
                self.embed_only = False
            else:
                self.embed_only = True
        except Exception:
            self.embed_only = False

        # TODO: need something better for output folder
        # https://hydra.cc/docs/tutorials/basic/running_your_app/working_directory/
        try:  # try statement done for testing suite
            self.output_file = str(
                Path(hydra.core.hydra_config.HydraConfig.get()["runtime"]["output_dir"])
                / cfg.experiment_summary_file
            )
        except Exception:
            self.output_file = cfg.experiment_summary_file

        # self.llm_rate_limiter_name = "openai"
        self.llm_rate_limiter_name = getattr(cfg.llm, "rate_limiter", None)

    def get_rate_limiter_kwargs(self) -> dict:
        """Based on the config files returns the set of parameters needed to setup a rate limiter."""
        if not self.llm_rate_limiter_name:
            # raise NotImplementedError("No rate limiter specified in config file.")
            logging.info("No rate_limiter specified in llm config file.")
            return {}

        rate_limiters = OmegaConf.to_container(self.cfg.rate_limiters, resolve=True)
        limiter_index = next(
            (i for i, d in enumerate(rate_limiters) if self.llm_rate_limiter_name in d),
            -1,
        )

        if limiter_index != -1:
            rate_limiter_config = rate_limiters[limiter_index][
                self.llm_rate_limiter_name
            ]
        else:
            logging.warning(
                "Rate limiter specified in llm config file cannot be found in config.yaml."
            )
            # raise NotImplementedError(
            #     "Rate limiter specified in llm config file cannot be found in config.yaml."
            # )

        return rate_limiter_config

    def get_rate_limiter_kwargs_old(self) -> dict:
        """Based on the config files returns the set of parameters needed to setup a rate limiter."""
        if not self.llm_rate_limiter_name:
            raise NotImplementedError("No rate limiter specified in config file.")
            return {}

        def find_index_given_dict_key(list, key: str) -> int:
            """
            Find the index of the first occurrence of a given key in a list of dictionaries.

            Args:
                list (list): A list of dictionaries.
                key (str): The key to search for in the dictionaries.

            Returns:
                int: The index of the first occurrence of the key in the list, or -1 if the key is not found.
            """
            for i, d in enumerate(list):
                if key in d:
                    return i
            return -1

        existing_limiters = OmegaConf.to_container(
            self.cfg.rate_limiters,
            resolve=True,
        )

        limiter_index = find_index_given_dict_key(
            existing_limiters, self.llm_rate_limiter_name
        )

        if limiter_index != -1:
            res = OmegaConf.to_container(
                self.cfg.rate_limiters[limiter_index][self.llm_rate_limiter_name],
                resolve=True,
            )
        else:
            logging.warning(
                "Rate limiter specified in llm config file cannot be found in config.yaml."
            )
            raise NotImplementedError(
                "Rate limiter specified in llm config file cannot be found in config.yaml."
            )
            return {}

        # res = dict(res[rate_limiter_name])
        print(res)
        # print(type(res[rate_limiter_name]))
        # print(res[rate_limiter_name])
        print("Done")
        # print(self.cfg.rate_limiters[limiter_index]["openai"])
        raise NotImplementedError

        return res if isinstance(res, dict) else {}

    def get_embed_params(self) -> dict:
        """Based on the config files returns the set of parameters need to start embedding."""
        return {
            "src_doc_folder": self.src_doc_folder,
            "vectordb_location": self.vectordb_location,
            "embedding_import": self.embedding_import,
            "embedding_kwargs": self.embedding_kwargs,
            "vectordb_import": self.vectordb_import,
            "rate_limit": self.embedding_rate_limit,
            "splitter_params": self.get_splitter_params(),
            "write_mode": self.write_mode,
        }

    def get_chat_params(self) -> dict:
        """Based on the config files returns the set of parameters need to start a chat."""
        return {
            "vectordb_location": self.vectordb_location,
            "embedding_import": self.embedding_import,
            "vectordb_import": self.vectordb_import,
            "llm_import": self.llm_import,
            "llm_parameters": self.get_llm_parameters(),
            "prompt_parameters": self.questions,
            "output_file": self.get_chat_session_file_parameters(self.cfg),
        }

    def get_splitter_params(self) -> dict:
        """Based on the config files returns the set of parameters needed to split source documents."""
        return {
            "splitter_import": self.splitter_import,
            "splitter_args": self.splitter_args,
        }

    def get_args_dict(self, cfg_sub: dict) -> dict:
        """Takes a subset of the Hydra configs and returns the same as a dict."""
        res = OmegaConf.to_container(cfg_sub, resolve=True)
        return res if isinstance(res, dict) else {}

    def create_rate_limiter(self) -> qrate_limiter.InMemoryRateLimiter:
        """Create a new rate limiter and add it to the global dictionary."""
        limiter_kwargs = self.get_rate_limiter_kwargs()

        if limiter_kwargs:
            rate_limiter = qrate_limiter.get_rate_limiter(
                self.llm_rate_limiter_name, **limiter_kwargs
            )
            return rate_limiter

        return None

    def get_llm_parameters(self) -> dict:
        """Based on the config files returns the set of parameters needed to setup an LLM."""
        res = OmegaConf.to_container(self.cfg.llm.llm_args, resolve=True)

        rate_limiter = self.create_rate_limiter()
        if rate_limiter:
            res["rate_limiter"] = rate_limiter

        return res if isinstance(res, dict) else {}

    def get_chat_session_file_parameters(self, cfg: DictConfig) -> dict:
        """Returns the full configuration in a single yaml and file location for output."""
        return {
            "path": self.output_file,
            "conf_yaml": OmegaConf.to_yaml(cfg),
        }

    def get_embedding_kwargs(self, cfg: DictConfig) -> dict:
        """Based on the config files returns the set of parameters needed for embedding."""
        try:
            embedding_kwargs = (
                cfg.embedding.embedding.kwargs if cfg.embedding.embedding.kwargs else {}
            )
        except Exception:
            embedding_kwargs = {}
        return embedding_kwargs


@hydra.main(version_base=None, config_path="conf", config_name="config")
def quke(cfg: DictConfig) -> None:
    """The main function to initiate a chat.

    Including the embedding of the provided source documents.

    Questions, LLM, embedding model, vectordb are specified in config files (using Hydra).
    """
    console = Console()
    config_parser = ConfigParser(cfg)

    embed_parameters = config_parser.get_embed_params()

    print(f"RATE_LIMITER: '{config_parser.get_rate_limiter_kwargs()}'")

    with console.status("Embedding...", spinner="aesthetic"):
        # python -m rich.spinner to see options
        embed.embed(**embed_parameters)
        # Used to log config here: logging.info("\n" + OmegaConf.to_yaml(cfg))

    if not config_parser.embed_only:
        with console.status("Chatting...", spinner="aesthetic"):
            chat_parameters = config_parser.get_chat_params()
            llm_chat.chat(**chat_parameters)

    logging.info(
        f"Source documents loaded from: {to_absolute_path(config_parser.src_doc_folder)}"
    )
    logging.info(
        f"Vector store created in: {to_absolute_path(config_parser.vectordb_location)}"
    )
    logging.info(f"Results captured in: {to_absolute_path(config_parser.output_file)}")


if __name__ == "__main__":
    quke()
