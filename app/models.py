from pydantic import BaseModel, Field, model_validator
from typing import Literal

class CompanyBase(BaseModel):
    """
    Extract 과정에서 사용
    Theme 크롤링 시 해당 테마 내 속한 종목에 대한 모델링
    """
    name: str = Field(..., description="주식 종목명", examples=["삼성전자"])
    srtnCd: str = Field(..., min_length=6, max_length=7, description="KRX 거래소 단축 코드")
    reason: str | None = Field(None, description="테마 편입 이유 (추후 테마-주식 간 Relationship 설정 시 사용)")

class Company(BaseModel):
    """
    CompanyBase를 가지고 실제 Load 시 사용할 종목 모델
    """
    name: str = Field(..., description="주식 종목명", examples=["삼성전자"])
    srtnCd: str = Field(..., min_length=6, max_length=7, description="KRX 거래소 단축 코드")
    market: Literal["KOSPI", "KOSDAQ"] = Field(description="거래소 구분")
    clpr: int = Field(..., description="종가")
    vs: int = Field(..., description="전일대비 등락")
    fltRt: float = Field(..., description="등락률")
    trqu: int = Field(...,description="거래량")
    trPrc: int = Field(..., description="거래대금")
    mrktTotAmt: int = Field(..., description="시가총액")

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
                'mrktTotAmt': int,
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
    # AntWinner처럼 개별 ID가 없는 경우에는 None 값이다
    source_theme_id: int | None = Field(None, description="크롤링 시점 source별 원본 테마 ID")
    description: str = Field(default="", description="테마 설명 및 개요")
    companies: list[CompanyBase] = Field(default=[], description="해당 테마에 속한 주식 리스트")