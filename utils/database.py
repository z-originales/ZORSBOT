from prisma import Prisma
from loguru import logger as log

class Database:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_client'):
            self._client = Prisma()

    def connect(self) -> None:
        log.info("Connecting to the database...")
        self._client.connect()

    def disconnect(self) -> None:
        log.info("Disconnecting from the database...")
        if self._client is not None:
            self._client.disconnect()

    @property
    def client(self):
        return self._client


