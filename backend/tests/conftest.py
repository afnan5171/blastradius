import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db import Base, get_db
from app.main import app
@pytest.fixture
def client():
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory=sessionmaker(bind=engine)
    def override():
        with factory() as db: yield db
    app.dependency_overrides[get_db]=override
    with TestClient(app) as c:
        c.post("/auth/demo")
        yield c
    app.dependency_overrides.clear()
    engine.dispose()
