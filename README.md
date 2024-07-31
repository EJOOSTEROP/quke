<!-- Template from https://github.com/othneildrew/Best-README-Template/blob/master/BLANK_README.md
-->


<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- SHIELDS FOR CONSIDERATION
# flake8-annotations
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/flake8-annotations/3.0.1?logo=python&logoColor=FFD43B)](https://pypi.org/project/flake8-annotations/)
[![PyPI](https://img.shields.io/pypi/v/flake8-annotations?logo=Python&logoColor=FFD43B)](https://pypi.org/project/flake8-annotations/)
[![PyPI - License](https://img.shields.io/pypi/l/flake8-annotations?color=magenta)](https://github.com/sco1/flake8-annotations/blob/main/LICENSE)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sco1/flake8-annotations/main.svg)](https://results.pre-commit.ci/latest/github/sco1/flake8-annotations/main)
[![Open in Visual Studio Code](https://img.shields.io/badge/Open%20in-VSCode.dev-blue)](https://github.dev/sco1/flake8-annotations)
-->


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ejoosterop/quke">
    <img src="https://github.com/EJOOSTEROP/quke/blob/main/media/llms.png?raw=true" alt="Logo" width="240" height="160">
  </a>

<h3 align="center">quke</h3>

  <p align="center">
    Compare the answering capabilities of different LLMs - for example LlaMa, ChatGPT, Cohere, Falcon - against user provided document(s) and questions.
    <br />
    <a href="https://github.com/ejoosterop/quke"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <!--
    <a href="https://github.com/ejoosterop/quke">View Demo</a>
    · -->
    <a href="https://github.com/ejoosterop/quke/issues">Report Bug</a>
    ·
    <a href="https://github.com/ejoosterop/quke/issues">Request Feature</a>
  </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>  
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#Base">Base</a></li>
        <li><a href="#specify-models-and-embeddings">Specify models and embeddings</a></li>
        <li><a href="#experiments">Experiments</a></li>
        <li><a href="#configuration">Configuration</a></li>
        <li><a href="#search-your-own-documents">Search your own documents</a></li>
        <li><a href="#limitations">Limitations</a></li>
        <li><a href="#privacy">Privacy</a></li>
      </ul>
    </li>
    <!--
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    -->
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <!--
    <li><a href="#acknowledgments">Acknowledgments</a></li>
    -->
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project
Compare the answering capabilities of different LLMs - for example LlaMa, ChatGPT, Cohere, Falcon - against user provided document(s) and questions.

Specify the different models, embedding tools and vector databases in configuration files.

Maintain reproducable experiments reflecting combinations of these configurations.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started
### Prerequisites
#### Poetry
The instructions assume a Python environment with [Poetry][poetry-url] installed. Development of the tool is done in Python 3.11. While Poetry is not actually needed for the tool to function, the examples assume Poetry is installed.

#### API keys
The tool uses 3rd party hosted inference APIs. API keys need to be specified as environment variables.

The services used:
- [HuggingFace][huggingface-url]
- [OpenAI][openai-url]
- [Cohere][cohere-url]
- [Replicate][replicate-url]

The API keys can be specied in a [.env file][.env-url]. Use the provided .env.example file as an example (enter your own API keys and rename it to '.env').

At present, all services used in the example configuration have free tiers available.

#### sqlite3
sqlite3 v3.35 or higher is required. This is oftentimes installed as part of a Linux install.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Installation
Navigate to the directory that contains the pyproject.toml file, then execute the
```sh
poetry install
```
command.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage
For the examples the project comes with a public financial document for a Canadian Bank (CIBC) as source pdf file.

### Base
In order to run the first example, ensure to specify your HuggingFace API key.

Use the command
```sh
poetry run quke
```
to ask the default questions, using the default embedding and the default LLM.

The answers provided by the LLM - in addition to various other logging messages - are saved in the ./output/ or ./multirun directories in separate date and time subdirectories, including in a file called `chat_session.md`.

The defaults are specified in the config.yaml file (in the ./quke/conf/ directory).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Specify models and embeddings
*Ensure to specify your Cohere API key before running.*

As per the configuration files, the default LLM is Falcon and the default embedding uses HuggingFace embedding.

To specify a different LLM - Cohere in this example - run the following:
```sh
poetry run quke embedding=huggingface llm=cohere question=eps
```

 <!--
 Falcon 7b returns a realistic answer to what is Lufthansa (and provides an EPS number which I did not confirm) using the first question. But it should not have as the document loaded does not mention Lufthansa at all.
 OpenAI and Cohere both state that they cannot know based on the document; openai (and to an extent Cohere) do provide an answer when not specifying 'using only the document provided. I did not check Llama2.
 ```sh
 poetry run quke embedding=huggingface llm=llama2 ++question.questions=['Using only the document provided can you tell what is Lufthansa? End your answer with my pleasure.']

 poetry run quke embedding=huggingface llm=gpt3-5 ++question.questions=['What is Lufthansa','What was their EPS in 2019?']

 ```
-->
<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Experiments
*Ensure to specify your OpenAI API key before running.*

The LLMs, embeddings, questions and other configurations can be captured in experiment config files. The command
```sh
poetry run quke +experiment=openai
```
uses an experiment file openai.yaml (see folder ./config/experiments) which specifies the LLM, embedding and questions to be used. It is equivalent to running:
```sh
poetry run quke embedding=openai llm=gpt4o question=eps
```
Multiple experiments can be run at once as follows:

*Ensure to specify your Replicate API key before running.*
```sh
poetry run quke --multirun +experiment=openai,llama2
```


<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Configuration
LLMs, embeddings, questions, experiments and other items are specified in a set of configuration files. These are saved in the ./config directory.

The [Hydra][hydra-url] package is used for configuration management. Their website explains more about the configuration system in general.

Four different models are specified (ChatGPT, LlaMa2, Falcon, and Cohere); using 4 different APIs (OpenAI, HuggingFace, Cohere and Replicate).

Additional LLMs (or embeddings, questions) can be set up by adding new configuration files.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Search your own documents
The documents to be searched are stored in the ./docs/pdf directory. At present only pdf documents are considered.
Note to set `vectorstore_write_mode` to `append` or `overwrite` in the embedding configuration file (or delete the folder with the existing vector database, in the ./idata folder).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Limitations
The free tiers for the third party services generally come with fairly strict limitations. They differ between services; and may differ over time.

 To try out the tool with your own documents it is best to start with a single small source document, no more than two questions and only one combination of LLM/embedding.

Error messages due to limitations of the APIs are not always clearly indicated as such.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Privacy
The tool uses third party APIs (OpenAI, HuggingFace, Cohere, Replicate). These process your source documents and your questions, to the extent that you provide these. They track your usage of their APIs. They may do other things; I do not know.

The tool uses the [LangChain][langchain-url] Python package to interact with the third party services. I do not know if the package 'leaks' any of the data in any way.

In general I do not know to what extent any of the data is encrypted during transmission.

The tool shares no information with me.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Cohere][cohere.com]][cohere-url]
* [![HuggingFace][huggingface.com]][huggingface-url]
* [![OpenAI][openai.com]][openai-url]
* [![Replicate][replicate.com]][replicate-url]
<br></br>

* [![Hydra][hydra.com]][hydra-url]
* [![LangChain][langchain.com]][langchain-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
<!--
## Roadmap

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3
    - [ ] Nested Feature

See the [open issues](https://github.com/ejoosterop/quke/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>
-->


<!-- CONTRIBUTING -->
<!--
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>
-->


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

<!--
Your Name - [@twitter_handle](https://twitter.com/twitter_handle) - email@email_client.com
-->

Project Link: [https://github.com/ejoosterop/quke](https://github.com/ejoosterop/quke)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
<!--
## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>
-->


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/ejoosterop/quke.svg?style=for-the-badge
[contributors-url]: https://github.com/ejoosterop/quke/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/ejoosterop/quke.svg?style=for-the-badge
[forks-url]: https://github.com/ejoosterop/quke/network/members
[stars-shield]: https://img.shields.io/github/stars/ejoosterop/quke.svg?style=for-the-badge
[stars-url]: https://github.com/ejoosterop/quke/stargazers
[issues-shield]: https://img.shields.io/github/issues/ejoosterop/quke.svg?style=for-the-badge
[issues-url]: https://github.com/ejoosterop/quke/issues
[license-shield]: https://img.shields.io/github/license/ejoosterop/quke.svg?style=for-the-badge
[license-url]: https://github.com/ejoosterop/quke/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/erik-oosterop-9505a21
[product-screenshot]: images/screenshot.png


[cohere-url]: https://cohere.com/
[huggingface-url]: https://huggingface.co/
[hydra-url]: https://hydra.cc/
[langchain-url]: https://python.langchain.com/
[openai-url]: https://openai.com/
[poetry-url]: https://python-poetry.org/
[replicate-url]: https://replicate.com/
[.env-url]: https://pypi.org/project/python-dotenv/

[openai.com]: https://img.shields.io/badge/openai-412991?style=for-the-badge&logo=openai&logoColor=white

[huggingface.com]: https://img.shields.io/badge/huggingface-yellow?style=for-the-badge&logo=huggingface&logoColor=white
[cohere.com]: https://img.shields.io/badge/Cohere-013220?style=for-the-badge&logo=cohere&logoColor=white
[replicate.com]: https://img.shields.io/badge/replicate-black?style=for-the-badge&logo=replicate&logoColor=white

[hydra.com]: https://img.shields.io/badge/hydra-white?style=for-the-badge&logo=python&logoColor=black
[langchain.com]: https://img.shields.io/badge/langchain-white?style=for-the-badge&logo=python&logoColor=black