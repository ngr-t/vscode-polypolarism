"""Sample exercising a typed return-column mismatch (PLY040): the schema
declares ``total: int`` but ``sum()`` over a Float64 column infers Float64,
so polypolarism reports a precise inferred-side span plus a ``declared here``
related location."""

import pandera.polars as pa
import polars as pl
from pandera.typing.polars import DataFrame


class Values(pa.DataFrameModel):
    value: pl.Float64


class Total(pa.DataFrameModel):
    total: int


def total_value(df: DataFrame[Values]) -> DataFrame[Total]:
    return df.select(total=pl.col("value").sum())
