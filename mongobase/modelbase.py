#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# modelbase.py
# mongobase
#
# SETTINGS:
#   At first, set up MONGO_DB_HOST, MONGO_DB_PORT, MONGO_DB_NAME
#   in mongobase_config.py.
#
# MODEL DEFINITION:
# 1. create a subclass.
# 2. set each definitions as below in the subclass.
#
#    __collection__ = ''  # set the collection name
#    __database__ = ''  # set the name of db restoring this instance
#    __structure__ = {}  # define keys and the data type
#    __required_fields__ = []  # lists required keys
#    __default_values__ = {}  # set default values to some keys
#    __validators__ = {}  # set pairs like key: validatefunc()
#    __indexed_key__ = ''  # set the index key for text search
#
#
# 3. define insert/update methods in the subclass.
#    as an example,
#
#    def save(self, should_return_if_exists=False):
#        return self.insertIfNotExistsWithKeys(
#            should_return_if_exists, 'email')
#
#    def update(self):
#        return self.updateWithCorrespondentKey('_id')
#
#
# API:
# 1. insert methods
#   - insertIfNotExistsWithKeys(
#       should_return_if_exists=False, *args) [Instance method]
#   - insertIfNotExistsWithQueryDict(
#       self, query, should_return_if_exists=False) [Instance method]
#
# 2. update methods
#   - updateWithCorrespondentKey(self, find_key) [Instance method]
#   - findAndUpdateById(cls, _id, updates) [Class method]
#
# 3. find methods
#   - find(cls, query, limit=None, skip=None, sort=None) [Class method]
#   - findOne(cls, query) [Class method]
#   - findAll(cls) [Class method]
#   - textSearch(cls, text, limit, skip) [Class method]
#
# 4. others
#   - count(cls) [Class method]
#   - remove(cls, query) [Class method]
#
#
# BASIC USAGE EXAMPLE:
#
# animal_name = 'wild boar'
# new_animal = Animal({
#     'name': animal_name,
#     'kind': 'cat'
#     })
# same_animal = Animal.findOne({'name': animal_name})
# if same_animal:
#     same_animal.count = same_animal.count + 1
#     return same_animal.update()
# else:
#     return new_animal.save()
#
#


import datetime
import logging
from importlib import import_module
from uuid import uuid4
from mongobase_config import MONGO_DB_HOST, MONGO_DB_PORT, MONGO_DB_NAME
from exceptions import RequiredKeyIsNotSatisfied
from pymongo import TEXT, MongoClient


class ModelBase(dict):
    __collection__ = ''  # set the collection name
    __database__ = ''  # set the name of db restoring this instance
    __structure__ = {}  # define keys and the data type
    __required_fields__ = []  # lists required keys
    __default_values__ = {}  # set default values to some keys
    __validators__ = {}  # set pairs like key: validatefunc()
    __indexed_key__ = ''  # set the index key for text search

    # attributed dictionary extension
    # obj['foo'] <-> obj.foo
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    __client = MongoClient(
        MONGO_DB_HOST, MONGO_DB_PORT)
    __db = __client[MONGO_DB_NAME]

    def __init__(self, init_dict):
        self.__client = MongoClient(
            MONGO_DB_HOST, MONGO_DB_PORT)
        self.__db = self.__client[MONGO_DB_NAME]

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
        """Return the instance as dictionary format.

        Return the dictionary
        only with properties written in the structure
        """
        extracted = {}
        for key in self.__structure__:
            extracted[key] = self[key]
        return extracted

    def __validate(self, target=None):
        """Validate the properties usually before insert/update it.

        1. validate values according to rules written in the __validators__
        2. validate values according to types written in the __structure__
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
                        'the key {} must be the type of {} but {}'
                        .format(
                            key, self.__structure__[key], type(target[key])))

    def __checkRequiredFields(self):
        """Check if required fields are filled before insert it.

        Required fields are defined in __required_fields__.
        """
        for key in self.__required_fields__:
            if not getattr(self, key):
                raise RequiredKeyIsNotSatisfied(
                    'the key [{}] must not be None'.format(key)
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

    @staticmethod
    def generateSearchGram(origin_text):
        """Generate Text search bi-gram.

        'Some text value'
        -> 'Some text value
            So om me et te xt tv va al lu ue'
        """
        search_gram = ''
        search_gram += origin_text
        # search_gram: 'Some text value'
        origin_text_without_space = origin_text.replace(' ', '')
        for i in range(3, len(origin_text_without_space)+1):
            search_gram += ' '
            search_gram += origin_text_without_space[0:i]
        # search_gram: 'Some text value Som Some Somet Somete Sometex Sometext
        #               Sometextv Sometextva Sometextval Sometextvalu
        #               Sometextvalue'
        for i in range(0, len(origin_text_without_space)-1):
            search_gram += ' '
            search_gram += origin_text_without_space[i:i+2]
        # search_gram: 'Some text value
        #               So om me et te ex xt tv va al lu ue'
        return search_gram

    def __insert(self, inserts, uuid):
        """The wrapper for db[collection_name].insert() in pymongo.

        Before and after calling insert() of pymongo, do things as below.

        1. set search text with generateSearchGram.
        2. validate instance properties with __validate().
        3. call pymongo insert() method.
        4. call pymongo create_index() method if __index_key__ has been set.

        The insert() method in pymongo executes
        db.collection.insert(inserts)
        method in mongo db.
        """
        # set search_text
        if self.__indexed_key__:
            origin_text = self[self.__indexed_key__]
            inserts.update(
                {'search_text': self.generateSearchGram(origin_text)})
        # validate
        self.__validate(inserts)
        # insert
        if self.__db[self.__collection__].insert(inserts):
            # create search index after inserted
            if self.__indexed_key__:
                self.__db[self.__collection__].create_index(
                    [('search_text', TEXT)], default_language='english')
            self._id = uuid
            logging.info(u'NEW {} CREATED'.format(self))
            return uuid
        else:
            return None

    def insertIfNotExistsWithKeys(self, should_return_if_exists=False, *args):
        """Insert this instance to db (If not already exists).

        Return value:
        A. If successfully inserted, it returns this instance itself.
        B1. If failed && sould_return is False, it returns None.
        B2. If failed && should_return is True,
        it returns the instance which already have the same key.

        The second argument should be the list of keys or a string key name.
        """
        query = {key: getattr(self, key) for key in args}
        return self.insertIfNotExistsWithQueryDict(
            query, should_return_if_exists)

    def insertIfNotExistsWithQueryDict(
            self, query, should_return_if_exists=False):
        """Insert this instance to db (avoid more specific deplications).


        The second argument 'query' should be the dictionary which is composed
        of the key value pairs.
        And only when no data with these key value pairs exists,
        the instance will be inserted.
        """
        exist = self.__db[self.__collection__].find_one(query)
        if bool(query) and exist:
            logging.info('ALREADY EXISTS, NOT SAVE')
            if should_return_if_exists:
                class_name = '{}{}'.format(
                    self.__collection__[0].upper(), self.__collection__[1:-1])
                module_name = 'models.{}'.format(self.__collection__[0:-1])
                Class = getattr(import_module(module_name), class_name)
                return Class(exist)
            return None
        else:
            assert self.__checkRequiredFields(), 'Reqired Key Error'
            inserts = self.purify()
            if '_id' in inserts and inserts['_id'] is not None:
                uuid = self._id
            else:
                uuid = str('{}-{}'.format(self.__collection__, uuid4()))
            inserts['_id'] = uuid
            logging.info(inserts)
            self.__insert(inserts, uuid)
            return self

    def updateWithCorrespondentKey(self, find_key):
        """Update a stored instance.(Instance method)

        Update a stored instance having the same value on the key
        appointed by find_key.
        The find_key:value pair is passed to pymongo find_and_update()
        method.

        Eventually, __findAndUpdate is called.
        """
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
            self.__validate(updates)
            return ModelBase.__findAndUpdate(
                self, find_key, getattr(self, find_key), updates)
        return None

    @classmethod
    def findAndUpdateById(cls, _id, updates):
        """Find and update.(Class method)

        1st argument is _id(ObjectId).
        2nd argument is dictionary consisted of key,value pairs to update.

        Eventually, __findAndUpdate is called.
        """
        # update from class by _id
        logging.info(u'FIND AND UPDATE {} WITH {}'.format(_id, updates))
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
        check_instance.__validate()
        return ModelBase.__findAndUpdate(cls, '_id', _id, updates)

    @staticmethod
    def __findAndUpdate(
            cls_or_instance, find_key, find_val, updates):
        """Find and update.(Static method)

        This is the wrapper method of find_one_and_update() in pymongo.
        """
        # validate
        check_instance = ModelBase(updates)
        check_instance.__validate()

        return cls_or_instance.__db[cls_or_instance.__collection__]\
            .find_one_and_update({find_key: find_val}, updates)

    @classmethod
    def find(cls, query, limit=None, skip=None, sort=None):
        """Find and return instances.

        Return value:
        A. list of ModelBase instances. (if found)
        B. None. (if not found)
        """
        # limit & skip & sort
        if limit and skip and sort:
            results = cls.__db[cls.__collection__]\
                .find(query).sort(sort).skip(skip).limit(limit)

        # limit & skip
        elif limit and skip and not sort:
            results = cls.__db[cls.__collection__]\
                .find(query).skip(skip).limit(limit)
        # limit & sort
        elif limit and not skip and sort:
            results = cls.__db[cls.__collection__]\
                .find(query).sort(sort).limit(limit)
        # skip & sort
        elif not limit and skip and sort:
            results = cls.__db[cls.__collection__]\
                .find(query).sort(sort).skip(skip)

        # limit
        elif limit and not skip and not sort:
            results = cls.__db[cls.__collection__].find(query).limit(limit)
        # skip
        elif not limit and skip and not sort:
            results = cls.__db[cls.__collection__].find(query).skip(skip)
        # sort
        elif not limit and not skip and sort:
            results = cls.__db[cls.__collection__].find(query).sort(sort)

        # (just find)
        else:
            results = cls.__db[cls.__collection__].find(query)

        return list(cls.generateInstances(results))

    @classmethod
    def findOne(cls, query):
        """Find one and return the instance.

        Return value:
        A. a ModelBase instance. (if found)
        B. None. (if not found)
        """
        client = MongoClient(
            MONGO_DB_HOST, MONGO_DB_PORT)
        db = client[MONGO_DB_NAME]

        result = db[cls.__collection__].find_one(query)
        if result:
            return cls(result)
        else:
            return None

    @classmethod
    def findAll(cls):
        """Find all and return all instances of the class.

        Return value:
        A. list of ModelBase instances. (if found)
        B. None. (if not found)
        """
        client = MongoClient(
            MONGO_DB_HOST, MONGO_DB_PORT)
        db = client[MONGO_DB_NAME]

        results = db[cls.__collection__].find()
        return list(cls.generateInstances(results))

    @classmethod
    def textSearch(cls, text, limit, skip):
        """Find by text search and return all matched instances.

        Args:
        1. search text(str)
        2. limit(int)
        3. skip(int)
        """
        # return ...
        cursor = cls.__db[cls.__collection__].find(
            {'$text': {'$search': text}},
            {'score': {'$meta': 'textScore'}}).skip(skip).limit(limit)
        cursorResults = cursor.sort([('score', {'$meta': 'textScore'})])
        return list(cls.generateInstances(cursorResults))

    @classmethod
    def count(cls):
        """Return the number of the documents.

        The wrapper of count() method in pymongo.
        """
        return cls.__db[cls.__collection__].count()

    @classmethod
    def remove(cls, query):
        """Remove documents matched with given key/values.

        The wrapper of remove() method in pymongo.
        """
        result = cls.__db[cls.__collection__].remove(query)
        logging.info(result)
        if 'ok' in result:
            return True if result['ok'] else None
        else:
            return False
