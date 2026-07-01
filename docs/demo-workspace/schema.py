import pandera.polars as pa
import polars as pl


class Sales(pa.DataFrameModel):
    amount: pl.Float64
    region: str
