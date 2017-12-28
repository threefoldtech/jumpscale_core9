from js9 import j
import os
import copy
from .JSBaseClassConfig import JSBaseClassConfig
from .JSBaseClassConfigs import JSBaseClassConfigs
from .Config import Config


class ConfigFactory():

    def __init__(self):
        self.__jslocation__ = "j.tools.configmanager"
        self._path = ""
        self._cache = {}
        self.interactive = True

    def reset(self):
        self._cache = {}

    def _findConfigDirParent(self, path, die=True):
        if path == "":
            path = j.sal.fs.getcwd()

        # first check if there is no .jsconfig in parent dirs
        curdir = copy.copy(path)
        while curdir.strip() != "":
            if j.sal.fs.exists("%s/.jsconfig" % curdir) and j.sal.fs.exists("%s/.git" % curdir):
                break
            # look for parent
            curdir = j.sal.fs.getParent(curdir)
        if curdir.strip() != "":
            return curdir
        if die:
            raise RuntimeError(
                "Could not find config dir as parent of:'%s'" % path)
        else:
            return None

    @property
    def path_configrepo(self):
        if not self._path:
            self._path = self._findConfigDirParent(path="", die=False)
            if self._path == None:
                res = j.clients.git.getGitReposListLocal()
                for key, path in res.items():
                    checkpath = "%s/.jsconfig" % path
                    if key.startswith("config_"):
                        if j.sal.fs.exists(checkpath):
                            self._path = path
                            j.logger.logging.info("found jsconfig dir in: %s" % self._path)
                            return self._path
            else:
                return self._path
            raise RuntimeError(
                "Cannot find path for configuration repo, please checkout right git repo & run 'js9_config init' in that repo ")
        return self._path

    @property
    def base_class_config(self):
        return JSBaseClassConfig

    @property
    def base_class_configs(self):
        return JSBaseClassConfigs

    def configure(self, location="", instance="main"):
        """
        Will display a npyscreen form to edit the configuration
        """
        sc = self.get_for_location(location=location, instance=instance)
        sc.configure()
        sc.save()
        return sc

    def update(self, location, instance="main", updatedict={}):
        """
        update the configuration by giving a dictionnary. The configuration will
        be updated with the value of updatedict
        """
        sc = self.get_for_location(location=location, instance=instance)
        sc.data = updatedict
        sc.save()
        return sc

    def _get_for_obj(self, factoryclassobj, template, ui=None, instance="main", data={}):
        """
        return a secret config
        """
        if not hasattr(factoryclassobj, '__jslocation__') or factoryclassobj.__jslocation__ is None or factoryclassobj.__jslocation__ is "":
            raise RuntimeError(
                "__jslocation__ has not been set on class %s" % factoryclassobj.__class__)
        location = factoryclassobj.__jslocation__
        key = "%s_%s" % (location, instance)

        if ui == None:
            ui = j.tools.formbuilder.baseclass_get()

        if key not in self._cache:
            sc = Config(instance=instance, location=location,
                        template=template, ui=ui, data=data)
            self._cache[key] = sc

        return self._cache[key]

    def get_for_location(self, location="", instance="main", data={}):
        """
        will look for jumpscale module on defined location
        and generate the config instance from there
        @RETURN config
        """
        if location == "" or location == None:
            if j.sal.fs.getcwd().startswith(self.path_configrepo):
                # means we are in subdir of current config  repo, so we can be
                # in location
                location = j.sal.fs.getBaseName(j.sal.fs.getcwd())
                if not location.startswith("j."):
                    raise RuntimeError(
                        "Cannot find location, are you in right directory? now in:%s" % j.sal.fs.getcwd())

        obj = eval(location)
        if obj._single_item:
            return obj.config
        else:
            return obj.get(instance=instance).config

    def get(self, location, template={}, instance="main", data={}, ui=None):
        """
        return a secret config
        """
        if location == "":
            raise RuntimeError("location cannot be empty")
        if instance == "" or instance == None:
            raise RuntimeError("instance cannot be empty")
        key = "%s_%s" % (location, instance)
        if key not in self._cache:
            sc = Config(instance=instance, location=location,
                        template=template, ui=ui, data=data)
            self._cache[key] = sc
        return self._cache[key]

    # should use config_update
    # def set(self, location, instance, config=None):
    #     """
    #     create a new config

    #     @param location: location of the client
    #     @param instance: instance name
    #     @param config: optional configuration to set.
    #     @type config: dict
    #     """
    #     # create the config directory and file, so we don't trigger the form
    #     # when creating a SercretConfig object
    #     path = j.sal.fs.joinPaths(j.tools.configmanager.path_configrepo, location, instance + '.toml')
    #     j.sal.fs.createDir(j.sal.fs.getParent(path))
    #     j.sal.fs.writeFile(path, "")

    #     jsclient_object = eval(location)

    #     sc = Config(instance=instance, jsclient_object=jsclient_object)
    #     if config is not None:
    #         sc.data = config
    #     sc.save()
    #     return sc

    def list(self, location):
        """
        list all the existing instance name for a location

        @return: list of instance name
        """
        instances = []

        root = j.sal.fs.joinPaths(self.path_configrepo, location)
        if not j.sal.fs.exists(root):
            return instances

        # jsclient_object = eval(location)

        for cfg_path in j.sal.fs.listFilesInDir(root):
            cfg_name = j.sal.fs.getBaseName(cfg_path)
            if cfg_name in ('.git', '.jsconfig'):
                continue
            # trim the extension
            instance_name = cfg_name.split(os.path.extsep)[0]
            instances.append(instance_name)
        return instances

    def delete(self, location, instance="*"):
        if instance != "*":
            path = j.sal.fs.joinPaths(
                j.tools.configmanager.path_configrepo, location, instance + '.toml')
            j.sal.fs.remove(path)
        else:
            path = j.sal.fs.joinPaths(
                j.tools.configmanager.path_configrepo, location)
            for item in j.sal.fs.listFilesInDir(path):
                j.sal.fs.remove(item)

    def init(self, path="", data={}):

        if self._findConfigDirParent(path, die=False) != None:
            return
        gitdir = "%s/.git" % path
        if not j.sal.fs.exists(gitdir) or not j.sal.fs.isDir(gitdir):
            raise RuntimeError("am not in root of git dir")

        j.sal.fs.touch("%s/.jsconfig" % path)

        self._path = path
        if data == None:
            j.tools.myconfig.configure()
        else:
            j.tools.myconfig.config.data = data
            j.tools.myconfig.config.save()

        return path

    def test(self):
        """
        js9 'j.tools.configmanager.test()'
        """

        tdir = "/tmp/tests/secretconfig"
        j.sal.fs.remove(tdir)
        j.sal.fs.createDir(tdir)
        j.sal.process.execute("cd %s && git init" % tdir)

        self._test_myconfig_singleitem()
        self._test_myconfig_multiitem()

        # j.sal.fs.remove(tdir)

    def _test_myconfig_singleitem(self):

        tdir = "/tmp/tests/secretconfig"
        tdir0 = "/tmp/tests/secretconfig"

        MYCONFIG = """
        fullname = "kristof@something"
        email = "kkk@kk.com"
        login_name = "dddd"
        ssh_key_name = "something"
        """
        data = j.data.serializer.toml.loads(MYCONFIG)

        self.init(path=tdir, data=data)

        j.tools.myconfig.config.data = data
        j.tools.myconfig.config.save()

        tdir = "/tmp/tests/secretconfig/j.tools.myconfig"
        # there should be 1 file
        assert len(j.sal.fs.listFilesInDir(tdir)) == 1

        # check that the saved data is ok
        assert j.data.serializer.toml.fancydumps(
            j.tools.myconfig.config.data) == j.data.serializer.toml.fancydumps(data)

        self.delete("j.tools.myconfig")  # should remove all
        assert len(j.sal.fs.listFilesInDir(tdir)) == 0

        j.tools.configmanager.reset()
        j.tools.myconfig.reset()  # will remove data from mem
        assert j.tools.myconfig.config._data == {
            'email': '', 'fullname': '', 'login_name': '', 'ssh_key_name': ''}
        assert j.tools.myconfig.config.data == {
            'email': '', 'fullname': '', 'login_name': '', 'ssh_key_name': ''}

        j.tools.myconfig.config.load()
        assert j.tools.myconfig.config.data == {
            'email': '', 'fullname': '', 'login_name': '', 'ssh_key_name': ''}
        j.tools.myconfig.config.data = data
        j.tools.myconfig.config.save()
        assert len(j.sal.fs.listFilesInDir(tdir)) == 1

        # clean the env
        j.tools.configmanager.reset()
        j.tools.myconfig.reset()
        j.tools.myconfig.config._data = {}
        assert j.data.serializer.toml.fancydumps(
            j.tools.myconfig.config.data) == j.data.serializer.toml.fancydumps(data)

        # clean the env
        j.tools.configmanager.reset()
        j.tools.myconfig.config.load()
        j.tools.myconfig.config.data = {"email": "someting@ree.com"}
        j.tools.myconfig.config.save()
        j.tools.configmanager.reset()

        assert j.tools.myconfig.config.data["email"] == "someting@ree.com"

        # delete
        self.delete("j.tools.myconfig", "main")
        assert len(j.sal.fs.listFilesInDir(tdir)) == 0
        assert len(j.sal.fs.listFilesInDir(tdir0)) == 1

    def _test_myconfig_multiitem(self):

        MYCONFIG = """
        name = ""
        addr = "192.168.1.1"
        port = 22
        clienttype = "ovh"
        active = true
        selected = true
        category = "me"
        description = "some descr"
        secretconfig_ = "my secret config"
        """
        data = j.data.serializer.toml.loads(MYCONFIG)

        for i in range(10):
            data["addr"] = "192.168.1.%s" % i
            data["name"] = "test%s" % i
            obj = j.tools.nodemgr.get("test%s" % i, data=data)

        # empty mem
        j.tools.configmanager.reset()
        j.tools.nodemgr.items = {}

        obj = j.tools.nodemgr.get("test5")
        assert obj.config._data["addr"] == "192.168.1.5"
        assert obj.config.data["addr"] == "192.168.1.5"
        # needs to be encrypted
        assert obj.config._data["secretconfig_"] != "my secret config"
        assert obj.config.data["secretconfig_"] == "my secret config"

        tdir = "/tmp/tests/secretconfig/j.tools.nodemgr"
        assert len(j.sal.fs.listFilesInDir(tdir)) == 10

        i = j.tools.nodemgr.get("test1")
        assert i.name == "test1"

        # j.tools.nodemgr.reset()
        # assert len(j.sal.fs.listFilesInDir(tdir))==0