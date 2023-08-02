# python based ubuntu image
FROM python:3.11-slim-buster
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
WORKDIR /app
COPY . /app
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        # deps for installing poetry
        curl
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN poetry install --no-root
VOLUME ["/app/data"]
ENTRYPOINT [ "poetry", "run", "python3", "/app/app.py", "interact", "/app/data", "Chinese", "English", "y"]
