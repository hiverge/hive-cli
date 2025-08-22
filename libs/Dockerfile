FROM temp-image:latest

RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv pip install --system --requirement pyproject.toml

COPY main.py .
COPY sandbox_utils sandbox_utils

EXPOSE 8080

ENTRYPOINT ["python", "main.py"]