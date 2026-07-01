"""Sample exercising one polypolarism error (pple-undeclared-column) and one warning (pplw-unmodeled-method)."""

import pandera.polars as pa
import polars as pl
from pandera.typing.polars import DataFrame


class InputSchema(pa.DataFrameModel):
    id: int
    value: pl.Float64


class OutputSchema(pa.DataFrameModel):
    id: int
    value: pl.Float64
    doubled: pl.Float64


def process(df: DataFrame[InputSchema]) -> DataFrame[OutputSchema]:
    return df.with_columns((pl.col("amount") * 2.0).alias("doubled"))


def smooth(df: DataFrame[InputSchema]):
    return df.interpolate()
