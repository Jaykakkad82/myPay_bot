from datetime import datetime, timedelta, timezone
from decimal import Decimal
from runtime.dynamo import _ddb_table

def _ddb_health_ping():
    t = _ddb_table()
    now = int(datetime.now(tz=timezone.utc).timestamp())
    item = {
        "PK": "HEALTH#PING",
        "SK": f"TS#{now}",
        "ok": True,
        "expiresAt": now + 86400,  # 1 day
    }
    t.put_item(Item=item)
    # read back
    resp = t.get_item(Key={"PK": "HEALTH#PING", "SK": f"TS#{now}"})
    return bool(resp.get("Item"))


print(_ddb_health_ping())  # should print true
