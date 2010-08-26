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


def maketag(context, tag, default, kwargs, content=None):
    default.update(kwargs)
    if content is not None:
        t = tag(**default)[content]
    else:
        t = tag(**default)
    context.write(flat.flatten(t))
    return ""


def submit(context, **kwargs):
    default = {'value': "Submit", 'type': "submit", 'id': "submit"}
    return maketag(context, tags.input, default, kwargs)


def checkbox(context, **kwargs):
    default = {'type': "checkbox", 'id': "checkbox", "value": '1'}
    if kwargs.has_key('checked') and kwargs['checked'] in [1, '1', 'checked']:
        kwargs['checked'] = "checked"
    elif kwargs.has_key('checked'):
        del kwargs['checked']
    return maketag(context, tags.input, default, kwargs)


def text(context, **kwargs):
    default = {'size': "20", 'value': "", 'name': "text", 'type': "text"}
    return maketag(context, tags.input, default, kwargs)


def textarea(context, **kwargs):
    default = {'cols': "60", 'rows': "10", 'name': "textarea"}
    content = kwargs['value']
    kwargs['value'] = ""
    return maketag(context, tags.textarea, default, kwargs, content)


def password(context, **kwargs):
    default = {'size': "20", 'value': "", 'name': "password", "type": "password"}
    return maketag(context, tags.input, default, kwargs)


def link(context, **kwargs):
    content = kwargs.get('value', kwargs.get('href', ""))
    return maketag(context, tags.a, {}, kwargs, content)
