from google.cloud import datastore
from umongo import Document, fields, validate
from ml2grow.framework.ugrow import DataStoreInstance
from datetime import datetime
import pytest
import time


instance = DataStoreInstance()


@instance.register
class User(Document):
    email = fields.EmailField(required=True, unique=True)
    birthday = fields.DateTimeField(validate=validate.Range(min=datetime(1900, 1, 1)))
    friends = fields.ReferenceField("User")


@pytest.fixture
def client():
    cl = datastore.Client(project='ml2grow-intern', namespace='abcd')
    for kind in ["user"]:
        for e in cl.query(kind=kind).fetch():
            cl.delete(e.key)
    instance.init(cl)
    yield cl


def test_create_commit_find(client):
    goku = User(email='goku@sayen.com', birthday=datetime(1984, 11, 20))
    goku.commit()
    time.sleep(0.5)
    found = list(goku.find({}))
    assert len(found) == 1
    assert found[0].birthday.replace(tzinfo=None) == goku.birthday
    assert found[0].email == goku.email

    found = goku.find_one({})
    assert found.birthday.replace(tzinfo=None) == goku.birthday
    assert found.email == goku.email

    data = list(client.query(kind='user').fetch())
    print(type(data))
    assert len(data) == 1
    data[0].key.id_or_name == found.pk
