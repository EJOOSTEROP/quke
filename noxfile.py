# nox is installed outside of poetry. VS Code is using Poetry Python interpreter,
# which does not know nox. Hence, use the terminal to run nox.
# TODO: apply some of this: https://github.com/cjolowicz/hypermodern-python/blob/master/noxfile.py#L14
# especially look at roughly line 51, flake/lint
import nox

nox.options.sessions = ["black", "ruff"]


# TODO: Is this an option: https://nox-poetry.readthedocs.io/en/stable/
# TODO: or a better option: https://github.com/pdm-project/pdm (instead of Poetry)
@nox.session
def flake(session):
    session.install(
        "flake8",
        "flake8-docstrings",
        "flake8-copyright",
        "flake8-annotations",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-import-order",
        "darglint",
    )
    session.run("flake8", "./quke/")


@nox.session
def black(session):
    session.install("black")
    session.run("black", "./quke/")


@nox.session
def ruff(session):
    session.install("ruff")
    session.run("ruff", "check", "./quke/", "./tests/", "pyproject.toml")


@nox.session
def test(session):
    # Not certain this is a good approach. But it currently works.
    session.run("pytest", "--cov=quke", "tests/")

    # TODO: test_files = session.posargs if session.posargs else []
    # TODO: session.run("pytest", "--cov=quke", *test_files)


@nox.session
def mypy(session):
    session.install("mypy")
    session.run(
        "mypy",
        "./quke",
        "--python-executable",
        "/home/vscode/.cache/pypoetry/virtualenvs/quke-61FoJWY3-py3.11/bin/python",
    )
