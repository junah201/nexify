from datetime import datetime
from typing import Annotated

from nexify import Nexify, Query

app = Nexify()


def default_date():
    return datetime.now().isoformat()


@app.get("/logs")
def get_logs(
    start_date: Annotated[str, Query(default_factory=default_date)],
    end_date: Annotated[str, Query(default_factory=default_date)],
):
    return {"start_date": start_date, "end_date": end_date}
