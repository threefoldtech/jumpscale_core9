from js9 import j
import os
import capnp
# import msgpack
import base64

ModelBaseCollection = j.data.capnp.getModelBaseClassCollection()
ModelBase = j.data.capnp.getModelBaseClass()
# from JumpScale9.clients.tarantool.KVSInterface import KVSTarantool


class $NameModel(ModelBase):
    '''
    '''

    def index(self):
        #no need to put indexes because will be done by capnp
        pass

    def save(self):
        self.reSerialize()
        self._pre_save()
        buff = self.dbobj.to_bytes()          
        key=self.key          
        # key=msgpack.dumps(self.key)
        # key=base64.b64encode(self.key.encode())
        return self.collection.client.call("model_$name_set",(key,buff))

    def delete(self):                    
        key=self.key          
        # key=base64.b64encode(self.key.encode())
        return self.collection.client.call("model_$name_del",(key))


class $NameCollection(ModelBaseCollection):
    '''
    This class represent a collection of $Names
    It's used to list/find/create new Instance of $Name Model object
    '''

    def __init__(self):
        self.logger = j.logger.get('model.$name')
        category = '$name'
        namespace = ""

        # instanciate the KVS interface on top of tarantool
        # cl = j.clients.tarantool.client_get()  # will get the tarantool from the config file, the main connection
        # db = KVSTarantool(cl, category)
        # mpath = j.sal.fs.getDirName(os.path.abspath(__file__)) + "/model.capnp"
        # SchemaCapnp = j.data.capnp.getSchemaFromPath(mpath, name='$Name')

        self.client =  j.clients.tarantool.client_get() #will get the tarantool from the config file, the main connection
        mpath=j.sal.fs.getDirName(os.path.abspath(__file__))+"/model.capnp"
        SchemaCapnp=j.data.capnp.getSchemaFromPath(mpath,name='$Name')
        super().__init__(SchemaCapnp, category=category, namespace=namespace, modelBaseClass=$NameModel, db=self.client, indexDb=self.client)
        self.client.db.encoding=None

    def new(self):
        return $NameModel(collection=self, new=True)

    def get(self,key):                    
        resp=self.client.call("model_$name_get",key)
        if len(resp.data) <= 1 and len(resp.data[0]) > 2:
            raise KeyError("value for %s not found" % key)
        value = resp.data[0][1]
        return $NameModel(key=key,collection=self, new=False,data=value)


    # BELOW IS ALL EXAMPLE CODE WHICH NEEDS TO BE REPLACED

    def list(self):
        resp=self.client.call("model_$name_list")
        return  [item.decode() for item in resp[0]]

    # def list(self, actor="", service="", action="", state="", serviceKey="", fromEpoch=0, toEpoch=9999999999999,tags=[]):
    #     raise NotImplementedError()
    #     return res
    
    # def find(self, actor="", service="", action="", state="", serviceKey="", fromEpoch=0, toEpoch=9999999999999, tags=[]):
    #     raise NotImplementedError()
    #     res = []
    #     for key in self.list(actor, service, action, state, serviceKey, fromEpoch, toEpoch, tags):
    #         if self.get(key):
    #             res.append(self.get(key))
    #     return res

