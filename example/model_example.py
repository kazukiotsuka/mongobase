#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# model_example.py
# mongobasej

import datetime
from bson.objectid import ObjectId
from mongobase.mongobase import ModelBase


class Animal(ModelBase):
    __collection__ = 'users' # set collection name
    __database__ = 'mydatabase' # set db name 
    keeper = {
        '_id': ObjectId,
        'name': unicode
    }
    __structure__ = {
        '_id': ObjectId,
        'name': unicode,
        'foods': list,
        'age': int,
        'main_keeper': dict, # keeper
        'sub_keepers': list, # [keeper]
        'is_mammal': bool,
        'is_vertebrate': bool,
        'created': datetime.datetime,
        'updated': datetime.datetime
    }
    __required_fields__ = ['name', 'main_keeper', 'created']
    __default_values__ = {
        'age': 0
        'created': datetime.datetime.utcnow(),
        'updated': datetime.datetime.utcnow()
    }
    __indexed_key__ = 'name' # search gram key

    def keeper_names(self):
        names = []
        names.append(self.main_keeper.name)
        for keeper in self.sub_keepers:
            names.append(keeper.name)
        return names

    def save(self, should_return_if_exists=False):
        return self.insertIfNotExistsWithKeys(
            should_return_if_exists, 'name')

    def update(self):
        self.updateWithCorrespondentKey('_id')

    def __repr__(self):
        return u'<Animal {}>'.format(self.name)
