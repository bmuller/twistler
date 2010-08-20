from nevow import flat, tags
from mako.runtime import supports_caller, Undefined

from nevow import flat, tags

## Undefined mako args should return empty strings
flat.registerFlattener(lambda o, ctx: "", Undefined)


@supports_caller
def form(context, action="", method="post"):
    context.write('<form action="%s" method="%s">' % (action, method))
    context['caller'].body()
    context.write("</form>")
    return ''


def maketag(context, tag, default, kwargs):
    default.update(kwargs)
    context.write(flat.flatten(tag(**default)))
    return ""


def submit(context, **kwargs):
    default = {'value': "Submit", 'type': "submit", 'id': "submit"}
    return maketag(context, tags.input, default, kwargs)


def text(context, **kwargs):
    default = {'size': "20", 'value': "", 'name': "text", 'type': "text"}
    return maketag(context, tags.input, default, kwargs)


def password(context, **kwargs):
    default = {'size': "20", 'value': "", 'name': "password", "type": "password"}
    return maketag(context, tags.input, default, kwargs)

