"""Sample exercising an undeclared extra return column (PLY040 "Extra column"):
the function produces `extra` but the strict output schema does not declare it,
so polypolarism reports the inferred-side column plus its dtype. The QuickFix
declares the column on the strict schema."""

import pandera.polars as pa
import polars as pl
from pandera.typing.polars import DataFrame


class Source(pa.DataFrameModel):
    value: pl.Float64


class Result(pa.DataFrameModel):
    value: pl.Float64

    class Config:
        strict = True


def add_extra(df: DataFrame[Source]) -> DataFrame[Result]:
    return df.with_columns(extra=pl.col("value") * 2.0)
