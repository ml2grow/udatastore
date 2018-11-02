import inspect

from .helpers import DataStoreClientWrapper
from .document import DataStoreDocument
from .reference import DataStoreReference
from .fields import ReferenceField

from umongo import fields
from umongo.frameworks.pymongo import _list_io_validate, _embedded_document_io_validate
from umongo.builder import BaseBuilder, _collect_indexes, on_need_add_id_field, data_proxy_factory, add_child_field, Schema, _collect_schema_attrs, DocumentTemplate
from umongo.builder import _build_document_opts as _build_document_opts_orig
from umongo.fields import ListField, EmbeddedField
from umongo.document import DocumentImplementation, DocumentOpts


_supported_field_types = [
    fields.BooleanField,
    fields.DateTimeField,
    fields.ReferenceField,
    fields.StringField,
    fields.NumberField,
    fields.IntegerField,
    fields.UrlField,
    fields.EmailField,
    fields.EmbeddedField,
    fields.ListField,
    fields.DictField,
    ReferenceField
]


def _build_document_opts(instance, template, name, nmspc, bases):
    opts = _build_document_opts_orig(instance, template, name, nmspc, bases)
    components = opts.__dict__
    # Override camel_to_snake
    components['collection_name'] = name
    return DocumentOpts(**components)


class DataStoreBuilder(BaseBuilder):

    BASE_DOCUMENT_CLS = DataStoreDocument

    @staticmethod
    def is_compatible_with(db):
        return isinstance(db, DataStoreClientWrapper)

    def _patch_field(self, field):
        super()._patch_field(field)

        validators = field.io_validate
        if not validators:
            field.io_validate = []
        else:
            if hasattr(validators, '__iter__'):
                validators = list(validators)
            else:
                validators = [validators]
            field.io_validate = validators
        if isinstance(field, ListField):
            field.io_validate_recursive = _list_io_validate
        if isinstance(field, fields.ReferenceField):
            # due to eventual consistency, this check is to prone to failure.
            #field.io_validate.append(_reference_io_validate)
            field.reference_cls = DataStoreReference
        if isinstance(field, EmbeddedField):
            field.io_validate_recursive = _embedded_document_io_validate

    @classmethod
    def _convert_field(cls, field, find_cls, replace_cls):
        if isinstance(field, find_cls):
            field = replace_cls(**field.__dict__)
        if isinstance(field, ListField):
            field.container = cls._convert_field(field.container, find_cls, replace_cls)
        return field

    @classmethod
    def _check_field(cls, field):
        if field.__class__ not in _supported_field_types:
            raise Exception("Field type {0} is currently unsupported for datastore".format(field.__class__.__name__))
        if isinstance(field, ListField):
            field.container = cls._check_field(field.container)
        return field

    @classmethod
    def _apply_to_schema(cls, schema_fields, callable):
        fields = {}
        for name, field in schema_fields.items():
            fields[name] = callable(field)
        return fields

    def build_document_from_template(self, template):
        """
        Lots of copy paste, only to sneak in _apply_to_schema which converts ReferenceFields to our
        ReferenceFields, and checks valid fields are used.
        """
        assert issubclass(template, DocumentTemplate)
        name = template.__name__
        bases = self._convert_bases(template.__bases__)
        opts = _build_document_opts(self.instance, template, name, template.__dict__, bases)
        nmspc, schema_fields, schema_non_fields = _collect_schema_attrs(template.__dict__)
        schema_fields = self._apply_to_schema(schema_fields, lambda f: self._check_field(f))
        schema_fields = self._apply_to_schema(schema_fields, lambda f: self._convert_field(f, fields.ReferenceField, ReferenceField))
        nmspc['opts'] = opts

        # Create schema by retrieving inherited schema classes
        schema_bases = tuple([base.Schema for base in bases
                              if hasattr(base, 'Schema')])
        if not schema_bases:
            schema_bases = (Schema, )
        on_need_add_id_field(schema_bases, schema_fields)
        # If Document is a child, _cls field must be added to the schema
        if opts.is_child:
            add_child_field(name, schema_fields)
        schema_cls = self._build_schema(template, schema_bases, schema_fields, schema_non_fields)
        nmspc['Schema'] = schema_cls
        schema = schema_cls()
        nmspc['schema'] = schema
        nmspc['DataProxy'] = data_proxy_factory(name, schema, strict=opts.strict)

        # _build_document_opts cannot determine the indexes given we need to
        # visit the document's fields which weren't defined at this time
        opts.indexes = _collect_indexes(nmspc.get('Meta'), schema.fields, bases)

        implementation = type(name, bases, nmspc)
        self._templates_lookup[template] = implementation
        # Notify the parent & grand parents of the newborn !
        for base in bases:
            for parent in inspect.getmro(base):
                if (not issubclass(parent, DocumentImplementation) or
                        parent is DocumentImplementation):
                    continue
                parent.opts.offspring.add(implementation)
        return implementation