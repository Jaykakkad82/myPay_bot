# agent_multi/runtime/dynamo.py
import boto3
from .config import AWS_REGION, DDB_TABLE, DDB_ENDPOINT

# _ddb = None
# _tbl = None

# def table():
#     global _ddb, _tbl
#     if _tbl is None:
#         _ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
#         _tbl = _ddb.Table(DDB_TABLE)
#     return _tbl

def _ddb_table():
    kwargs = {"region_name": AWS_REGION}
    if DDB_ENDPOINT:
        kwargs.update({
            "endpoint_url": DDB_ENDPOINT,
            "aws_access_key_id": "local",
            "aws_secret_access_key": "local",
        })
        # kwargs["endpoint_url"] = DDB_ENDPOINT
    # resource gives nice Table() interface
    ddb = boto3.resource("dynamodb", **kwargs)
    return ddb.Table(DDB_TABLE)
