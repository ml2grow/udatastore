from umongo import Document, fields, validate
from datetime import datetime
import time


class UserTempl(Document):
    email = fields.EmailField(required=True, unique=True)
    birthday = fields.DateTimeField(validate=validate.Range(min=datetime(1900, 1, 1)))
    friend = fields.ListField(fields.ReferenceField("UserTempl"))


def test_create_commit_find(instance):
    User = instance.register(UserTempl)
    goku = User(email='goku@sayen.com', birthday=datetime(1984, 11, 20))
    goku.commit()

    found = list(goku.find({}))
    assert len(found) == 1
    assert found[0].birthday.replace(tzinfo=None) == goku.birthday
    assert found[0].email == goku.email

    found = User.find_one({'birthday': goku.birthday})
    assert found.birthday.replace(tzinfo=None) == goku.birthday
    assert found.email == goku.email

    data = list(instance.db.client.query(kind='UserTempl').fetch())
    assert len(data) == 1
    data[0].key.id_or_name == found.pk


def test_fetch_reference(instance):
    User = instance.register(UserTempl)
    goku = User(email='goku@sayen.com', birthday=datetime(1984, 11, 20))
    goku.commit()
    vegeta = User(email='vegeta@over9000.com', friend=[goku])
    vegeta.commit()

    found = User.get(vegeta.pk)
    assert found == vegeta
    retrieved = found.friend[0].fetch()
    assert retrieved == goku
