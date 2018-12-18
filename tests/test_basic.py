from google.cloud import datastore
from umongo import Document, fields, validate
from umongo.fields import StringField

from udatastore.helpers import DataStoreClientWrapper
from udatastore.builder import DataStoreBuilder
from udatastore.fields import BytesField, DictField
from datetime import datetime
import pytest
import pickle


class UserTempl(Document):
    email = fields.EmailField(required=True, unique=True)
    birthday = fields.DateTimeField(validate=validate.Range(min=datetime(1900, 1, 1)))
    friend = fields.ReferenceField("UserTempl")


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
    assert isinstance(goku.pk, datastore.Key)

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
    vegeta = User(email='vegeta@over9000.com', friend=goku)
    vegeta.commit()

    found = User.get(vegeta.pk.id)
    assert found == vegeta
    retrieved = found.friend.fetch()
    assert retrieved == goku


def test_unsupposered_fields(instance):
    with pytest.raises(Exception):
        instance.register(IncorrectTempl)


def test_find_by_reference(instance):
    User = instance.register(UserTempl)
    goku = User(email='goku@sayen.com', birthday=datetime(1984, 11, 20))
    goku.commit()
    vegeta = User(email='vegeta@over9000.com', friend=goku)
    vegeta.commit()

    found = User.find_one({'friend': goku.pk})
    assert found.pk == vegeta.pk


class FaxTempl(Document):
    name = fields.StringField(required=True, attribute='_id')
    number = fields.StringField(required=True)


def test_attribute(instance):
    Fax = instance.register(FaxTempl)
    f = Fax(name="abcdef", number="034407777")
    f.commit()
    assert f.pk == Fax.collection.key("abcdef")
    found = Fax.find_one({'_id': f.pk})
    assert found.name == "abcdef"
    assert found.pk == f.pk
    assert found.dump() == {'name': 'abcdef', 'number': '034407777'}


class RecipeTempl(Document):
    mix = BytesField(required=True)
    order = fields.IntegerField(required=True)


def test_bytes_field(instance):
    Recipe = instance.register(RecipeTempl)
    t = datetime.now()
    r = Recipe(mix=t, order=2)
    assert r.mix == t
    r.commit()
    assert r.dump() == {'id': str(r.pk.id_or_name), 'mix': pickle.dumps(t), 'order': 2}
    assert r.to_mongo() == {'_id': r.pk, 'mix': pickle.dumps(t), 'order': 2}
    assert r._data._data['mix'] == t

    found = Recipe.get(r.pk.id_or_name)
    assert found.mix == t

    found = Recipe.find_one()
    assert found.mix == t

class PokemonTempl(Document):
    name = StringField(required=True)
    attributes = DictField(required=True)


def test_dict_field(instance):
    Pokemon = instance.register(PokemonTempl)
    attr_dict = {"type": "grass", "H.P.": "104"}
    venusaur = Pokemon(name="Venusaur", attributes=attr_dict)
    venusaur.commit()

    found = Pokemon.find_one({'_id': venusaur.pk})

    assert attr_dict == found.attributes
