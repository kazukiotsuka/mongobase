# mongobase
lightway orm mapper for pymongo

### basic usage
```python
animal_name = 'wild boar'
new_animal = Animal({
    'name': animal_name
    })
same_animal = Animal.findOne({'name': animal_name})
if same_animal:
    same_animal.count = same_animal.count + 1
    return same_animal.update()
else:
    return new_animal.save()
```

###### mongobase instance works both as object and dict

```python
a_cat = Animal.findOne({'name': 'cat'})
a_cat.age = 2
a_cat['keeper'] = {'name': 'spam egg', 'gender': 'male'}
a_cat.update()
```

###### find with mongodb dictionary / return mongobase instances list

```python
mammals = Animal.find({'keeper': {'$exists': True}, 'type': 'mammal'}, limit=10, skip=10)
for mammal in mammals:
  print mammal.name
  print mammal.keeper
```

###### automatic required field / type check

```python
new_animal = Animal({
  'name': None
})
new_animal.save() # raise RequieredKeyIsNotSatisfied exception
new_animal = Animal({
  'name': 101
})
new_animal.save() # raise TypeError exception
```

###### automatically generate textSearch model with bigram

```python
class Animal(ModelBase):
    ...
    __indexed_key__ = 'name' # search gram key
    ...
```
```python
search_key = generateBigram(name) # name:'reindeer' -> search_key:'re ei in nd de ee er'
animals = Animal.textSearch(search_key, limit=1, skip=0)
```


###### model definition

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
