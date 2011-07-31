# -*- encoding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1312106592.5951951
_template_filename=u'/home/medo/workspace/j25framework/test/web/testproject/apps/kalamna/templates/Controller1/test_format.html'
_template_uri=u'Controller1/test_format.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
_exports = []


def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        format = context.get('format', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'<h1>welcome ')
        __M_writer(unicode(format))
        __M_writer(u'</h1>')
        return ''
    finally:
        context.caller_stack._pop_frame()


