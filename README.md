# μDatastore: ODM for Google Cloud Datastore
Implemented as framework in the [μMongo](https://github.com/Scille/umongo) library (a python ODM for MongoDB)

While working Google Cloud Datastore, most of our code uses the `google-cloud-datastore` package, 
for creating, updating and querying entities. We often find ourselves writing code to export objects
to `datastore.Entity`, and import from entities to objects. On AppEngine, there is `ndb` which avoids this,
so the idea emerged to create an ODM for datastore ourselves. 

Having worked with μMongo before, a prototype was created which implements an additional framework based on 
following conventions:
* A datastore partition (project/namespace) corresponds to a mongo database
* A datastore entity kind corresponds to a mongo collection
* The datastore `__key__` field corresponds to the mongo `_id` field

## Install

    pip install udatastore

## Example
```python
from datetime import datetime
from google.cloud import datastore
from udatastore import DataStoreInstance
from umongo import Document, fields, validate


db = datastore.Client(project="dummy", namespace='abcd')
instance = DataStoreInstance()
instance.init(db)


@instance.register
class User(Document):
    email = fields.EmailField(required=True, unique=True)
    birthday = fields.DateTimeField(validate=validate.Range(min=datetime(1900, 1, 1)))
    friends = fields.ListField(fields.ReferenceField("User"))

goku = User(email='goku@sayen.com', birthday=datetime(1984, 11, 20))
goku.commit()
vegeta = User(email='vegeta@over9000.com', friends=[goku])
vegeta.commit()

vegeta.friends
# <object umongo.data_objects.List([<object udatastore.reference.DataStoreReference(document=User, pk=<Key('User', 4476), project=dummy>)>])>
vegeta.dump()
# {'email': 'vegeta@over9000.com', 'id': '4477', 'friends': [<Key('User', 4476), project=dummy>]}
User.find_one({"email": 'goku@sayen.com'})
# <object Document __main__.User({'email': 'goku@sayen.com', 'id': 4474,
#                                 'friends': <object umongo.data_objects.List([])>,
#                                 'birthday': datetime.datetime(1984, 11, 20, 0, 0)})>
```

## Limitations:
Not all features of μMongo are available or work exactly the same in μDatastore:
* No indexes
* We do not currently support all field types
* Datastore converts any `datetime` to UTC timezone. For now, μDatastore overrides this behaviour and always works with
unaware datetimes.
* We bring our own `ReferenceField` implementation. You are free to use `umongo.fields.ReferenceField`, as the `DataStoreBuilder` 
will automatically replace these fields with our implementation. We also disable the io_validation on reference fields.
Because datastore is eventually consistent this may report errors when creating references to previously created entities.

