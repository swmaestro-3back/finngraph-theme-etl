from pydantic import BaseModel, Field, model_validator
from typing import Literal

class CompanyBase(BaseModel):
    """
    extract 과정에서 사용
    """
    name: str = Field(..., description="주식 종목명", examples=["삼성전자"])
    srtnCd: str = Field(..., min_length=6, max_length=7, description="KRX 거래소 단축 코드")
    reason: str | None = Field(None, description="테마 편입 이유 (추후 테마-주식 간 Relationship 설정 시 사용)")

class Company(CompanyBase):
    """
    GraphDB load 과정에서 사용
    """
    market: Literal["KOSPI", "KOSDAQ"] = Field(description="거래소 구분")
    clpr: int = Field(..., description="종가")
    vs: int = Field(..., description="전일대비 등락")
    fltRt: float = Field(..., description="등락률")
    trqu: int = Field(...,description="거래량")
    trPrc: int = Field(..., description="거래대금")
    mrkTotAmt: int = Field(..., description="시가총액")

    @model_validator(mode="before")
    @classmethod
    def convert_types(cls, data: dict) -> dict:
        """
        str형을 각 필드 타입에 맞게 형변환 진행
        """
        if isinstance(data, dict):
            numeric_fields = {
                'clpr': int,
                'vs': int,
                'trqu': int,
                'trPrc': int,
                'mrkTotAmt': int,
                'fltRt': float
            }

            for field, target_type in numeric_fields.items():
                if field in data and isinstance(data[field], str):
                    clean_val = data[field].replace(',', '').strip() # 콤마나 양끝 공백 처리
                    try:
                        data[field] = target_type(clean_val)
                    except ValueError:
                        pass
                        
        return data
    
class Theme(BaseModel):
    name: str = Field(..., description="테마명", examples=["철강"])
    source: Literal["naver", "judal", "antwinner"]
    theme_id: int | None = None
    description: str = Field(default="", description="테마 설명 및 개요")
    companies: list[CompanyBase | Company] = Field(default=[], description="해당 테마에 속한 주식 리스트")