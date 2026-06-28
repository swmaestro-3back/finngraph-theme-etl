from neo4j import AsyncGraphDatabase, AsyncSession
from typing import AsyncGenerator
from contextlib import asynccontextmanager

# BoltDriver
# It addresses a single database machine. This may be a standalone server or could be a specific member of a cluster.
# Connections established by a BoltDriver are always made to the exact host and port detailed in the URI.

# Neo4jDriver
# The routing behaviour works in tandem with Neo4j’s Causal Clustering feature by directing read and write behaviour to appropriate cluster members.

class Neo4jDatabase:
    # constructor
    def __init__(self) -> None:
        self._driver = None

    # URI에 맞는 Driver 생성 (BoltDriver 또는 Neo4jDriver)
    def init_driver(self, uri: str, auth: tuple):
        try:
            self._driver = AsyncGraphDatabase.driver(uri, auth=auth)
        except Exception as e:
            raise e
    
    async def close(self):
        if self._driver:
            await self._driver.close()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self._driver:
            raise RuntimeError("Neo4j Driver is not initialized. Call init_driver first.")
        
        session = self._driver.session()

        try:
            # yield 함수를 만나는 순간
            # 일시정지 후 session 객체 반환하면서 제어권 넘기기
            yield session
        # get_session을 호출한 부모함수가 종료되면 다시 재개되며 finally 블록 실행
        finally:
            await session.close()

# 전역적으로 하나의 객체만 사용
# 싱글톤 패턴 적용
neo4j_database = Neo4jDatabase()