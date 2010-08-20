from nevow import rend, inevow, static
from twisted.web.util import Redirect
from mako.lookup import TemplateLookup
from mako.exceptions import TemplateLookupException
import os

class AppController(rend.Page):
    addSlash = True
    
    def __init__(self, viewsDir="views", templateCacheDir=None):
        """
        Don't cache by default.
        """
        # this is the root of our views
        self.viewsDir = viewsDir
        self.templateCacheDir = templateCacheDir
        self.controllers = {}
        

    def addViewDirs(self, klass, viewDirs):
        viewDirs = viewDirs or []
        # try a view directory with the same name as this controller
        viewDirs.append(BaseController.controllerName(klass))

        templateDirs = []
        for viewDir in viewDirs:
            # make this path: <viewsDir>/<viewDir which is controllername>
            templateDirs.append(os.path.join(self.viewsDir, viewDir))
        templateDirs = filter(os.path.exists, templateDirs)
        klass.template_lookup = TemplateLookup(directories=templateDirs, module_directory=self.templateCacheDir)
        

    def addController(self, klass, paths=None, viewDirs=None):
        """
        viewDir will be relative to the viewsDir param in the constructor.
        """
        name = BaseController.controllerName(klass)
        self.controllers[name] = klass        
        paths = paths or []
        for path in paths:
            self.controllers[path] = klass

        # Add view directory
        self.addViewDirs(klass, viewDirs)


    def locateChild(self, ctx, segments):
        if len(segments) == 0:
            return rend.NotFound

        # rootpath is most often the controller name
        rootpath = segments[0]
        if not self.controllers.has_key(rootpath):
            return rend.NotFound
        
        contklass = self.controllers[rootpath]
        return contklass(ctx, segments)._render()



class BaseController:
    def __init__(self, ctx, segments):
        self.ctx = ctx
        self.segments = segments
        self.name = BaseController.controllerName(self.__class__)
        self.rootPath = segments[0]
        
        self.action = 'index'
        if len(segments) > 1 and segments[1] != '':
            self.action = segments[1]
            
        self.id = None
        if len(segments) > 2:
            self.id = segments[2]


    @classmethod
    def controllerName(klass, controllerKlass):
        name = controllerKlass.__name__
        if not name.endswith('Controller'):
            raise RuntimeError, "%s is impropperly named: name should have 'Controller' suffix" % name
        return name[:-10].lower()


    @property
    def session(self):
        return inevow.ISession(self.ctx)


    def getDefaultViewArgs(self):
        return {}


    def getViewArgs(self, givenArgs=None):
        args = {}
        for key in ['segments', 'name', 'rootPath', 'action', 'id']:
            args[key] = getattr(self, key)
            
        # allow defaults to be easily set
        args.update(self.getDefaultViewArgs())
        
        if givenArgs is not None:
            args.update(givenArgs)
            
        return args


    def view(self, args=None, name=None):
        name = name or self.action
        temp = None        

        try:
            temp = self.__class__.template_lookup.get_template("%s.mako" % name)
        except TemplateLookupException:
            return rend.NotFound
        
        args = self.getViewArgs(args)
        return temp.render(**args)


    def _render(self):
        func = getattr(self, self.action, None)
        if func is not None and callable(func):
            result = func(self.ctx)
        else:
            result = self.view()

        if result != rend.NotFound:
            return result, ""
        return result


    def path(self, action=None, controller=None, id=None):
        controller = controller or self.rootPath
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

        
