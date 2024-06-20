from typing import Dict, List
from pydantic import BaseModel, Field, RootModel


class Values(RootModel):
    root: Dict[str, float] = Field(
        ...,
        description="A set of key-value pairs where the key is the metric name and the value is the numerical data",
    )


class DataPoint(BaseModel):
    name: str = Field(..., description="The label or name for the data point")
    values: Values


class BaseChartData(RootModel):
    root: List[DataPoint]


class BarChartData(BaseChartData):
    pass


class AreaChartData(BaseChartData):
    pass


class LineChartData(BaseChartData):
    pass


class RadarChartData(BaseChartData):
    pass


class PieChartData(BaseChartData):
    pass
