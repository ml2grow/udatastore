from umongo.instance import LazyLoaderInstance
from .builder import DataStoreBuilder
from .helpers import DataStoreClientWrapper


class DataStoreInstance(LazyLoaderInstance):

    def __init__(self, *args, **kwargs):
        self.BUILDER_CLS = DataStoreBuilder
        super().__init__(*args, **kwargs)

    def init(self, db):
        super(DataStoreInstance, self).init(DataStoreClientWrapper(db))