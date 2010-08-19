from nevow import rend, inevow, static
from twisted.web.util import Redirect
from mako.lookup import TemplateLookup
import os

class AppController(rend.Page):
    addSlash = True
    
    def __init__(self, viewsDir="views", templateCacheDir=None):
        """
        Don't cache by default.
        """
        # this is the root of our views
        self.viewsDir = viewsDir
        self.templateDirs = [viewsDir]
        self.templateCacheDir = templateCacheDir
        self.addViewDir('layout')
        self.controllers = {}
        

    def addViewDir(self, dir):
        self.templateDirs.append(os.path.join(self.viewsDir, dir))
        self.tlookup = TemplateLookup(directories=self.templateDirs, module_directory=self.templateCacheDir)
        

    def addController(self, klass, paths=None, viewDir=None):
        """
        viewDir will be relative to the viewsDir param in the constructor.
        """
        name = klass.__name__[:-10].lower()
        self.controllers[name] = klass        
        paths = paths or []
        for path in paths:
            self.controllers[path] = klass

        # Add view directory
        viewDir = viewDir or name
        self.addViewDir(viewDir)


    def locateChild(self, ctx, segments):
        if len(segments) == 0:
            return rend.NotFound

        contname = segments[0]
        if not self.controllers.has_key(contname):
            return rend.NotFound
        
        contklass = self.controllers[contname]
        return contklass(ctx, segments, self)._render()



class BaseController:
    def __init__(self, ctx, segments, tlookup):
        self.ctx = ctx
        self.segments = segments
        self.name = segments[0]
        self.tlookup = tlookup
        
        self.action = 'index'
        if len(segments) > 1 and segments[1] != '':
            self.action = segments[1]
            
        self.id = None
        if len(segments) > 2:
            self.id = segments[2]


    def view(self, args, name=None):
        name = name or self.action
        temp = self.tlookup.get_template("%s.phtml" % name)
        return temp.render(**args)
        

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

        
