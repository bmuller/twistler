from twisted.application import service, internet

from twistler.controllers import BaseController, AppController

from nevow import tags, loaders, appserver

class TestController(BaseController):
    def index(self, ctx, id):
        return loaders.stan(tags.html[tags.body["index id is: %s" % str(id)]]).load(ctx)[0]

    def show(self, ctx, id):
        return loaders.stan(tags.html[tags.body["show id is: %s" % str(id)]]).load(ctx)[0]

    
TestController.addController('test', 'blah', '')


application = service.Application('pubsubin')
site = appserver.NevowSite(AppController())
webServer = internet.TCPServer(8080, site)
webServer.setServiceParent(application)

