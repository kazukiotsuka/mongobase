![MongoBase Logo](https://github.com/kazukiotsuka/mongobase/blob/master/docs/source/img/mongobase.png)


MongoBase is a Python package that provides high-level features:
- Lightweight OR Mapper (ORM) for MongoDB
- Simple DataBase Model structure definition with automatic type checking
- High-level automatic text search indexes generation from multiple keys

### Dependencies
- pymongo_ 3.7+

More About MongoBase
-------------------------

| Component | Description |
| ---- | --- |
|**mongobase** | an high-level interface with model definition system from ModelBase and many database operations|
|**modelbase** | an OR Mapper class with automatic type checking according to the defined structure (MongoBase subclass)|

The philosophies on MongoBase are
- enable to use MongoDB on python easily and programatically safely
- cleary viewable everything about the data model just by a quick looking over the model definition
- easy to learn how to use. for instance, method names correspond to MongoDB to be able to use them as if on the mongoclient.
- high performance. it uses the latest connection pool mechanism so that efficiently use client objects




The introduction of Basic Interfaces
---------------------------

#### Model Definition

```python
class Bird(MongoBase):
    __collection__ = 'birds'
    __structure__ = {
        '_id': ObjectId,
        'name': str,
        'age': int,
        'is_able_to_fly': bool,
        'created': dt.datetime,
        'updated': dt.datetime
    }
    __required_fields__ = ['_id', 'name']
    __default_values__ = {
        '_id': ObjectId(),
        'is_able_to_fly': False,
        'created': dt.datetime.now(dt.timezone.utc),
        'updated': dt.datetime.now(dt.timezone.utc)
    }
    __validators__ = {
        'name': validate_length(0, 1000),
    }
    __search_text_keys__ = ['name'] 
    __search_text_index_type__ = 'bigram'
    __indexes__ = [
        [('item_name', ASCENDING),],
    ]
```

Insert & Update
---------------------------
```python
>> chicken = Bird({'_id': ObjectId(), 'name': 'chicken', 'age': 3})
>> chicken.save()
{'_id': ObjectId('5c80f4fa16fa0d6c102cd2a6'),
 'name': 'chicken',
 'age': 3,
 'is_able_to_fly': False,
 'created': datetime.datetime(2019, 3, 7, 10, 39, 54, 643685, tzinfo=datetime.timezone.utc),
 'updated': datetime.datetime(2019, 3, 7, 10, 39, 54, 643690, tzinfo=datetime.timezone.utc)}
>> chicken.is_able_to_fly = True
>> chicken.update()
```

#### Find
```python
>>> Bird.findOne({'name': 'mother chicken'})
{'_id': ObjectId('5c79166716fa0d215968d3ba'),
 'name': 'mother chicken',
 'age': 63,
 'is_able_to_fly': False,
 'created': datetime.datetime(2019, 3, 1, 11, 20, 21, 306000),
 'updated': datetime.datetime(2019, 3, 1, 11, 20, 21, 306000)}
>>> mother_chicken.remove()
1
>>> all_chickens = Bird.find({'name': 'chicken'}, sort=[('_id', ASCENDING)])
list of mongobase instances are returned.
>>> len(all_chickens)
18
>>> Bird.count()
201
```

#### Bulk Operation

- bulk_insert
```python
>>> many_pigeon = []
>>> for i in range(10000):
>>>     many_pigeon += [Bird({'_id': ObjectId(), 'name': f'pigeon', 'age': i})]
>>> Bird.bulk_insert(many_pigeon)
10000
```

```
- bulk_update

>>> updates = []
>>> for pigeon in many_pigeon:
>>>    pigeon.age *= 3
>>>    updates += [pigeon]
>>> Bird.bulk_update(updates)
10000
```




#### Contextual Database

```python
with db_context(db_uri='localhost', db_name='test') as db:
    flamingo = Bird({'_id': ObjectId(), 'name': 'flamingo', 'age': 20})
    flamingo.save(db=db)
    
    flamingo.age = 23
    flamingo = flamingo.update(db=db)
    flamingo = Bird.findAndUpdateById(flamingo._id, {'age': 24}, db=db)
    
    n_flamingo = Bird.count({'name': 'flamingo'}, db=db)

Bird.count({'name': 'flamingo'})

```

#### Multi Processing
```python
def breed(tasks):
    db = Bird._db()  # create a MongoDB Client for the forked process
    for i in range(len(tasks)):
        sparrow = Bird({'_id': ObjectId(), 'name': f'sparrow', 'age': 0})
        sparrow.save(db=db)
        
tasks = [[f'task {i}' for i in range(N_BATCH)] for j in range(N_PROCESS)
process_pool = multiprocessing.Pool(N_PROCESS)
process_pool.map(breed, tasks)
```


#### MongoBase has Many Other Features
If you'd like to know other features, please check the file mongobase.py.

DB Settings
---------------------------
simply write to mongobase/config.py
```python
MONGO_DB_URI = "101.21.434.121"
MONGO_DB_URI_TEST = "localhost"
MONGO_DB_NAME = "zoo"
MONGO_DB_NAME_TEST = "zoo-test"
MONGO_DB_CONNECT_TIMEOUT_MS = 3000
MONGO_DB_SERVER_SELECTION_TIMEOUT_MS = 3000
MONGO_DB_SOCKET_TIMEOUT_MS = 300000
MONGO_DB_SOCKET_KEEP_ALIVE = True
MONGO_DB_MAX_IDLE_TIME_MS = 40000
MONGO_DB_MAX_POOL_SIZE = 200
MONGO_DB_MIN_POOL_SIZE = 10
MONGO_DB_WAIT_QUEUE_MULTIPLE = 12
MONGO_DB_WAIT_QUEUE_TIMEOUT_MS = 100
```


Getting Started
------------------
If you start MongoBase, there is a tutorial jupyter notebook here.  
Highly recommend to check it.
https://github.com/kazukiotsuka/mongobase/blob/master/tutorial/MongoBase_starting_guide.ipynb


Release and Contributing
---------------------------
Many methods are the wrapper of pymongo.  
There are a lot of features that this library is covering.  
Would appreciate if you add their methods anytime.


License
--------------------
MongoBase is MIT-style licensed, as found in the LICENSE file.