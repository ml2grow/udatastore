import umongo
from .instance import DataStoreInstance, DataStoreBuilder

umongo.frameworks.register_builder(DataStoreBuilder)