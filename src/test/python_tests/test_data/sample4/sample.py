"""Sample for column rename: the `amount` column is declared on the schema and
referenced twice via `pl.col("amount")`, so a rename touches all three sites."""

import pandera.polars as pa
import polars as pl
from pandera.typing.polars import DataFrame


class Sales(pa.DataFrameModel):
    amount: pl.Float64
    region: str


def scale(df: DataFrame[Sales]) -> DataFrame[Sales]:
    return df.filter(pl.col("amount") > 0).with_columns(pl.col("amount") * 2.0)
