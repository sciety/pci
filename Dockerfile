FROM ubuntu:latest
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    git \
    python3 \
    python3-pip \
    python3-venv \
    sudo \
    virtualenvwrapper \
    libsystemd-dev \
    postgresql \
    postgresql-contrib \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY Makefile .python-version pyproject.toml /app/

COPY utils /app/utils
RUN make web2py

RUN uv sync

# Install hivemind binary
RUN apt-get update && apt-get install -y curl && \
    curl -L -o /tmp/hivemind.gz https://github.com/DarthSim/hivemind/releases/download/v1.1.0/hivemind-v1.1.0-linux-amd64.gz && \
    gunzip -c /tmp/hivemind.gz > /usr/local/bin/hivemind && \
    chmod +x /usr/local/bin/hivemind && \
    rm -f /tmp/hivemind.gz

# Some DB setup copied from makefile
RUN echo "map_admin $$USER postgres" | sudo tee -a /etc/postgresql/*/main/pg_ident.conf
RUN sudo sed -i '/local *all *postgres *peer/ s/$$/ map=map_admin/' /etc/postgresql/*/main/pg_hba.conf

# Initialize DB directory
ENV PGDATA=/var/lib/postgresql/data
RUN mkdir -p "$PGDATA" && \
    chown -R postgres:postgres "$PGDATA" && \
    sudo -u postgres bash -c "/usr/lib/postgresql/16/bin/initdb -D $PGDATA"

# Initialize database using Make target
COPY sql_dumps /app/sql_dumps
RUN sudo -u postgres /usr/lib/postgresql/16/bin/pg_ctl -D "$PGDATA" -w start && \
    sudo -u postgres make db && \
    sudo -u postgres /usr/lib/postgresql/16/bin/pg_ctl -D "$PGDATA" -m fast -w stop

COPY . /app
RUN make conf init
CMD ["hivemind"]
