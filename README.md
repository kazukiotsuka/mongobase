# mongobase
lightweight O/R mapper for pymongo

###Dependencies
- pymongo_ 3.0+


###Basic usage

```python
animal_name = 'wild boar'
new_animal = Animal({
    'name': animal_name,
    'kind': 'cat'
    })
same_animal = Animal.findOne({'name': animal_name})
if same_animal:
    same_animal.count = same_animal.count + 1
    return same_animal.update()
else:
    return new_animal.save()
```

#####object/dict
mongobase instance works both as object and dict

```python
a_cat = Animal.findOne({'kind': 'cat'})
a_cat.age = 2
a_cat['keeper'] = {'name': 'spam egg', 'gender': 'male'}
a_cat.update()
```

#####find and fetch data
find with mongodb dictionary and return mongobase instances list

```python
vertebrates = Animal.find({'keeper': {'$exists': True}, 'type': 'vertebrate'}, limit=10, skip=10)
for vertebrate in vertebrates:
  print vertebrate.kind
  print vertebrate.keeper

mouse = Animal.findOne({'type': 'mammal', 'age': 10, 'kind':'mouse'})
print mouse # <Animal name='micky'>
```

#####automatic value check
automatic required field / type check

```python
new_animal = Animal({
  'name': None
})
new_animal.save() # raise RequieredKeyIsNotSatisfied exception
new_animal = Animal({
  'name': 'tom',
  'type': 101
})
new_animal.save() # raise TypeError exception 'the key type must be unicode'
```

#####text search
automatically generate textSearch model with bigram

```python
class Animal(ModelBase):
    ...
    __indexed_key__ = 'name' # search gram key
    ...
```

```python
search_key = generateBigram(name) # name:'big reindeer' -> search_key:'bi ig gr re ei in nd de ee er'
animals = Animal.textSearch(search_key, limit=1, skip=0)
```


#####model definition
model definition example

```python
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
```
