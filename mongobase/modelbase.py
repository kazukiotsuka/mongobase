#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# tools/modelbase.py
#
#
# MODEL DEFINITION:
# 1. create a subclass.
# 2. set each definitions as below in the subclass.
#
#    __structure__ = {}  # define keys and the data type
#    __required_fields__ = []  # lists required keys
#    __default_values__ = {}  # set default values to some keys
#    __validators__ = {}  # set pairs like key: validatefunc()
#
# BASIC USAGE EXAMPLE:
#
# animal_name = 'wild boar'
# cat = Animal({
#     'name': 'cat',
#     'num_of_legs': 4
#     })
#
# cat.validate()  # check types in __structure__ and run __validators__
# cat.purify()  # convert to dict
# cat.serialize()  # convert to json compatible dict
# cat._is_required_fields_satisfied()  # raise RequiredKeyIsNotSatisfied if not enough

import logging
import datetime
import sys
from .exceptions import RequiredKeyIsNotSatisfied


class ModelBase(dict):
    # __collection__ = ''  # set the collection name
    __structure__ = {}  # define keys and the data type
    __required_fields__ = []  # lists required keys
    __default_values__ = {}  # set default values to some keys
    __validators__ = {}  # set pairs like key: validatefunc()
    # __search_text_keys__ = []  # set index keys for text search

    # attributed dictionary extension
    # obj['foo'] <-> obj.foo
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def __init__(self, init_dict):
        # set properties written in __structure__
        for key in self.__structure__:
            if key in init_dict and init_dict[key] is not None:
                # when an initial value is given and it's not None
                default_val = init_dict[key]
            elif key in self.__default_values__:
                # when an initial value is given for some keys
                default_val = self.__default_values__[key]
            else:
                default_val = None
            setattr(self, key, default_val)

    def getattr(self, key):
        return getattr(self, key)

    def setattr(self, key, value):
        return setattr(self, key, value)

    def purify(self):
        """Return an instance as dictionary format.

        returns:
            object (dict): object only with keys in  __structure__.
        """
        extracted = {}
        for key in self.__structure__:
            extracted[key] = self[key]
        if 'search_text' in self:
            extracted['search_text'] = self['search_text']
        # if self.__search_text_keys__:
        #     extracted.update({'search_text': self['search_text']})
        return extracted

    def serialize(self):
        """Return the json formatted dict.

        1. datetime.datetime -> YYYY/mm/dd/HH/MM/SS

        returns:
            object (dict): pure json format dict
        """
        extracted = {}
        for key in self.__structure__:
            extracted[key] = datetime.datetime.strftime(self[key], '%Y/%m/%d/%H/%M/%S')\
                if isinstance(self[key], datetime.datetime) else self[key]
        return extracted

    def validate(self, target=None):
        """Validate properties usually before inserted or updated.

        1. validate values according to rules written in the __validators__
        2. validate values according to types written in the __structure__

        returns:
            result (bool): True if no error occured.
        """
        if target is None:
            target = self
        # validate values according to rules in the __validators__
        for name in self.__validators__:
            logging.info(u'VALIDATE {}'.format(name))
            assert self.__validators__[name](target[name])
        # validate values according to types written in the __structure__
        for key in self.__structure__:
            if not (isinstance(target[key], self.__structure__[key])
                    or target[key] is None):
                if not key == '_id':
                    raise TypeError(
                        'the key \'{}\' must be of type {} but {}'
                        .format(
                            key, self.__structure__[key], type(target[key])))
        return True

    def _is_required_fields_satisfied(self):
        """Check if required fields are filled.

        Required fields are defined as __required_fields__.
        `RequiredKeyIsNotSatisfied` exception is raised if not enough.

        returns:
            satisfied (bool): True if all fields have a value.
        """
        for key in self.__required_fields__:
            if getattr(self, key) is None:
                raise RequiredKeyIsNotSatisfied(
                    'the key \'{}\' must not be None'.format(key)
                    )
                return False
        return True

    @classmethod
    def generateInstances(cls, documents):
        """Return this instances converted from dicts in documents.

        Convert dict objects to this instance and return them.
        """
        for obj in documents:
            yield cls(obj)