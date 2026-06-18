import polars as pl
from pandera.typing.polars import DataFrame

from schema import Sales


def scale(df: DataFrame[Sales]) -> DataFrame[Sales]:
    return df.with_columns(pl.col("amount") * 2.0)
