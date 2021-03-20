ARG PYVER
FROM ${PYVER}

WORKDIR /code

COPY setup.py requirements.txt /code/
COPY django_sorcery/__version__.py /code/django_sorcery/

RUN apt update && \
 apt install -y postgresql-client && \
 touch README.rst && \
 pip install -r requirements.txt
