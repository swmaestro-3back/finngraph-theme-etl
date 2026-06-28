from pydantic import BaseModel, Field
from typing import Literal

class Company(BaseModel):
    name: str = Field(..., description="주식 종목명", examples=["삼성전자"])
    market: Literal["KOSPI", "KOSDAQ"] | None = Field(None, description="소속 시장")
    srtn: str = Field(..., min_length=6, max_length=7, description="KRX 거래소 단축 코드")
    reason: str | None = Field(None, description="해당 테마에 편입된 이유 (추후 Theme-Company간 Relationship 설정 시 사용)")

class Theme(BaseModel):
    name: str = Field(..., description="테마명", examples=["철강"])
    source: Literal["Naver", "Judal", "AntWinner"]
    theme_id: int | None = None
    description: str = Field(default="", description="테마 설명 및 개요")
    companies: list[Company] = Field(default=[], description="해당 테마에 속한 주식 리스트")