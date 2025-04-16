# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12.10-slim

# uft-8 locale
RUN apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8
RUN apt-get update && apt-get install -y supervisor
ENV LANG=en_US.UTF-8

EXPOSE 3000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV TOKEN=7740506271:AAFBPW0-YX91kXIvnQOshElW3mW2ncZb9MQ
ENV CHAT_ID=8024833881

# Install pip requirements
COPY requirements.txt . 
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
