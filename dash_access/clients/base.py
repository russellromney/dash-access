import os
import msgpack
import decimal
import time

class BaseAccessStore(object):
    """default encoding for all stores"""
    encoder = msgpack

    def teardown(self):
        # default is to do nothing
        # e.g. for dynamo, no need to do anything to close clients
        pass

    def instantiate(self):
        pass
    
    def get_table(self):
        pass 
    
    def table_key(self):
        pass
    
    def get(self,*args,**kwargs):
        return self._get(*args,**kwargs)

    def _get(self):
        pass

    def get_all(self, *args,**kwargs):
        return self._get_all(*args,**kwargs)

    def _get_all(self, *args,**kwargs):
        pass
    
    def set(self, *args,**kwargs):
        return self._set(*args,**kwargs)

    def _set(self):
        pass
    
    def insert(self, *args,**kwargs):
        return self._insert(*args,**kwargs)

    def _insert(self):
        pass
    
    def encode(self, val):
        return self._encode(val)

    def _encode(self, val):
        return val

    def decode(self, val):
        return self._decode(val)
    
    def _decode(self, val):
        return val

    def delete(self, *args, **kwargs):
        return self._delete(*args, **kwargs)

    def _delete(self):
        pass

    def table_fields(self, table: str) -> dict:
        """
        a list of all the fields that should be in the 
        table; idea is to fill all the values in with a default
        if not in the return value from the store
        """
        if table == 'groups':
            return {k:None for k in ["id","update_ts"]}
        elif table == 'relationships':
            return {k:None for k in ['id','principal','principal_type','granted','granted_type','ts']}
        elif table == "access_events":
            return {k:None for k in ["user_id","permission","ts","status"]}
        elif table == "admin_events":
            return {k:None for k in ["ts","table_name","operation","vals","where_val"]}
        return {}