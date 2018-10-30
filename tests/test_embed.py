from umongo import Document, fields, EmbeddedDocument


class NormalizerTempl(EmbeddedDocument):
    scale = fields.IntegerField(required=True)
    shift = fields.IntegerField(required=True)


class ModelTempl(Document):
    hypers = fields.DictField(required=True)
    normalization = fields.EmbeddedField(NormalizerTempl)


def test_store_retrieve(instance):
    Normalizer = instance.register(NormalizerTempl)
    Model = instance.register(ModelTempl)
    m = Model(
        hypers={
            'variance': 0.2,
            'mean': 1.2
        },
        normalization = Normalizer(scale=1, shift=2)
    )
    m.commit()
    found = Model.get(m.pk)
    assert found == m