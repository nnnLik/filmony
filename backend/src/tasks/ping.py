from celery import Celery


def register_tasks(app: Celery) -> None:
    @app.task(name='tasks.ping')
    def ping() -> str:
        """Smoke task to verify broker + worker wiring."""
        return 'pong'
