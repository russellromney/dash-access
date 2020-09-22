import os
import decimal
import boto3
from boto3.dynamodb.types import Binary

from clients.base import BaseAccessStore

class DynamoStore(BaseAccessStore):
    """
    representation of a connection to a remote key:value store

    abstracts
        encoding
        serialization
        which store is being used

    Override instantiate(), get_table(), _get(), _set(), etc. for easy inheritance
    """

    def __init__(self, path: str = None):
        # DYNAMO
        self.instantiate(path)

    def instantiate(self, path):
        """
        instantiate with dynamodb as the backing store
        """
        resource = boto3.resource("dynamodb")
        self.users = resource.Table(os.environ["USERS_TABLE"])
        self.groups = resource.Table(os.environ["GROUPS_TABLE"])

    def _encode(self, val):
        """
        Handles all type changes to the data store

        encodes the object if it's not a simple type, using its encode
            simple: int/str/bytes
            not simple: dict/list/tuple/float
        
        if it's a float it returns a decimal.Decimal object
        otherwise just returns the value
        """
        if isinstance(val, list) or isinstance(val, tuple) or isinstance(val, dict):
            out = self.encoder.dumps(val)
            out = Binary(out)
        elif isinstance(val, float):
            out = decimal.Decimal(val)
        else:
            out = val

    def _decode(self, val):
        """
        Handles all type changes from the data store

        if the value has type boto3.dynamodb.types.Binary, it was encoded before sending;
        grab the instance's value and decode it with the KeyValStore encoder        

        otherwise just returns the value
        """
        out = None
        if isinstance(val, decimal.Decimal) or isinstance(val, float):
            out = float(val)
        elif isinstance(val, Binary):
            out = val.value
            out = self.encoder.loads(out)
        elif isinstance(val, bytes):
            out = self.encoder.loads(val)
        else:
            out = val
        return out

    def get_table(self, table: str):
        """select the right table"""
        if table == "users":
            return self.users
        elif table == "groups":
            return self.groups

        # TABLE DOESN'T EXIST
        else:
            raise ValueError(f"KeyValStore: table {table} is not available. ")

    def get_all(self, table: str) -> list:
        return self._get_all(table=table)

    def _get_all(self, table: str) -> list:
        table_fields = self.table_fields(table)
        table = self.get_table(table)

        out = table.scan()
        if out.get('Items'):
            out = [
                {key: self.decode(value) for key, value in d.items()}
                for d in out['Items']
            ]
            # ADD DEFAULT FIELD VALUES FOR MISSING FIELDS
            for o in out:
                for field in table_fields:
                    if not field in o:
                        out[field] = table_fields[field]


        return []

    def get(self, key: str, table: str) -> dict:
        return self._get(key=key, table=table)

    def _get(self, key: str, table: str) -> dict:
        """
        key:
            str, int, float
            
        note on types:
            if value was a dictionary, it transforms back to dictionary and loads
            if value was a int, float, just returns the original value

        returns:            
            The value for the key in the store
            None if key does not exist

        NOTE this simplifies everything by returning the entire record 
            every time. Otherwise we'd have to do some custom logic. 
            It's easier to expect a full record and handle errors later.
        NOTE we fill in the blanks for fields that are missing; no errors here!
        """
        # SELECT TABLE
        table_fields = self.table_fields(table)
        table = self.get_table(table)

        # GET THE VALUE
        val = table.get_item(Key={"id": key})
        out = None
        if val.get("Item"):
            out = val["Item"]
            out = {key: self.decode(value) for key, value in out.items()}

            # ADD DEFAULT FIELD VALUES FOR MISSING FIELDS
            for field in table_fields:
                if not field in out:
                    out[field] = table_fields[field]

        return out

    def set(self, key: str, table: str, val: dict) -> bool:
        return self._set(key=key, table=table, val=val)

    def _set(self, key: str, table: str, val: dict) -> bool:
        """
        key:
            str
        val:
            str, int, float, dict, list, tuple

        notes on types:
            datatypes are handled with self.encode()

        returns:
            True if val successfully stored
            False otherwise
        """
        # SELECT TABLE
        table = self.get_table(table)

        # PROCESS VALUES
        out = {key: self.encode(value) for key, value in val.items() if key != "id"}

        # PUT THE VALUE
        res = table.put_item(Item={"id": key, **out})
        res = res["ResponseMetadata"].get("HTTPStatusCode") == 200

        return res

    def delete(self, key: str, table: str) -> bool:
        return self._delete(key=key, table=table)
    
    def _delete(self, key: str, table: str) -> bool:
        # SELECT TABLE
        table = self.get_table(table)

        # RUN THE DELETE
        res = table.delete_item(Key={"id": key})
        res = res["ResponseMetadata"].get("HTTPStatusCode") == 200

        return res


class DynamoLoggerStore(BaseAccessStore):
    """
    Logging setup.
    Default store is DyanmoDB.
    Overwrite _insert, instantiate, etc. for inheritance.
    instantiate must take a path variable
    """
    def __init__(self, path: str = None):
        self.instantiate(path)

    def instantiate(self, path):
        self.LOGIN_TABLE = os.environ["LOGGING_TABLE_LOGIN_EVENTS"]
        self.ACCESS_TABLE = os.environ["LOGGING_TABLE_ACCESS_EVENTS"]
        resource = boto3.resource("dynamodb")
        self.login_table = resource.Table(self.LOGIN_TABLE)
        self.access_table = resource.Table(self.ACCESS_TABLE)

    def get_table(self, table: str):
        if table == 'access':
            return self.access_table
        elif table == 'login':
            return self.login_table
        raise ValueError('LoggingStore: table must match login or access table in environment')

    
    def insert(self, table: str, **kwargs):
        return self._insert(table=table, **kwargs)
    
    def _insert(self, table: str, **kwargs):
        """
        insert values into a logging table
        table name must exist (duh)
        kwargs is column names mapped to values
        
        returns indicator of success
        """
        out = {key: self.encode(value) for key, value in kwargs.items()}
        this_table = self.get_table(table=table)
        res = this_table.put_item(Item=out)
        res = res["ResponseMetadata"].get("HTTPStatusCode") == 200
        return res