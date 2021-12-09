from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class Result(BaseModel):
    success: Optional[bool]
    data: Optional[Any]
    message: Optional[str]
    code: Optional[int]

    class Config:
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None}

    @staticmethod
    def build_success(data=None, message=None, code=None):
        return Result(success=True, data=data, message=message, code=code)

    @staticmethod
    def build_failure(message=None, code=None):
        return Result(success=False, message=message, code=code)


class TaskExecuteParam(BaseModel):
    code: int
    config: Optional[dict]
