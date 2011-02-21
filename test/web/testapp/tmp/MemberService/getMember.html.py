# -*- encoding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1295555733.466783
_template_filename=u'/home/arefaey/devel/ws/c9prod/applicationserver/test/web/testapp/templates/MemberService/getMember.html'
_template_uri=u'MemberService/getMember.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='ascii'
_exports = []


def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        password = context.get('password', UNDEFINED)
        name = context.get('name', UNDEFINED)
        _id = context.get('_id', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'<html><head>Mermber Service</head><body>ID:')
        __M_writer(unicode(_id))
        __M_writer(u'-name:')
        __M_writer(unicode(name))
        __M_writer(u'-password:')
        __M_writer(unicode(password))
        __M_writer(u'</body></html>')
        return ''
    finally:
        context.caller_stack._pop_frame()


