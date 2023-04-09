FROM buildpack-deps:buster

RUN mkdir -p /opt/pyenv &&\
    curl -sL https://github.com/pyenv/pyenv/archive/refs/heads/master.tar.gz | \
    tar -C /opt/pyenv --strip-components 1 -xz && \
    apt-get update && \
    apt-get install -y postgresql-client && \
    apt-get clean

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} sorcerer && \
    useradd -l -u ${USER_ID} -g ${GROUP_ID} -m -d /home/sorcerer sorcerer && \
    mkdir -p /code && chown -R sorcerer:sorcerer /code

USER sorcerer
ENV PATH=/opt/pyenv/bin:/home/sorcerer/.pyenv/shims:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
WORKDIR /code

RUN pyenv install 3.6:latest
RUN pyenv install 3.7:latest
RUN pyenv install 3.8:latest
RUN pyenv install 3.9:latest
RUN pyenv install 3.10:latest
RUN pyenv install 3.11:latest

RUN pyenv install pypy3.6:latest
RUN pyenv install pypy3.7:latest
RUN pyenv install pypy3.8:latest
RUN pyenv install pypy3.9:latest

RUN pyenv global $(pyenv versions | grep ' 3.11.') && \
    pip install pre-commit tox && \
    pyenv global $(pyenv versions | grep -v system | cut -c 3- | cut -d' ' -f1)
