import asyncio

from models import Company, Theme
from utils.krx import get_stock_by_krx

async def transform(themes: list[Theme]) -> list[Theme]:
    """
    1. 각 테마들을 받아 CompanyBase를 순회함
    2. 순회하면서 utils/krx에 있는 api를 바탕으로 데이터 가져와서 Company로 만듦
    3. list[Company]로 만들어서 각 Theme의 companies를 list[Company] 데이터로 대체함
    """
    for theme in themes:
        tasks = [asyncio.to_thread(get_stock_by_krx, c.name) for c in theme.companies]
        results = await asyncio.gather(*tasks)

        companies = []
        for company_base, krx_stock in zip(theme.companies, results):
            if krx_stock is None:
                continue
            companies.append(Company(
                name=krx_stock.name,
                srtnCd=krx_stock.srtnCd,
                reason=company_base.reason,
                market=krx_stock.market,
                clpr=krx_stock.clpr,
                vs=krx_stock.vs,
                fltRt=krx_stock.fltRt,
                trqu=krx_stock.trqu,
                trPrc=krx_stock.trPrc,
                mrkTotAmt=krx_stock.mrkTotAmt,
            ))
        theme.companies = companies

    return themes
