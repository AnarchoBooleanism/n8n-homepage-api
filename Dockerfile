# Container for running FastAPI in, with all necessary packages included
FROM python:3.14-slim@sha256:5b3879b6f3cb77e712644d50262d05a7c146b7312d784a18eff7ff5462e77033

# To be passed from Github Actions
ARG GIT_VERSION_TAG=unspecified
ARG GIT_COMMIT_MESSAGE=unspecified
ARG GIT_VERSION_HASH=unspecified

WORKDIR /app

# Install necessary Debian packages
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && \
    apt-get -y install --no-install-recommends \
        tini && \
    rm -rf /var/lib/apt/lists/*

# Create Python virtual environment to install stuff in
ENV VIRTUAL_ENV="/opt/venv"
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install pip packages (including Ansible)
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt 

# Copy over important files
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

COPY app /app

# Final details
# Note: You will want to set POSTGRES_PASSWORD
ENV FASTAPI_HOST="0.0.0.0"
ENV FASTAPI_PORT="8000"
ENV POSTGRES_USER="postgres"
ENV POSTGRES_HOST="localhost"
ENV POSTGRES_PORT="5432"
ENV POSTGRES_DB="n8n"
ENV ROOT_PATH_PREFIX="/"
ENV FORWARDED_ALLOW_IPS="*"

EXPOSE 8000

ENTRYPOINT ["tini", "--", "/docker-entrypoint.sh"]