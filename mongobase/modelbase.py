#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# modelbase.py
# mongobase

import datetime
from importlib import import_module
from uuid import uuid4
from mongobase_config import MONOGO_DB_HOST, MONGO_DB_PORT, MONGO_DB_NAME
from logger import logger
from exceptions import RequiredKeyIsNotSatisfied
from pymongo import TEXT

client = MongoClient(MONOG_DB_HOST, MONGO_DB_PORT)
db = client[MONGO_DB_NAME]

class ModelBase(dict):
    __collection__ = ''
    __database__ = ''
    __structure__ = {}
    __required_fields__ = {}
    __default_values__ = {}
    __validators__ = {}

    # attributed dictionary extension
    # obj['foo'] <-> obj.foo
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def __init__(self, init_dict):
        # set properties written in __structure__
        for key in self.__structure__:
            default_val = self.__default_values__[key]\
                if key in self.__default_values__ else None
            if key in init_dict:
                default_val = init_dict[key]
            setattr(self, key, default_val)

    def getattr(self, key):
        return getattr(self, key)

    def setattr(self, key, value):
        return setattr(self, key, value)

    def purify(self):
        # return the dictionary extracted
        # only properties written in the structure
        extracted = {}
        for key in self.__structure__:
            extracted[key] = self[key]
        return extracted

    def validate(self, target=None):
        if target is None:
            target = self
        # validate values according to rules in the __validators__
        for name in self.__validators__:
            logger(u'VALIDATE {}'.format(name))
            assert self.__validators__[name](target[name])
        # validate values according to types written in the __structure__
        for key in self.__structure__:
            if not (isinstance(target[key], self.__structure__[key])
                    or target[key] is None):
                if not key == '_id':
                    raise TypeError(
                        'the key {} must be the type of {} but {}'
                        .format(
                            key, self.__structure__[key], type(target[key])))

    def checkRequiredFields(self):
        for key in self.__required_fields__:
            if not getattr(self, key):
                raise RequiredKeyIsNotSatisfied(
                    'the key [{}] must not be None'.format(key)
                    )
                return False
        return True

    @classmethod
    def generateInstances(cls, documents):
        for obj in documents:
            yield cls(obj)

    @staticmethod
    def generateSearchGram(origin_text):
        # 'Some text value'
        # -> 'Some text value
        #     So om me et te xt tv va al lu ue'
        search_gram = ''
        search_gram += origin_text
        # search_gram: 'Some text value'
        origin_text_without_space = origin_text.replace(' ', '')
        for i in xrange(3, len(origin_text_without_space)+1):
            search_gram += ' '
            search_gram += origin_text_without_space[0:i]
        # search_gram: 'Some text value Som Some Somet Somete Sometex Sometext
        #               Sometextv Sometextva Sometextval Sometextvalu
        #               Sometextvalue'
        for i in xrange(0, len(origin_text_without_space)-1):
            search_gram += ' '
            search_gram += origin_text_without_space[i:i+2]
        # search_gram: 'Some text value
        #               So om me et te ex xt tv va al lu ue'
        return search_gram

    def insert(self, inserts, uuid):
        # db.collection.insert(inserts)
        #
        # set search_text
        if self.__indexed_key__:
            origin_text = self[self.__indexed_key__]
            inserts.update(
                {'search_text': self.generateSearchGram(origin_text)})
        # validate
        self.validate(inserts)
        # insert
        if db[self.__collection__].insert(inserts):
            # create search index after inserted
            if self.__indexed_key__:
                db[self.__collection__].create_index(
                    [('search_text', TEXT)], default_language='english')
            self._id = uuid
            logger(u'NEW {} CREATED'.format(self))
            return uuid
        else:
            return None

    def insertIfNotExistsWithKeys(self, should_return_if_exists=False, *args):
        # insert if not exists
        #
        # [when inserted]
        # return self if inserted
        #
        # [when not inserted]
        # return None (should_return is False)
        # return stored element with the same key (should_return is True)
        query = {key: getattr(self, key) for key in args}
        return self.insertIfNotExistsWithQueryDict(
            query, should_return_if_exists)

    def insertIfNotExistsWithQueryDict(
            self, query, should_return_if_exists=False):
        exist = db[self.__collection__].find_one(query)
        if bool(query) and exist:
            logger('ALREADY EXISTS, NOT SAVE')
            if should_return_if_exists:
                class_name = '{}{}'.format(
                    self.__collection__[0].upper(), self.__collection__[1:-1])
                module_name = 'models.{}'.format(self.__collection__[0:-1])
                Class = getattr(import_module(module_name), class_name)
                return Class(exist)
            return None
        else:
            assert self.checkRequiredFields(), 'Reqired Key Error'
            inserts = self.purify()
            if '_id' in inserts and inserts['_id'] is not None:
                uuid = self._id
            else:
                uuid = unicode('{}-{}'.format(self.__collection__, uuid4()))
            inserts['_id'] = uuid
            logger(inserts)
            self.insert(inserts, uuid)
            return self

    def updateWithCorrespondentKey(self, find_key):
        # update self instance
        if hasattr(self, find_key) and getattr(self, find_key):
            # updates as full document dictionary
            updates = self.purify()
            updates['updated'] = datetime.datetime.utcnow()
            # update search_text
            if self.__indexed_key__:
                updates['search_text'] =\
                    self.generateSearchGram(updates[self.__indexed_key__])
            # validate
            self.validate(updates)
            return ModelBase.findAndModifyWithUpdateDict(
                self, find_key, getattr(self, find_key), updates)
        return None

    @classmethod
    def findAndUpdateById(cls, _id, updates):
        # update from class by _id
        logger(u'FIND AND UPDATE {} WITH {}'.format(_id, updates))
        # updates must be like {'$set': {'key': val,...}}
        # otherwise, the rest of fields will be removed
        if '$set' in updates:
            updates['$set'].update({'updated': datetime.datetime.utcnow()})
        else:
            updates['$set'] = {'updated': datetime.datetime.utcnow()}
        # update search_text if the related field changed
        if cls.__indexed_key__ is not None\
                and cls.__indexed_key__ in updates['$set']:
            updates['$set']['search_text'] =\
                cls.generateSearchGram(updates['$set'][cls.__indexed_key__])
        # validate
        check_instance = ModelBase(updates)
        check_instance.validate()
        return ModelBase.findAndModifyWithUpdateDict(cls, '_id', _id, updates)

    @staticmethod
    def findAndModifyWithUpdateDict(
            cls_or_instance, find_key, find_val, updates):
        '''
        pymongo 3.0
        return db[self.__collection__].find_one_and_update(
            {find_key: getattr(self, find_key)}, updates)
        '''
        # validate
        check_instance = ModelBase(updates)
        check_instance.validate()
        return db[cls_or_instance.__collection__].find_and_modify(
            {find_key: find_val}, updates, upsert=False)

    @classmethod
    def find(cls, query, limit=None, skip=None, sort=None):
        # return the list of ModelBase objects if found or
        # return None if not found

        # limit & skip & sort
        if limit and skip and sort:
            results = db[cls.__collection__]\
                .find(query).sort(sort).skip(skip).limit(limit)

        # limit & skip
        elif limit and skip and not sort:
            results = db[cls.__collection__]\
                .find(query).skip(skip).limit(limit)
        # limit & sort
        elif limit and not skip and sort:
            results = db[cls.__collection__]\
                .find(query).sort(sort).limit(limit)
        # skip & sort
        elif not limit and skip and sort:
            results = db[cls.__collection__]\
                .find(query).sort(sort).skip(skip)

        # limit
        elif limit and not skip and not sort:
            results = db[cls.__collection__].find(query).limit(limit)
        # skip
        elif not limit and skip and not sort:
            results = db[cls.__collection__].find(query).skip(skip)
        # sort
        elif not limit and not skip and sort:
            results = db[cls.__collection__].find(query).sort(sort)

        # (just find)
        else:
            results = db[cls.__collection__].find(query)

        return list(cls.generateInstances(results))

    @classmethod
    def findOne(cls, query):
        # return ModelBase object if found or
        # return None if not found
        result = db[cls.__collection__].find_one(query)
        if result:
            return cls(result)
        else:
            return None

    @classmethod
    def findAll(cls):
        # return the list of ModelBase objects if found or
        # return None if not found
        results = db[cls.__collection__].find()
        return list(cls.generateInstances(results))

    @classmethod
    def textSearch(cls, text, limit, skip):
        # return ...
        cursor = db[cls.__collection__].find(
            {'$text': {'$search': text}},
            {'score': {'$meta': 'textScore'}}).skip(skip).limit(limit)
        cursorResults = cursor.sort([('score', {'$meta': 'textScore'})])
        return list(cls.generateInstances(cursorResults))

    @classmethod
    def count(cls):
        # return the number of sub class documents
        return db[cls.__collection__].count()

    @classmethod
    def remove(cls, query):
        result = db[cls.__collection__].remove(query)
        logger(result)
        if 'ok' in result:
            return True if result['ok'] else None
        else:
            return False

