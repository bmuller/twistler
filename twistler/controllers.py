from nevow import rend

class AppController(rend.Page):
    addSlash = True
    controllers = {}

    def splitPath(self, segments):
        action = 'index'
        if len(segments) > 1 and segments[1] != '':
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
    def __init__(self, action, id):
        self.action = action
        self.id = id
        

    @classmethod
    def addController(klass, *paths):
        name = klass.__name__[:-10].lower()
        AppController.controllers[name] = klass        
        for path in paths:
            AppController.controllers[path] = klass
