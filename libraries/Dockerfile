FROM repo-image:latest


COPY pyproject.toml .
RUN uv pip install --system --requirement pyproject.toml

COPY main.py .
COPY sandbox_utils sandbox_utils

EXPOSE 8080

ENTRYPOINT ["python", "main.py"]