FROM python:3.11-slim

LABEL maintainer="RTF Core Team"
LABEL description="RedTeam Framework v2.0 — Enterprise RedTeam Platform"

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY framework/ ./framework/
COPY rtf.py .
COPY config/ ./config/

RUN mkdir -p data logs tools wordlists payloads labs scripts

RUN useradd -m -s /bin/bash rtf && chown -R rtf:rtf /app
USER rtf

EXPOSE 8000 5000

ENTRYPOINT ["python", "rtf.py"]
CMD ["api"]
