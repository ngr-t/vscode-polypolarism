"""Sample for the PLY042 "declare the column" QuickFix: `flag` is undeclared on
`Src`, but `.cast(pl.Boolean)` pins its dtype statically, so polypolarism emits
`fix.suggested_dtype` and the editor can declare `flag: pl.Boolean`."""

import pandera.polars as pa
import polars as pl
from pandera.typing.polars import DataFrame


class Src(pa.DataFrameModel):
    keep: pl.Int64


def f(df: DataFrame[Src]) -> DataFrame[Src]:
    return df.filter(pl.col("flag").cast(pl.Boolean))
