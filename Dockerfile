ARG PYVER
FROM ${PYVER}

WORKDIR /code

COPY setup.py requirements.txt /code/
COPY django_sorcery/__version__.py /code/django_sorcery/
RUN touch README.rst && \
 pip install -r requirements.txt

RUN apt-get update && apt-get install -y postgresql-client && apt-get clean

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} sorcerer && \
 useradd -l -u ${USER_ID} -g ${GROUP_ID} -m -d /home/sorcerer sorcerer

USER sorcerer
