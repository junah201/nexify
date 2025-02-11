from nexify import Nexify
from nexify.schedule import Rate


def test_schedule(app):
    app = Nexify()

    @app.schedule(Rate(5, unit=Rate.MINUTES))
    def handler(): ...

    assert str(app.scheduler.operations[0].expressions[0]) == "rate(5 minutes)"
