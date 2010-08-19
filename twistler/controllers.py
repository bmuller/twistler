from nevow import rend, inevow, static
from twisted.web.util import Redirect


class AppController(rend.Page):
    addSlash = True
    controllers = {}   

    @classmethod
    def addController(appklass, klass, paths=None):
        name = klass.__name__[:-10].lower()
        AppController.controllers[name] = klass        
        paths = paths or []
        for path in paths:
            AppController.controllers[path] = klass


    def locateChild(self, ctx, segments):
        if len(segments) == 0:
            return rend.NotFound

        contname = segments[0]
        if not AppController.controllers.has_key(contname):
            return rend.NotFound
        
        contklass = AppController.controllers[contname]
        return contklass(ctx, segments)._render()



class BaseController:
    def __init__(self, ctx, segments):
        self.ctx = ctx
        self.segments = segments
        self.name = segments[0]
        
        self.action = 'index'
        if len(segments) > 1 and segments[1] != '':
            self.action = segments[1]
            
        self.id = None
        if len(segments) > 2:
            self.id = segments[2]


    def _render(self):
        func = getattr(self, self.action, None)
        if func is not None and callable(func):
            return func(self.ctx, self.id), ""
        return rend.NotFound


    def path(self, controller=None, action=None, id=None):
        controller = controller or self.name
        action = action or self.action
        
        url = inevow.IRequest(self.ctx).URLPath().child(controller).child(action)
        if id is not None:
            url = url.child(str(id))
            
        return url
        


class StaticController(BaseController):
    PATH = "."
    KWARGS = {}
    
    def _render(self):
       f = static.File(self.__class__.PATH, **self.__class__.KWARGS)
       if len(self.segments) > 1:
           return f.locateChild(self.ctx, self.segments[1:])
       self.action = ""
       return Redirect(self.path()), ""

        
