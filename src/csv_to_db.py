import pandas as pd
import asyncio
from sqlalchemy import Float, Integer
from sqlalchemy.ext.asyncio import create_async_engine
from config import get_db_url  # ← убрал "src."

async def transfer():
    df = pd.read_csv("data/glass.csv")
    engine = create_async_engine(get_db_url())
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: df.to_sql(
                "glass", sync_conn, if_exists="append", index=False,
                dtype={
                    "RI": Float,
                    "Na": Float,
                    "Mg": Float,
                    "Al": Float,
                    "Si": Float,
                    "K": Float,
                    "Ca": Float,
                    "Ba": Float,
                    "Fe": Float,
                    "Type": Integer
                }
            )
        )
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(transfer())