#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mongobase.py
#
#
# MODEL DEFINITION:
# 1. create a subclass.
# 2. set each definitions as below in the subclass.
#
#    __collection__ = ''  #  the collection name
#    __database__ = ''  #  the name of db restoring this instance
#    __structure__ = {}  # define keys and the data type
#    __required_fields__ = []  # lists required keys
#    __default_values__ = {}  #  default values to some keys
#    __validators__ = {}  #  pairs like key: validatefunc()
#    __search_text_keys__ = []  #  keys for text search
#    __search_text_index_unit__ = ''  #  split unit for text search
#    __indexes__ = []  #  index list
#
#
# Interface:
# 1. insert methods
#   - insertIfNotExistsWithKeys(*args) [Instance method]
#   - insertIfNotExistsWithQueryDict(self, query) [Instance method]
#
# 2. update methods
#   - updateWithCorrespondentKey(self, find_key) [Instance method]
#   - findAndUpdateById(cls, _id, updates) [Class method]
#
# 3. find methods
#   - find(cls, query, limit=None, skip=None, sort=None) [Class method]
#   - findOne(cls, query) [Class method]
#   - findAll(cls) [Class method]
#   - findInRanges(cls, ranges_dict, limit, skip, sort) [Class method]
#   - textSearch(cls, text, limit, skip) [Class method]
#   - distinct(key) [Class method]
#
#   - count(cls) [Class method]
#   - remove(cls, query) [Class method]
#   - incrementalId(cls) [Class method]
#


import csv
import datetime
import logging
import unicodedata
import inspect
import jaconv
import MeCab
from pymongo import TEXT, MongoClient, ReturnDocument, DESCENDING, ASCENDING
from pymongo.operations import InsertOne, ReplaceOne, UpdateOne, UpdateMany
from mongobase.mongobase import ModelBase
from mongobase.config import Config


class db_context(object):
    """
    Example::
        >>> with db_context(db_name='test') as db:
        ...   obj = MongoBaseSubClass({'_id': ObjectId, 'index': 1})
        ...   obj.save(db=db)
        ...   obj.update({'index': 2})
        ...   resu
    """
    def __init__(self, db_uri=Config.MONGO_DB_URI, db_name=None):
        assert db_uri and db_name, 'db_uri and db_name must be specified'
        self.__db_uri__ = db_uri
        self.__db_name__ = db_name

    def create_db(self, db_uri, db_name):
        self.__db = MongoClient(
            db_uri,
            connectTimeoutMS=Config.MONGO_DB_CONNECT_TIMEOUT_MS,
            serverSelectionTimeoutMS=Config.MONGO_DB_SERVER_SELECTION_TIMEOUT_MS,
            socketTimeoutMS=Config.MONGO_DB_SOCKET_TIMEOUT_MS,
            socketKeepAlive=Config.MONGO_DB_SOCKET_KEEP_ALIVE,
            maxIdleTimeMS=Config.MONGO_DB_MAX_IDLE_TIME_MS,
            maxPoolSize=Config.MONGO_DB_MAX_POOL_SIZE,
            minPoolSize=Config.MONGO_DB_MIN_POOL_SIZE,
            waitQueueMultiple=Config.MONGO_DB_WAIT_QUEUE_MULTIPLE,
            waitQueueTimeoutMS=Config.MONGO_DB_WAIT_QUEUE_TIMEOUT_MS
        )[db_name]
        return self.__db

    def __enter__(self):
        return self.create_db(self.__db_uri__, self.__db_name__)

    def __exit__(self, *args):
        return self.__db.client.close()


class MongoBase(ModelBase):
    __collection__ = ''  # set the collection name
    # __structure__ = {}  # define keys and the data type
    # __required_fields__ = []  # lists required keys
    # __default_values__ = {}  # set default values to some keys
    # __validators__ = {}  # set pairs like key: validatefunc()
    __search_text_keys__ = []  # index keys for text search. [('key', weight(int)),..] if weighted_type is 'weighted'
    __search_text_index_unit__ = 'bigram'  # either bigram or morpheme
    __search_text_index_with_kana__ = False  # add kana from mecab to the index if True
    __search_text_index_with_unigram__ = False  # add unigram to the index if True
    __search_text_weight_type__ = 'uniform'  # designate weights to each text index key if 'weighted'
    __indexes__ = []  # set index for any key.

    __db_uri__ = Config.MONGO_DB_URI
    __db_name__ = Config.MONGO_DB_NAME

    __db = MongoClient(
            __db_uri__,
            connectTimeoutMS=Config.MONGO_DB_CONNECT_TIMEOUT_MS,
            serverSelectionTimeoutMS=Config.MONGO_DB_SERVER_SELECTION_TIMEOUT_MS,
            socketTimeoutMS=Config.MONGO_DB_SOCKET_TIMEOUT_MS,
            socketKeepAlive=Config.MONGO_DB_SOCKET_KEEP_ALIVE,
            maxIdleTimeMS=Config.MONGO_DB_MAX_IDLE_TIME_MS,
            maxPoolSize=Config.MONGO_DB_MAX_POOL_SIZE,
            minPoolSize=Config.MONGO_DB_MIN_POOL_SIZE,
            waitQueueMultiple=Config.MONGO_DB_WAIT_QUEUE_MULTIPLE,
            waitQueueTimeoutMS=Config.MONGO_DB_WAIT_QUEUE_TIMEOUT_MS
        )[__db_name__]

    def __init__(self, init_dict):
        super().__init__(init_dict)

    @classmethod
    def _client(cls, db_uri=None):
        """Return MongoClient.

        This method is used in other methods of MongoBase.
        """
        db_uri = db_uri if db_uri else cls.__db_uri__
        return MongoClient(
            db_uri,
            connectTimeoutMS=Config.MONGO_DB_CONNECT_TIMEOUT_MS,
            serverSelectionTimeoutMS=Config.MONGO_DB_SERVER_SELECTION_TIMEOUT_MS,
            socketTimeoutMS=Config.MONGO_DB_SOCKET_TIMEOUT_MS,
            socketKeepAlive=Config.MONGO_DB_SOCKET_KEEP_ALIVE,
            maxIdleTimeMS=Config.MONGO_DB_MAX_IDLE_TIME_MS
        )

    @classmethod
    def _db(cls, db_name=None):
        db_name = db_name if db_name else cls.__db_name__
        return cls._client()[db_name]

    @classmethod
    def set_test_db_client(cls, test_db_uri, test_db_name):
        """Set Test MongoDB.

        Set cls.__db for testing.
        """
        MongoBase.__db_uri__ = test_db_uri
        MongoBase.__db_name__ = test_db_name
        MongoBase.__db = cls._client(test_db_uri)[test_db_name]

    @classmethod
    def reset_test_db_client(cls):
        """Reset Test MongoClient and DB to default.

        Set cls.__db for the default.
        """
        MongoBase.__db_uri__ = Config.MONGO_DB_URI
        MongoBase.__db_name__ = Config.MONGO_DB_NAME
        MongoBase.__db = cls._client(Config.MONGO_DB_URI)[Config.MONGO_DB_NAME]

    def save(self, db=None):
        return self.insertIfNotExistsWithKeys('_id', db=db)

    def update(self, db=None):
        return self.updateWithCorrespondentKey('_id', db=db)

    def remove(self, db=None):
        return self.deleteById(self._id, db=db)

    @classmethod
    def find(cls, query: dict, limit=None, skip=None, sort=None, returns_generator=False, db=None, **kwargs) -> list:
        """Find and return instances.

        returns:
            objects (list):  ModelBase instances if found else None.
        """
        results = cls.__find(
            query, limit=limit, skip=skip, sort=sort, db=db, **kwargs)
        if returns_generator:
            return cls.generateInstances(results)
        else:
            return list(cls.generateInstances(results))

    @classmethod
    def findOne(cls, query, db=None, *args, **kwargs):
        """Find one and return an instance.

        returns:
            object (ModelBase): a ModelBase instance if found else None.
        """
        __db = db if db else cls.__db
        result = __db[cls.__collection__].find_one(query, *args, **kwargs)
        if result:
            return cls(result)
        else:
            return None

    @classmethod
    def findAll(cls, db=None):
        """Find all and return all instances of the class.

        returns:
            objects (list): ModelBase instances if found else None.
        """
        __db = db if db else cls.__db
        results = __db[cls.__collection__].find()
        return list(cls.generateInstances(results))

    @classmethod
    def __find(cls, query, limit=None, skip=None, sort=None, db=None, **kwargs) \
            -> 'cursor obj':
        """Find and return cursor objects.

        returns:
            cursor objects (list): list of Pymongo cursor instances if found else None
        """
        __db = db if db else cls.__db
        # limit & skip & sort
        if limit and skip and sort:
            results = __db[cls.__collection__]\
                .find(query, **kwargs).sort(sort).skip(skip).limit(limit)

        # limit & skip
        elif limit and skip and not sort:
            results = __db[cls.__collection__]\
                .find(query, **kwargs).skip(skip).limit(limit)
        # limit & sort
        elif limit and not skip and sort:
            results = __db[cls.__collection__]\
                .find(query, **kwargs).sort(sort).limit(limit)
        # skip & sort
        elif not limit and skip and sort:
            results = __db[cls.__collection__]\
                .find(query, **kwargs).sort(sort).skip(skip)

        # limit
        elif limit and not skip and not sort:
            results = __db[cls.__collection__].find(
                query, **kwargs).limit(limit)
        # skip
        elif not limit and skip and not sort:
            results = __db[cls.__collection__].find(
                query, **kwargs).skip(skip)
        # sort
        elif not limit and not skip and sort:
            results = __db[cls.__collection__].find(
                query, **kwargs).sort(sort)

        # (just find)
        else:
            results = __db[cls.__collection__].find(query, **kwargs)
        return results

    @classmethod
    def createIndexes(cls, db=None, **kwargs):
        """ Create indexes defined in __indexes__
        """
        __db = db if db else cls.__db
        if len(cls.__indexes__) >= 1:
            for index in cls.__indexes__:
                logging.info('start creating index: {} {}'.format(cls.__name__, index))
                __db[cls.__collection__].create_index(index, background=True, **kwargs)
                logging.info('finished creating index: {} {}'.format(cls.__name__, index))

    def insertIfNotExistsWithKeys(self, *args, db=None):
        """Insert this object to db if not already exists.

        returns:
            insertion results (MongoBase object or None): if already inserted, returns None.
        """
        query = {key: getattr(self, key) for key in args}
        return self.insertIfNotExistsWithQueryDict(query, db=db)

    def insertIfNotExistsWithQueryDict(self, query: dict, db=None):
        """Insert this object to db if no matched document exists.

        args:
            query (dict): not perform the insertion if matched document exists.

        returns:
            result (MongoBase object or None): returns self if inserted
        """
        __db = db if db else self.__db
        if bool(query) and __db[self.__collection__].find_one(query):
            logging.info('ALREADY EXISTS, NOT SAVE')
            return None
        else:
            return self.__insert(db=db)

    def __insert(self, db=None):
        """The wrapper for db[collection_name].insert_one() in pymongo.

        This performs,
            1. sets search text with generateSearchGram.
            2. validates instance properties with validate().
            3. calls insert_one() method in pymongo.
            4. calls create_index() method in pymongo if __search_text_keys__ has any value.
        """
        __db = db if db else self.__db
        storeable_document = self.__prepare_insert()
        if __db[self.__collection__].insert_one(storeable_document):
            # create search index after inserted
            if self.__search_text_keys__:
                __db[self.__collection__].create_index(
                    [('search_text', TEXT)], default_language='english')
            logging.info(u'NEW {} INSERTED.'.format(self))
            return self
        else:
            logging.info(u'[WARNING] {} NOT INSERTED.'.format(self))
            return None

    def __prepare_insert(self):
        """Convert to a storeable formatted document.

        return:
            document (dict): storeable formatted object.
        """
        # check __required_fields__
        assert self._is_required_fields_satisfied()
        # prepare document to save
        document = self.purify()
        assert '_id' in document, \
            f'document must have key "_id". but not in {document}.'
        # set search_text
        if self.__search_text_keys__:
            # select index method
            if self.__search_text_weight_type__ == 'uniform':
                search_text = ' '.join(
                    [self[key] for key in self.__search_text_keys__ if self[key]]
                )
            elif self.__search_text_weight_type__ == 'weighted':
                # repeat n times depending on keys in self.__search_text_keys__
                search_text = ' '.join(
                    [' '.join([self[key] for _ in range(weight)]) for key, weight in
                     self.__search_text_keys__ if self[key]]
                )
            else:
                raise Exception('index method must be either uniform or weighted')

            # select index unit
            if self.__search_text_index_unit__ == 'bigram':
                search_gram = self.generateSearchBiGramStr(search_text)
                document.update(
                    {'search_text': search_gram})
                self.search_text = search_gram
            elif self.__search_text_index_unit__ == 'morpheme':
                search_morpheme = self.generateSearchMorphemeStr(
                    search_text,
                    with_kana=self.__search_text_index_with_kana__,
                    with_unigram=self.__search_text_index_with_unigram__
                )
                document.update({'search_text': search_morpheme})
                self.search_text = search_morpheme
            else:
                raise Exception('index unit must be either bigram or morpheme')
        # validate
        assert self.validate(document)
        return document

    @classmethod
    def bulk_insert(cls, inserts: list, db=None):
        """Bulk insert operation.

        args:
            inserts (list): list of MongoBase instances to be inserted.

        returns:
            inserted_count (int): # of documents inserted.
        """
        __db = db if db else cls.__db
        requests = []
        for obj in inserts:
            assert isinstance(obj, cls),\
                f'all objects must be MongoBase objects. but {obj} is {type(obj)}.'
            # create a valid document to insert
            storeable_document = obj.__prepare_insert()
            requests += [InsertOne(storeable_document)]
        result = __db[cls.__collection__].bulk_write(requests)
        return result.inserted_count

    @classmethod
    def bulk_update(cls, updates: list, ids: list = None, db=None):
        """Bulk update operation.

        args:
            updates (list): list of update dictionaries.
            ids (list): list of _id of documents to be updated. (optional)

        *if updates have _id, ids is not required

        returns:
            updated_count (int): # of documents updated.
        """
        __db = db if db else cls.__db
        requests = []
        if ids:
            for _id, update in zip(ids, updates):
                update = cls.__prepare_updates(update)
                requests += [UpdateOne({'_id': _id}, update)]
        else:
            for update in updates:
                assert update.get('_id'),\
                    '_id is required in update object when ids are not set in the argument.'
                _id = update.get('_id')
                update = cls.__prepare_updates(update)
                requests += [UpdateOne({'_id': _id}, {'$set': update})]
        print(requests[0])
        result = __db[cls.__collection__].bulk_write(requests)
        return result.modified_count

    def updateWithCorrespondentKey(self, find_key, db=None):
        """Update an instance with the identical key.

        args:
            find_key (str): the key of instance to identify the document.
        """
        if hasattr(self, find_key) and getattr(self, find_key):
            storeable_document = self.__prepare_insert()
            return MongoBase.__findAndUpdate(
                self, find_key, getattr(self, find_key), storeable_document, db=db)
        return None

    @classmethod
    def findAndUpdateById(cls, _id, update: dict, db=None):
        """Find and update.(Class method)

        args:
            _id (any type): any type of value defined in the __structure__
            update (dict): key,value pairs to update.

        __findAndUpdate() is called finally.
        """
        logging.info(u'FIND AND UPDATE {} WITH {}'.format(_id, update))
        return cls.__findAndUpdate(cls, '_id', _id, update, db=db)

    @staticmethod
    def __findAndUpdate(
            cls_or_instance, find_key, find_val, update: dict, db=None):
        """Find and update.

        args:
            cls_or_instance (MongoBase subclass or instance):
            find_key (any type): identical key to find a document to update
            find_val (any type): identical value to find a document to update
            update (dict): keys and values to be updated.
        """
        __db = db if db else cls_or_instance.__db
        # create a valid update object
        update = cls_or_instance.__prepare_updates(update)
        # update object must be like {'$set': {'key': val,...}}
        # otherwise, the rest of fields will be removed
        update_set = {'$set': update}
        document = __db[cls_or_instance.__collection__] \
            .find_one_and_update(
                {find_key: find_val},
                update_set,
                return_document=ReturnDocument.AFTER)
        if not document:
            return None
        if inspect.isclass(cls_or_instance):
            return cls_or_instance(document)
        else:
            return cls_or_instance

    @classmethod
    def __prepare_updates(cls, update: dict):
        """Create an valid update object.

        args:
            update (dict): keys and values to be updated.
        """
        update['updated'] = datetime.datetime.now(datetime.timezone.utc)
        # update search_text if the related field changed
        if cls.__search_text_keys__\
                and list(set(update).intersection(
                    cls.__search_text_keys__)):

            # select index method
            if cls.__search_text_weight_type__ == 'uniform':
                search_text = ' '.join(
                    [update[key] for key in cls.__search_text_keys__ if update[key]]
                )
            elif cls.__search_text_weight_type__ == 'weighted':
                # repeat n times depending on keys in cls.__search_text_keys__
                search_text = ' '.join(
                    [' '.join([update[key] for _ in range(weight)]) for key, weight in
                     cls.__search_text_keys__ if update[key]]
                )
            else:
                raise Exception('index method must be either uniform or weighted')

            if cls.__search_text_index_unit__ == 'bigram':
                update['search_text'] = cls.generateSearchBiGramStr(search_text)
            elif cls.__search_text_index_unit__ == 'morpheme':
                update['search_text'] = cls.generateSearchMorphemeStr(
                    search_text,
                    with_kana=cls.__search_text_index_with_kana__,
                    with_unigram=cls.__search_text_index_with_unigram__
                )
            else:
                raise Exception('index unit must be either bigram or morpheme')
        # validate
        assert cls(update).validate()
        # return update dict excluding key '_id'
        return {k:v for k,v in update.items() if k != '_id'}

    @classmethod
    def updateMany(
            cls, query: dict, update: dict, upsert=False, array_filters=None,
            bypass_document_validation=False, collation=None, session=None, db=None):
        """Update specific fields for many documents.

        returns:
            - matched_count: int
            - modified_count: int
        """
        result = cls.__updateMany(
            cls, query, update, upsert=upsert,
            array_filters=array_filters, bypass_document_validation=bypass_document_validation,
            collation=collation, session=session, db=db)
        return result.matched_count, result.modified_count

    @staticmethod
    def __updateMany(
            cls_or_instance, query: dict, update: dict, upsert=False,
            array_filters=None, bypass_document_validation=False,
            collation=None, session=None, db=None):
        """Update specific fields for many documents.

        equal to db.collection.updateMany(query, {$set: {key: new_val})
        """
        __db = db if db else cls_or_instance.__db
        return __db[cls_or_instance.__collection__].update_many(
            query, {'$set': update}, upsert=upsert, array_filters=array_filters,
            bypass_document_validation=bypass_document_validation,
            collation=collation, session=session)

    @classmethod
    def deleteById(cls, _id, db=None):
        return cls.__delete_one({'_id': _id}, db=db)

    @classmethod
    def delete(cls, query, db=None):
        return cls.__delete(query, db=db)

    @classmethod
    def __delete_one(cls, query, db=None):
        """Wrapper of delete_one()

        returns:
            deleted_count (int): # of deleted documents
        """
        __db = db if db else cls.__db
        result = __db[cls.__collection__].delete_one(query)
        return result.deleted_count

    @classmethod
    def __delete(cls, query, db=None):
        """Wrapper of delete_many()

        returns:
            deleted_count (int): # of deleted documents
        """
        __db = db if db else cls.__db
        result = __db[cls.__collection__].delete_many(query)
        return result.deleted_count

    @staticmethod
    def generateSearchBiGramStr(origin_text):
        """Generate Text search bi-gram.

        'Some text value'
        -> 'So om me et te xt tv va al lu ue'
        """

        def generate(text):
            search_gram = ''
            # search_gram: 'Some text value'
            text_without_space = text.replace(' ', '')
            for i in range(0, len(text_without_space)-1):
                if i != 0:
                    search_gram += ' '
                search_gram += text_without_space[i:i+2]
            # search_gram: 'So om me et te ex xt tv va al lu ue'
            return search_gram

        texts = origin_text.split(' ')
        return ' '.join([generate(text) for text in texts])

    @staticmethod
    def generateSearchMorphemeStr(origin_text, with_kana=False, with_unigram=False):
        """Generate Morpheme from original text for text search

        args:
            origin_text (str): original text
            with_kana (bool): True if add yomi to text
            with_unigram (bool): if True, add unigram
        returns:
            parced_text (str): parsed text
        """
        preprocessed_text = unicodedata.normalize('NFKC', origin_text)

        if with_kana:
            tagger = MeCab.Tagger("-O chasen -u {}".format(Config.FOOD_NAME_MECAB_DIC_PATH))
            morphs = tagger.parse(preprocessed_text).split('\n')[:-2]
            text_by_morph = ' '.join(
                [morph.split('\t')[0] for morph in morphs] + [morph.split('\t')[1] for morph in morphs]
            )
        else:
            tagger = MeCab.Tagger("-O wakati -u {}".format(Config.FOOD_NAME_MECAB_DIC_PATH))
            text_by_morph = tagger.parse(preprocessed_text).replace(' \n', '')

        if with_unigram:
            text_by_morph = text_by_morph + ' ' + ' '.join([char for char in preprocessed_text])
        return text_by_morph

    @classmethod
    def textSearch(cls, text, limit, skip, query=None, sort=None, with_kana=False, with_unigram=False,
                   db=None, **kwargs):
        """Find by text search and return all matched instances.

        args:
            search text(str):
            limit(int):
            skip (int):
            query(dict):
            sort (int): condition other than text search
        """
        __db = db if db else cls.__db

        if not query:
            query = {}

        if cls.__search_text_index_unit__ == 'bigram':
            query['$text'] = {'$search': cls.generateSearchBiGramStr(text)}
        elif cls.__search_text_index_unit__ == 'morpheme':
            text = ' '.join([text, jaconv.hira2kata(text)])  # add kata-kana converted from hira-kana
            print(text)
            query['$text'] = {
                '$search': cls.generateSearchMorphemeStr(text, with_kana=with_kana, with_unigram=with_unigram)
            }
        else:
            raise Exception('index unit must be either bigram or morpheme')

        if not sort:
            # if no sort condition is set, the order follows textScore.
            sort = [('score', {'$meta': 'textScore'})]

        cursor = __db[cls.__collection__].find(
            query,
            {'score': {'$meta': 'textScore'}},
            **kwargs).skip(skip).limit(limit)
        print(f'B : {cursor}')
        cursorResults = cursor.sort(sort)
        return list(cls.generateInstances(cursorResults))

    @classmethod
    def aggregate(cls, pipeline: list, should_return_generator=False, db=None):
        """Call db.collection.aggregate()

        args:
            pipeline: list  ex) [{ '$group' : {
                                    '_id': '$gender',
                                    'count': { '$sum': 1}
                                }}]
        returns:
            - aggregation results: (list)  ex.) [{'_id': 1, 'count': 1213}]
        """
        __db = db if db else cls.__db
        if should_return_generator:
            return __db[cls.__collection__].aggregate(pipeline=pipeline)
        else:
            return [item for item in __db[cls.__collection__].aggregate(pipeline=pipeline)]

    @classmethod
    def largestID(cls, db=None) -> int:
        """Return largest _id.
        """
        ids = cls.distinct('_id', db=db)
        largest_id = 0
        for _id in ids:
            largest_id = int(_id) if largest_id < int(_id) else largest_id
        return largest_id

    @classmethod
    def count(cls, query=None, db=None):
        """Return the number of the documents.

        The wrapper of count() method in pymongo.
        """
        __db = db if db else cls.__db
        return __db[cls.__collection__].count(query)

    @classmethod
    def incrementalId(cls, db=None) -> int:
        __db = db if db else cls.__db
        cursor = __db[cls.__collection__].find({}, {'_id': 1})
        return cursor.sort('_id', DESCENDING).limit(1).next()['_id'] + 1\
            if int(cursor.count()) > 0 else 1

    @classmethod
    def distinct(cls, key, query=None, db=None):
        """Get a list of distinct values.

        The wrapper of distinct() method in pymongo.
        """
        __db = db if db else cls.__db
        if not query:
            return __db[cls.__collection__].distinct(key)
        else:
            return cls.__find(query, db=__db).distinct(key)

    @classmethod
    def outputCsv(cls, query={}):
        """Output data as csv.
        """
        keys = cls.__structure__.keys()
        with open('{}.csv'.format(cls.__name__), 'w') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow(keys)
            for estate in cls.find(query):
                try:
                    values = [estate.serialize().get(key) for key in keys]
                except Exception as e:
                    logging.debug(e)
                else:
                    writer.writerow(values)

    @classmethod
    def importFromCsv(cls, id_keys=None):
        """ Import station database from csv file.
        """
        data_frame = pd.read_csv(cls.CSV_FILE)
        import math
        for row, data in data_frame.iterrows():
            data = dict(data)
            for key, val_type in cls.__structure__.items():
                val = data.get(key)
                if data.get(key) and not isinstance(data.get(key), val_type):
                    try:
                        data[key] = val_type(data.get(key))
                    except:
                        pass

                if (isinstance(val, float) and math.isnan(val)):
                    data[key] = None

            if id_keys:
                try:
                    data['_id'] = ''.join([data[key] for key in id_keys])
                except TypeError as e:
                    continue

            print(data['_id'])

            cls(dict(data)).insertIfNotExistsWithQueryDict(
                {'_id': data['_id']})