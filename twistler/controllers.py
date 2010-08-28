from nevow import rend, inevow, static
from twisted.web.util import Redirect
from twisted.python import log
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
        cname = BaseController.controllerName(klass)
        viewDirs = viewDirs + [cname]

        templateDirs = []
        for viewDir in viewDirs:
            # make this path: <viewsDir>/<viewDir which is controllername>
            templateDirs.append(os.path.join(self.viewsDir, viewDir))
        templateDirs = filter(os.path.exists, templateDirs)
        if self.templateCacheDir is not None:
            cachedir = os.path.join(self.templateCacheDir, cname)
        else:
            cachedir = None
        klass.template_lookup = TemplateLookup(directories=templateDirs, module_directory=cachedir)
        

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
        return contklass(self, ctx, segments)._render()



class BaseController(rend.Page):
    def __init__(self, appcontroller, ctx, segments):
        self.ctx = ctx
        self.segments = segments
        self.rootPath = segments[0]
        self.appcontroller = appcontroller
        
        self.action = 'index'
        if len(segments) > 1 and segments[1] != '':
            self.action = segments[1]
            
        self.id = None
        if len(segments) > 2:
            self.id = segments[2]
        self.params = {'id': self.id}


    @classmethod
    def isValidAction(klass, action):
        return not action.startswith('_') and not action in dir(BaseController)


    @classmethod
    def controllerName(klass, controllerKlass):
        name = controllerKlass.__name__
        if not name.endswith('Controller'):
            raise RuntimeError, "%s is impropperly named: name should have 'Controller' suffix" % name
        return name[:-10].lower()


    @property
    def session(self):
        return inevow.ISession(self.ctx)


    def addParams(self, *names):
        for name in names:
            if not self.params.has_key(name):
                self.params[name] = self.ctx.arg(name, '')


    def getDefaultViewArgs(self):
        return {}


    def getViewArgs(self, givenArgs=None):
        # start with default of whatever our params are set to
        args = self.params
        args['message'] = self.message
        for key in ['segments', 'rootPath', 'action', 'id']:
            # don't overwrite something already set in the params
            if not args.has_key(key):
                args[key] = getattr(self, key)
        args['controller'] = self
            
        # allow defaults to be easily set
        defaults = self.getDefaultViewArgs()
        defaults.update(args)
        
        if givenArgs is not None:
            defaults.update(givenArgs)
            
        return defaults


    def view(self, args=None, action=None):
        # set the last args used, so if this template calls include
        # all of the same args will be available
        self.lastargs = self.getViewArgs(args)
        return self.include(action)
        

    def include(self, action=None):
        """
        This can be called from templates
        """
        action = action or self.action
        temp = None        

        try:
            logargs = (self.__class__.__name__, self.__class__.template_lookup.directories, action)
            log.msg("%s: looking in %s for view %s" % logargs)
            temp = self.__class__.template_lookup.get_template("%s.mako" % action)
        except TemplateLookupException:
            return rend.NotFound

        return temp.render(**self.lastargs)


    def _render(self):
        if not BaseController.isValidAction(self.action):
            return rend.NotFound
        
        func = getattr(self, self.action, None)
        if func is not None and callable(func):
            result = func(self.ctx)
        else:
            result = self.view()

        # after rendering, we can reset our session message value if necessary
        self._resetMessage()
        
        if result != rend.NotFound:
            return result, ""
        return result


    def _resetMessage(self):
        if not hasattr(self.session, 'message'):
            self.session.message = ""
        elif self.session.message == "":
            pass
        elif self.session.message == getattr(self.session, '_message', ''):
            self.session.message = self.session._message = ""
        else:
            self.session._message = self.session.message        


    def path(self, action=None, clear_query=True, **kwargs):
        controller = kwargs.pop('controller', None)
        id = kwargs.pop('id', None)

        # only when neither action nor controller are explicitly
        # specified do we pull the id from the current path
        if action is None and controller is None:
            id = id or self.id
            
        controller = controller or self.rootPath
        action = action or self.action
        
        path = self.request.URLPath().child(controller).child(action).child(id)
        # clear all query args except the ones passed in
        if clear_query:
            path._querylist = []
        for name, value in kwargs.items():
            path = path.add(name, value)
        return path


    @property
    def request(self):
        return inevow.IRequest(self.ctx)


    def redirect(self, url):
        return Redirect(url)


    @property
    def message(self):
        return getattr(self.session, 'message', '')


    @message.setter
    def message(self, value):
        self.session.message = value


class StaticController(BaseController):
    PATH = "."
    KWARGS = {}
    
    def _render(self):
       f = static.File(self.__class__.PATH, **self.__class__.KWARGS)
       if len(self.segments) > 1:
           return f.locateChild(self.ctx, self.segments[1:])
       self.action = ""
       return self.redirect(self.path()), ""

        
NotFound = rend.NotFound
