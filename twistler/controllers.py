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
        cachedir = os.path.join(self.templateCacheDir, cname)
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
        return contklass(ctx, segments)._render()



class BaseController(rend.Page):
    def __init__(self, ctx, segments):
        self.ctx = ctx
        self.segments = segments
        self.rootPath = segments[0]
        
        self.action = 'index'
        if len(segments) > 1 and segments[1] != '':
            self.action = segments[1]
            
        self.id = None
        if len(segments) > 2:
            self.id = segments[2]
        self.params = {}


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
        log.msg("args by default: %s" % str(args))
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


    def path(self, action=None, controller=None, id=None):
        controller = controller or self.rootPath
        action = action or self.action
        
        url = inevow.IRequest(self.ctx).URLPath().child(controller).child(action)
        if id is not None:
            url = url.child(str(id))
            
        return url


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

        
