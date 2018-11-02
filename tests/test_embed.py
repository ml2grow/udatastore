from umongo import Document, fields, EmbeddedDocument


class NormalizerTempl(EmbeddedDocument):
    scale = fields.IntegerField(required=True)
    shift = fields.IntegerField(required=True)

    class Meta:
        abstract = True


class NormalizerExtTempl(NormalizerTempl):
    editable = fields.BooleanField(required=True)


class ModelTempl(Document):
    hypers = fields.DictField(required=True)
    normalization = fields.EmbeddedField(NormalizerTempl)


def test_store_retrieve(instance):
    Normalizer = instance.register(NormalizerTempl)
    NormalizerExt = instance.register(NormalizerExtTempl)
    Model = instance.register(ModelTempl)
    m = Model(
        hypers={
            'variance': 0.2,
            'mean': 1.2
        },
        normalization=NormalizerExt(scale=1, shift=2, editable=True)
    )
    m.commit()
    found = Model.get(m.pk)
    assert found == m

    found = list(Model.find({'normalization.scale': 1, 'hypers.variance': 0.2}))
    assert found[0] == m
    assert isinstance(found[0].normalization, Normalizer)
    assert isinstance(found[0].normalization, NormalizerExt)