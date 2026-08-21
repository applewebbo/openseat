FROM python:3.14-slim-bookworm

WORKDIR /usr/src/app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=prod

# dbbackup shells out to pg_dump, which refuses a server newer than itself:
# keep this at the major version of the database Coolify provisions.
ARG POSTGRES_VERSION=18

# System deps + hivemind (process manager, static binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl ca-certificates gettext gnupg lsb-release \
  && install -d /usr/share/keyrings \
  && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
     | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
     > /etc/apt/sources.list.d/pgdg.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends "postgresql-client-${POSTGRES_VERSION}" \
  && HIVEMIND_VERSION="1.1.0" \
  && ARCH="$(dpkg --print-architecture)" \
  && case "$ARCH" in \
       amd64) HIVEMIND_ARCH="amd64" ;; \
       arm64) HIVEMIND_ARCH="arm64" ;; \
       *) echo "Unsupported arch: $ARCH" >&2; exit 1 ;; \
     esac \
  && curl -fsSL "https://github.com/DarthSim/hivemind/releases/download/v${HIVEMIND_VERSION}/hivemind-v${HIVEMIND_VERSION}-linux-${HIVEMIND_ARCH}.gz" \
     | gunzip > /usr/local/bin/hivemind \
  && chmod +x /usr/local/bin/hivemind \
  && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
  && mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app
ENV PATH=/app/.venv/bin:$PATH

# Dependency layer: cached as long as pyproject.toml/uv.lock are unchanged
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Pre-download the Tailwind CLI so the first boot doesn't pull ~120MB
# IMPORTANT: keep TAILWIND_VERSION aligned with what django-tailwind-cli expects
# (the release skill verifies this on every release)
ARG TAILWIND_VERSION=2.10.13
RUN mkdir -p /app/.django_tailwind_cli \
  && ARCH="$(dpkg --print-architecture)" \
  && case "$ARCH" in \
       amd64) TW_ARCH="x64" ;; \
       arm64) TW_ARCH="arm64" ;; \
       *) echo "Unsupported arch: $ARCH" >&2; exit 1 ;; \
     esac \
  && curl -fsSL "https://github.com/dobicinaitis/tailwind-cli-extra/releases/download/v${TAILWIND_VERSION}/tailwindcss-extra-linux-${TW_ARCH}" \
     -o "/app/.django_tailwind_cli/tailwindcss-extra-linux-${TW_ARCH}-${TAILWIND_VERSION}" \
  && chmod +x "/app/.django_tailwind_cli/tailwindcss-extra-linux-${TW_ARCH}-${TAILWIND_VERSION}"

COPY . /app

EXPOSE 80
CMD ["sh", "./entrypoint.sh"]
