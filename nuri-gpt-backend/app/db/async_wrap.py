"""동기 Supabase 호출을 스레드풀에서 실행하는 유틸

supabase-py의 `.execute()`는 블로킹 I/O이므로
async def에서 직접 호출하면 이벤트 루프가 막힌다.
asyncio.to_thread로 감싸면 스레드풀에서 실행되어
다른 요청이 동시에 처리될 수 있다.
"""

import asyncio
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")


async def run_sync(func: Callable[..., T], *args, **kwargs) -> T:
    """블로킹 동기 함수를 스레드풀에서 실행한다.

    Usage:
        result = await run_sync(repo.client.table("templates").select("*").eq("user_id", uid).execute)
        # 또는 람다로 인자 전달:
        result = await run_sync(lambda: repo.client.table("templates").select("*").execute())
    """
    return await asyncio.to_thread(func, *args, **kwargs)
