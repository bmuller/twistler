from twisted.application import service, internet
from twisted.application import internet
from twisted.application import service

from twisted.enterprise import adbapi
from nevow import appserver, rend, tags, loaders

class AppController(rend.Page):
    addSlash = True
    controllers = {}

    def locateChild(self, ctx, segments):
        if len(segments) == 0:
            return rend.NotFound
        
        contname = segments[0]
        if not BaseController.controllers.has_key(contname):
            return rend.NotFound
        cont = BaseController.controllers[contname]

        cont.action = 'index'
        if len(segments) > 1:
            cont.action = segments[1]
            
        cont.id = None
        if len(segments) > 2:
            cont.id = segments[2]

        if hasattr(cont, action) and callable(getattr(cont, action)):
            return getattr(cont, cont.action).__call__(ctx, cont.id), ""
        return rend.NotFound


class BaseController(rend.Page):
    viewsdir = "."
    viewcache = {}

    def __init__(self, name):
        self.name = name
        

    @classmethod
    def addController(klass):
        name = klass.__name__[:-10].lower()
        if not AppController.controllers.has_key(name):
            AppController.controllers[name] = klass(name)


    def view(self, action=None):
        action = action or self.action
        klass = self.__class__
        path = os.path.join(klass.viewsdir, self.name, action)
        if os.path.exists(path):
            klass.viewcache[path] = loaders.xmlfile(
        
        
class TestController(BaseController):
    def index(self, ctx, id):
        return loaders.xmlfile('test.xml').load(ctx)[0]

TestController.addController()


application = service.Application('pubsubin')
site = appserver.NevowSite(TestController())
webServer = internet.TCPServer(8080, site)
webServer.setServiceParent(application)

