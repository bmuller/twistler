from twisted.application import service, internet
from twisted.application import internet
from twisted.application import service

from twisted.enterprise import adbapi
from nevow import appserver, rend, tags, loaders

class AppController(rend.Page):
    addSlash = True
    controllers = {}

    def splitPath(self, segments):
        action = 'index'
        if len(segments) > 1:
            action = segments[1]
            
        id = None
        if len(segments) > 2:
            id = segments[2]

        return (segments[0], action, id)
    

    def locateChild(self, ctx, segments):
        if len(segments) == 0:
            return rend.NotFound

        contname, action, id = self.splitPath(segments)
        if not AppController.controllers.has_key(contname):
            return rend.NotFound
        contklass = AppController.controllers[contname]
        controller = contklass(action, id)

        if hasattr(controller, action) and callable(getattr(controller, action)):
            return getattr(controller, action).__call__(ctx, id), ""
            
        return rend.NotFound



class BaseController(rend.Page):
    addSlash = True

    def __init__(self, action, id):
        self.action = action
        self.id = id
        

    @classmethod
    def addController(klass, *paths):
        name = klass.__name__[:-10].lower()
        AppController.controllers[name] = klass        
        for path in paths:
            AppController.controllers[path] = klass
        


class TestController(BaseController):
    def index(self, ctx, id):
        return loaders.xmlfile('test.xml').load(ctx)[0]

    def show(self, ctx, id):
        return tags.html[tags.body["id is: %s" % str(id)]]

    
TestController.addController('test', 'blah')


application = service.Application('pubsubin')
site = appserver.NevowSite(AppController())
webServer = internet.TCPServer(8080, site)
webServer.setServiceParent(application)

