import pandera.polars as pa
import polars as pl
from pandera.typing.polars import DataFrame

from schema import Sales


class Taxed(pa.DataFrameModel):
    amount: pl.Float64
    region: str
    tax: pl.Int64


def with_tax(df: DataFrame[Sales]) -> DataFrame[Taxed]:
    return df.with_columns((pl.col("amount") * 0.1).alias("tax"))
