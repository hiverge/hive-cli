FROM temp-image:latest

RUN apt-get update && apt-get install -y \
    python3-pip rsync \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

WORKDIR /app/service

COPY pyproject.toml .
RUN uv pip install --system --break-system-packages --requirement pyproject.toml

COPY . .

RUN rsync -a /app/repo/ /app/.backup/

EXPOSE 8080

ENTRYPOINT ["python", "main.py"]
