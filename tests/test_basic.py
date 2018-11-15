from umongo import Document, fields, validate
from udatastore.helpers import DataStoreClientWrapper
from udatastore.builder import DataStoreBuilder
from datetime import datetime
import pytest


class UserTempl(Document):
    email = fields.EmailField(required=True, unique=True)
    birthday = fields.DateTimeField(validate=validate.Range(min=datetime(1900, 1, 1)))
    friend = fields.ListField(fields.ReferenceField("UserTempl"))


class IncorrectTempl(Document):
    birthday = fields.UUIDField(required=True)


def test_instance(instance, client):
    assert isinstance(instance.db, DataStoreClientWrapper)
    assert instance.db.client == client
    assert instance.BUILDER_CLS == DataStoreBuilder


def test_create_commit_find(instance):
    User = instance.register(UserTempl)
    goku = User(email='goku@sayen.com', birthday=datetime(1984, 11, 20))
    goku.commit()

    found = list(goku.find({}))
    assert len(found) == 1
    assert found[0].birthday.replace(tzinfo=None) == goku.birthday
    assert found[0].email == goku.email

    found = User.find_one({'birthday': goku.birthday})
    assert found.birthday == goku.birthday
    assert found.email == goku.email

    data = list(instance.db.client.query(kind='UserTempl').fetch())
    assert len(data) == 1
    data[0].key.id_or_name == found.pk


def test_find_one_not_exist(instance):
    User = instance.register(UserTempl)
    assert User.find_one() is None


def test_fetch_reference(instance):
    User = instance.register(UserTempl)
    goku = User(email='goku@sayen.com', birthday=datetime(1984, 11, 20))
    goku.commit()
    vegeta = User(email='vegeta@over9000.com', friend=[goku])
    vegeta.commit()

    found = User.get(vegeta.pk.id)
    assert found == vegeta
    retrieved = found.friend[0].fetch()
    assert retrieved == goku


def test_unsupposered_fields(instance):
    with pytest.raises(Exception):
        instance.register(IncorrectTempl)


