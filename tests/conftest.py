from google.cloud import datastore
import pytest
from ml2grow.framework.ugrow import DataStoreInstance


@pytest.fixture
def instance():
    cl = datastore.Client(project='ml2grow-intern', namespace='abcd')
    for kind in ["UserTempl", "ModelTempl"]:
        for e in cl.query(kind=kind).fetch():
            print(e)
            cl.delete(e.key)
    inst = DataStoreInstance()
    inst.init(cl)
    yield inst