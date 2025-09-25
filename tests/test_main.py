import os
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List

import pytest
from aiohttp import web

from hive_cli.libs import main


@asynccontextmanager
async def start_server(handler: Callable[[web.Request], web.StreamResponse]):
    """
    Spin up a tiny aiohttp server for tests.
    `handler` runs for POST /.
    Yields the full endpoint URL.
    """
    app = web.Application()
    app.router.add_post("/", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    # Discover the bound port
    sockets = list(site._server.sockets)
    port = sockets[0].getsockname()[1]
    url = f"http://127.0.0.1:{port}/"
    try:
        yield url
    finally:
        await runner.cleanup()


def _write_repo_script(repo_dir: str, file: str, content: str):
    path = os.path.join(repo_dir, file)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# -----------------------
# main_loop integration
# -----------------------


@pytest.mark.asyncio
async def test_main_loop_run_then_stop(monkeypatch):
    """
    Emulate the two-request conversation:
      1) client posts {"status":"ready"} -> server returns a RUN job payload
      2) client posts result -> server returns {"action":"stop"}
    """
    # 1) stub the executor to return a deterministic result
    calls = {"ran": 0}

    def fake_exec(code, args, timeout, memory_limit, evaluation_script):
        calls["ran"] += 1
        assert code == {"file.py": "print('ok')"}
        assert args == ["a", 1]
        assert timeout == 2.5
        assert memory_limit == 64
        assert evaluation_script == "evaluator.py"
        return {"output": "DONE", "metainfo": "ok"}

    monkeypatch.setattr(
        main, "execute_python_function", fake_exec, raising=True
    )

    # 2) stateful server that serves run then stop
    posts: List[Dict[str, Any]] = []
    step = {"n": 0}

    async def handler(request: web.Request):
        payload = await request.json()
        posts.append(payload)
        if step["n"] == 0:
            step["n"] += 1
            return web.json_response(
                {
                    "action": "run",
                    "code": {"file.py": "print('ok')"},
                    "timeout": 2.5,
                    "memory_limit": 64,
                    "args": ["a", 1],
                    "evaluation_script": "evaluator.py",
                }
            )
        else:
            # Validate we posted back a result
            assert "result" in payload
            assert payload["result"] == {"output": "DONE", "metainfo": "ok"}
            return web.json_response({"action": "stop"})

    async with start_server(handler) as endpoint:
        await main.main_loop(
            endpoint=endpoint,
            initial_delay=0.01,
            delay_multiplier=1.2,
            request_timeout=5.0,
        )

    # We should have posted twice: ready, then result
    assert len(posts) == 2
    assert posts[0] == {"status": "ready"}
    assert calls["ran"] == 1


@pytest.mark.asyncio
async def test_main_loop_unknown_action_raises():
    async def handler(request: web.Request):
        # Always return an unknown action
        return web.json_response({"action": "surprise"})

    async with start_server(handler) as endpoint:
        with pytest.raises(ValueError):
            await main.main_loop(endpoint=endpoint)
