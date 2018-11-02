from google.cloud import datastore
import pytest
from udatastore import DataStoreInstance


@pytest.fixture
def client():
    cl = datastore.Client(project='ml2grow-intern', namespace='abcd')
    for kind in ["UserTempl", "ModelTempl", "User", "IncorrectTempl"]:
        for e in cl.query(kind=kind).fetch():
            cl.delete(e.key)
    yield cl


@pytest.fixture
def instance(client):
    inst = DataStoreInstance()
    inst.init(client)
    yield inst