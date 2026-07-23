import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.core import http_client, setup_logging
from app.main import SOURCES, _extract_source

async def main():
    setup_logging()
    http_client.start()
    try:
        results = await asyncio.gather(
            *(_extract_source(source_name) for source_name in SOURCES),
            return_exceptions=True,
        )
        for source_name, result in zip(SOURCES, results):
            if isinstance(result, Exception):
                print(f"[{source_name}] 실패: {result}")
            else:
                print(f"[{source_name}] 성공: {len(result)}개")
    finally:
        await http_client.stop()


if __name__ == "__main__":
    asyncio.run(main())
