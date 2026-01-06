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
COPY . /app


RUN make web2py
RUN uv sync
RUN echo "map_admin $$USER postgres" | sudo tee -a /etc/postgresql/*/main/pg_ident.conf
RUN sudo sed -i '/local *all *postgres *peer/ s/$$/ map=map_admin/' /etc/postgresql/*/main/pg_hba.conf

CMD ["../web2py/web2py.py", "--password", "pci", "--ip", "0.0.0.0"]
