# -*- coding: utf-8 -*-

from sqlalchemy import Column, INTEGER
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import reconstructor


class IdMixin(object):

    @declared_attr
    def id(cls):
        column = Column(INTEGER, primary_key=True)
        column._creation_order = 0
        return column


@as_declarative()
class Model(object):

    __table_name_mask__ = '{__source__}_{__table_type__}_{__table_name__}'

    @reconstructor
    def init_on_load(cls):
        assert hasattr(cls, '__schema__')
        assert hasattr(cls, '__table_name_mask__')
        for p in Model.table_name_properties(cls.__table_name_mask__):
            assert hasattr(cls, p)

    @declared_attr
    def __table_args__(cls):
        return {'schema': cls.__schema__}

    @declared_attr
    def __tablename__(cls):

        if not hasattr(cls, '__table_name__'):
            cls.__table_name__ = cls.__name__

        return cls.__table_name_mask__.format(**dict((p, getattr(cls, p)) for p in Model.table_name_properties(cls.__table_name_mask__)))

    def update_subset(self, d, subset):
        if isinstance(subset, dict):
            return self(**{subset[k]: d[k] for k in set(subset).intersection(d)})
        else:
            return self(**{k: d[k] for k in set(subset).intersection(d)})

    @classmethod
    def from_dict(cls, d, subset=None):
        if subset is None:
            return cls(**d)
        elif isinstance(subset, dict):
            return cls(**{subset[k]: d[k] for k in set(subset).intersection(d)})
        else:
            return cls(**{k: d[k] for k in set(subset).intersection(d)})

    @staticmethod
    def table_name_properties(table_name_mask):
        return [t.strip('{').strip('}') for t in table_name_mask.split('}_{')]

    # def __repr__(self):
    #     # TODO - necessary?
    #     class_properties = []
    #     for k, v in sorted(self.__dict__.iteritems()):
    #         if not k.startswith('_'):
    #             if isinstance(v, str):
    #                 v = '\'' + v + '\''
    #             class_properties.append(k + '=' + v)
    #     return str(self.__class__.__name__) + '(' + ', '.join(class_properties) + ')'
