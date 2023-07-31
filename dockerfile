# python based ubuntu image
FROM python:3.11-slim-buster
WORKDIR /app
COPY . /app
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN poetry install --no-root
CMD [ "poetry", "python3", "/app/app.py" ]
VOLUME ["/app/data"]
