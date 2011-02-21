import sys, tempfile, warnings
import urllib, urlparse, cgi
if sys.version >= '2.7':
    from io import BytesIO as StringIO
else:
    from cStringIO import StringIO

from webob.headers import EnvironHeaders
from webob.acceptparse import accept_property, Accept, MIMEAccept, NilAccept, MIMENilAccept, NoAccept
from webob.multidict import TrackableMultiDict, MultiDict, UnicodeMultiDict, NestedMultiDict, NoVars
from webob.cachecontrol import CacheControl, serialize_cache_control
from webob.etag import etag_property, AnyETag, NoETag

from webob.descriptors import *
from webob.datetime_utils import *
from webob.cookies import Cookie

__all__ = ['BaseRequest', 'Request']

if sys.version >= '2.6':
    parse_qsl = urlparse.parse_qsl
else:
    parse_qsl = cgi.parse_qsl

class _NoDefault:
    def __repr__(self):
        return '(No Default)'
NoDefault = _NoDefault()


class BaseRequest(object):
    ## Options:
    unicode_errors = 'strict'
    decode_param_names = False
    ## The limit after which request bodies should be stored on disk
    ## if they are read in (under this, and the request body is stored
    ## in memory):
    request_body_tempfile_limit = 10*1024

    def __init__(self, environ=None, environ_getter=None, charset=NoDefault, unicode_errors=NoDefault,
                 decode_param_names=NoDefault, **kw):
        if environ_getter is not None:
            raise ValueError('The environ_getter argument is no longer '
                             'supported')
        if environ is None:
            raise TypeError("You must provide an environ arg")
        d = self.__dict__
        d['environ'] = environ
        if charset is not NoDefault:
            self.charset = charset
        cls = self.__class__
        if (isinstance(getattr(cls, 'charset', None), str)
            or hasattr(cls, 'default_charset')
        ):
            raise DeprecationWarning("The class attr [default_]charset is deprecated")
        if unicode_errors is not NoDefault:
            d['unicode_errors'] = unicode_errors
        if decode_param_names is not NoDefault:
            d['decode_param_names'] = decode_param_names
        if kw:
            my_class = self.__class__
            for name, value in kw.iteritems():
                if not hasattr(my_class, name):
                    raise TypeError("Unexpected keyword: %s=%r" % (name, value))
                setattr(self, name, value)

    def _body_file__get(self):
        """
        Access the body of the request (wsgi.input) as a file-like
        object.

        If you set this value, CONTENT_LENGTH will also be updated
        (either set to -1, 0 if you delete the attribute, or if you
        set the attribute to a string then the length of the string).
        """
        return self.environ['wsgi.input']
    def _body_file__set(self, value):
        if isinstance(value, str):
            length = len(value)
            value = StringIO(value)
        else:
            length = -1
        self.environ['wsgi.input'] = value
        self.environ['CONTENT_LENGTH'] = str(length)
    def _body_file__del(self):
        self.environ['wsgi.input'] = StringIO('')
        self.environ['CONTENT_LENGTH'] = '0'
    body_file = property(_body_file__get, _body_file__set, _body_file__del, doc=_body_file__get.__doc__)

    scheme = environ_getter('wsgi.url_scheme')
    method = environ_getter('REQUEST_METHOD')
    script_name = environ_getter('SCRIPT_NAME')
    path_info = environ_getter('PATH_INFO')
    content_length = converter(
        environ_getter('CONTENT_LENGTH', None, '14.13'),
        parse_int_safe, serialize_int, 'int')
    remote_user = environ_getter('REMOTE_USER', None)
    remote_addr = environ_getter('REMOTE_ADDR', None)
    query_string = environ_getter('QUERY_STRING', '')
    server_name = environ_getter('SERVER_NAME')
    server_port = converter(
        environ_getter('SERVER_PORT'),
        parse_int, serialize_int, 'int')

    uscript_name = upath_property('SCRIPT_NAME')
    upath_info = upath_property('PATH_INFO')


    def _content_type__get(self):
        """Return the content type, but leaving off any parameters (like
        charset, but also things like the type in ``application/atom+xml;
        type=entry``)

        If you set this property, you can include parameters, or if
        you don't include any parameters in the value then existing
        parameters will be preserved.
        """
        return self.environ.get('CONTENT_TYPE', '').split(';', 1)[0]
    def _content_type__set(self, value):
        if value is None:
            del self.content_type
            return
        value = str(value)
        if ';' not in value:
            content_type = self.environ.get('CONTENT_TYPE', '')
            if ';' in content_type:
                value += ';' + content_type.split(';', 1)[1]
        self.environ['CONTENT_TYPE'] = value
    def _content_type__del(self):
        if 'CONTENT_TYPE' in self.environ:
            del self.environ['CONTENT_TYPE']

    content_type = property(_content_type__get, _content_type__set, _content_type__del,
                            _content_type__get.__doc__)

    _charset_cache = (None, None)

    def _charset__get(self):
        """Get the charset of the request.

        If the request was sent with a charset parameter on the
        Content-Type, that will be used.  Otherwise if there is a
        default charset (set during construction, or as a class
        attribute) that will be returned.  Otherwise None.

        Setting this property after request instantiation will always
        update Content-Type.  Deleting the property updates the
        Content-Type to remove any charset parameter (if none exists,
        then deleting the property will do nothing, and there will be
        no error).
        """
        content_type = self.environ.get('CONTENT_TYPE', '')
        cached_ctype, cached_charset = self._charset_cache
        if cached_ctype == content_type:
            return cached_charset
        charset_match = CHARSET_RE.search(content_type)
        if charset_match:
            result = charset_match.group(1).strip('"').strip()
        else:
            result = 'UTF-8'
        self._charset_cache = (content_type, result)
        return result
    def _charset__set(self, charset):
        if charset is None or charset == '':
            del self.charset
            return
        charset = str(charset)
        content_type = self.environ.get('CONTENT_TYPE', '')
        charset_match = CHARSET_RE.search(self.environ.get('CONTENT_TYPE', ''))
        if charset_match:
            content_type = content_type[:charset_match.start(1)] + charset + content_type[charset_match.end(1):]
        # comma to separate params? there's nothing like that in RFCs AFAICT
        #elif ';' in content_type:
        #    content_type += ', charset="%s"' % charset
        else:
            content_type += '; charset="%s"' % charset
        self.environ['CONTENT_TYPE'] = content_type
    def _charset__del(self):
        new_content_type = CHARSET_RE.sub('', self.environ.get('CONTENT_TYPE', ''))
        new_content_type = new_content_type.rstrip().rstrip(';').rstrip(',')
        self.environ['CONTENT_TYPE'] = new_content_type

    charset = property(_charset__get, _charset__set, _charset__del,
                       _charset__get.__doc__)

    _headers = None

    def _headers__get(self):
        """
        All the request headers as a case-insensitive dictionary-like
        object.
        """
        if self._headers is None:
            self._headers = EnvironHeaders(self.environ)
        return self._headers

    def _headers__set(self, value):
        self.headers.clear()
        self.headers.update(value)

    headers = property(_headers__get, _headers__set, doc=_headers__get.__doc__)

    @property
    def host_url(self):
        """
        The URL through the host (no path)
        """
        e = self.environ
        url = e['wsgi.url_scheme'] + '://'
        if e.get('HTTP_HOST'):
            host = e['HTTP_HOST']
            if ':' in host:
                host, port = host.split(':', 1)
            else:

                port = None
        else:
            host = e['SERVER_NAME']
            port = e['SERVER_PORT']
        if self.environ['wsgi.url_scheme'] == 'https':
            if port == '443':
                port = None
        elif self.environ['wsgi.url_scheme'] == 'http':
            if port == '80':
                port = None
        url += host
        if port:
            url += ':%s' % port
        return url

    @property
    def application_url(self):
        """
        The URL including SCRIPT_NAME (no PATH_INFO or query string)
        """
        return self.host_url + urllib.quote(self.environ.get('SCRIPT_NAME', ''))

    @property
    def path_url(self):
        """
        The URL including SCRIPT_NAME and PATH_INFO, but not QUERY_STRING
        """
        return self.application_url + urllib.quote(self.environ.get('PATH_INFO', ''))

    @property
    def path(self):
        """
        The path of the request, without host or query string
        """
        return urllib.quote(self.script_name) + urllib.quote(self.path_info)

    @property
    def path_qs(self):
        """
        The path of the request, without host but with query string
        """
        path = self.path
        qs = self.environ.get('QUERY_STRING')
        if qs:
            path += '?' + qs
        return path

    @property
    def url(self):
        """
        The full request URL, including QUERY_STRING
        """
        url = self.path_url
        if self.environ.get('QUERY_STRING'):
            url += '?' + self.environ['QUERY_STRING']
        return url


    def relative_url(self, other_url, to_application=False):
        """
        Resolve other_url relative to the request URL.

        If ``to_application`` is True, then resolve it relative to the
        URL with only SCRIPT_NAME
        """
        if to_application:
            url = self.application_url
            if not url.endswith('/'):
                url += '/'
        else:
            url = self.path_url
        return urlparse.urljoin(url, other_url)

    def path_info_pop(self, pattern=None):
        """
        'Pops' off the next segment of PATH_INFO, pushing it onto
        SCRIPT_NAME, and returning the popped segment.  Returns None if
        there is nothing left on PATH_INFO.

        Does not return ``''`` when there's an empty segment (like
        ``/path//path``); these segments are just ignored.

        Optional ``pattern`` argument is a regexp to match the return value
        before returning. If there is no match, no changes are made to the
        request and None is returned.
        """
        path = self.path_info
        if not path:
            return None
        slashes = ''
        while path.startswith('/'):
            slashes += '/'
            path = path[1:]
        idx = path.find('/')
        if idx == -1:
            idx = len(path)
        r = path[:idx]
        if pattern is None or re.match(pattern, r):
            self.script_name += slashes + r
            self.path_info = path[idx:]
            return r

    def path_info_peek(self):
        """
        Returns the next segment on PATH_INFO, or None if there is no
        next segment.  Doesn't modify the environment.
        """
        path = self.path_info
        if not path:
            return None
        path = path.lstrip('/')
        return path.split('/', 1)[0]

    def _urlvars__get(self):
        """
        Return any *named* variables matched in the URL.

        Takes values from ``environ['wsgiorg.routing_args']``.
        Systems like ``routes`` set this value.
        """
        if 'paste.urlvars' in self.environ:
            return self.environ['paste.urlvars']
        elif 'wsgiorg.routing_args' in self.environ:
            return self.environ['wsgiorg.routing_args'][1]
        else:
            result = {}
            self.environ['wsgiorg.routing_args'] = ((), result)
            return result

    def _urlvars__set(self, value):
        environ = self.environ
        if 'wsgiorg.routing_args' in environ:
            environ['wsgiorg.routing_args'] = (environ['wsgiorg.routing_args'][0], value)
            if 'paste.urlvars' in environ:
                del environ['paste.urlvars']
        elif 'paste.urlvars' in environ:
            environ['paste.urlvars'] = value
        else:
            environ['wsgiorg.routing_args'] = ((), value)

    def _urlvars__del(self):
        if 'paste.urlvars' in self.environ:
            del self.environ['paste.urlvars']
        if 'wsgiorg.routing_args' in self.environ:
            if not self.environ['wsgiorg.routing_args'][0]:
                del self.environ['wsgiorg.routing_args']
            else:
                self.environ['wsgiorg.routing_args'] = (self.environ['wsgiorg.routing_args'][0], {})

    urlvars = property(_urlvars__get, _urlvars__set, _urlvars__del, doc=_urlvars__get.__doc__)

    def _urlargs__get(self):
        """
        Return any *positional* variables matched in the URL.

        Takes values from ``environ['wsgiorg.routing_args']``.
        Systems like ``routes`` set this value.
        """
        if 'wsgiorg.routing_args' in self.environ:
            return self.environ['wsgiorg.routing_args'][0]
        else:
            # Since you can't update this value in-place, we don't need
            # to set the key in the environment
            return ()

    def _urlargs__set(self, value):
        environ = self.environ
        if 'paste.urlvars' in environ:
            # Some overlap between this and wsgiorg.routing_args; we need
            # wsgiorg.routing_args to make this work
            routing_args = (value, environ.pop('paste.urlvars'))
        elif 'wsgiorg.routing_args' in environ:
            routing_args = (value, environ['wsgiorg.routing_args'][1])
        else:
            routing_args = (value, {})
        environ['wsgiorg.routing_args'] = routing_args

    def _urlargs__del(self):
        if 'wsgiorg.routing_args' in self.environ:
            if not self.environ['wsgiorg.routing_args'][1]:
                del self.environ['wsgiorg.routing_args']
            else:
                self.environ['wsgiorg.routing_args'] = ((), self.environ['wsgiorg.routing_args'][1])

    urlargs = property(_urlargs__get, _urlargs__set, _urlargs__del, _urlargs__get.__doc__)

    @property
    def is_xhr(self):
        """Returns a boolean if X-Requested-With is present and ``XMLHttpRequest``

        Note: this isn't set by every XMLHttpRequest request, it is
        only set if you are using a Javascript library that sets it
        (or you set the header yourself manually).  Currently
        Prototype and jQuery are known to set this header."""
        return self.environ.get('HTTP_X_REQUESTED_WITH', '') == 'XMLHttpRequest'

    def _host__get(self):
        """Host name provided in HTTP_HOST, with fall-back to SERVER_NAME"""
        if 'HTTP_HOST' in self.environ:
            return self.environ['HTTP_HOST']
        else:
            return '%(SERVER_NAME)s:%(SERVER_PORT)s' % self.environ
    def _host__set(self, value):
        self.environ['HTTP_HOST'] = value
    def _host__del(self):
        if 'HTTP_HOST' in self.environ:
            del self.environ['HTTP_HOST']
    host = property(_host__get, _host__set, _host__del, doc=_host__get.__doc__)

    def _body__get(self):
        """
        Return the content of the request body.
        """
        try:
            length = int(self.environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            return ''
        # maybe we should use .tell() before reading and then use it to seek back?
        body = self.body_file.read(length)
        try:
            self.body_file.seek(0)
        except (AttributeError, IOError):
            # AttributeError is thrown if body_file doesn't have a .seek method
            # IOError is thrown if body_file is stdin (or wrapped stdin)
            tempfile_limit = self.request_body_tempfile_limit
            if tempfile_limit and len(body) > tempfile_limit:
                fileobj = tempfile.TemporaryFile()
                fileobj.write(body)
                fileobj.seek(0)
            else:
                fileobj = StringIO(body)
            # We don't want/need to lose CONTENT_LENGTH here (as setting
            # self.body_file would do):
            self.environ['wsgi.input'] = fileobj
        return body

    def _body__set(self, value):
        if value is None:
            del self.body
            return
        if not isinstance(value, str):
            raise TypeError(
                "You can only set Request.body to a str (not %r)" % type(value))
        body_file = StringIO(value)
        self.body_file = body_file
        self.environ['CONTENT_LENGTH'] = str(len(value))

    def _body__del(self, value):
        del self.body_file

    body = property(_body__get, _body__set, _body__del, doc=_body__get.__doc__)


    @property
    def str_POST(self):
        """
        Return a MultiDict containing all the variables from a form
        request. Returns an empty dict-like object for non-form
        requests.

        Form requests are typically POST requests, however PUT requests
        with an appropriate Content-Type are also supported.
        """
        env = self.environ
        if self.method not in ('POST', 'PUT'):
            return NoVars('Not a form request')
        if 'webob._parsed_post_vars' in env:
            vars, body_file = env['webob._parsed_post_vars']
            if body_file is self.body_file:
                return vars
        # Paste compatibility:
        if 'paste.parsed_formvars' in env:
            # from paste.request.parse_formvars
            vars, body_file = env['paste.parsed_formvars']
            if body_file is self.body_file:
                # FIXME: is it okay that this isn't *our* MultiDict?
                return vars
        content_type = self.content_type
        if ';' in content_type:
            content_type = content_type.split(';', 1)[0]
        if (self.method == 'PUT' and not content_type) or \
                content_type not in ('', 'application/x-www-form-urlencoded',
                                     'multipart/form-data'):
            # Not an HTML form submission
            return NoVars('Not an HTML form submission (Content-Type: %s)'
                          % content_type)
        fs_environ = env.copy()
        # FieldStorage assumes a default CONTENT_LENGTH of -1, but a
        # default of 0 is better:
        fs_environ.setdefault('CONTENT_LENGTH', '0')
        fs_environ['QUERY_STRING'] = ''
        fs = cgi.FieldStorage(fp=self.body_file,
                              environ=fs_environ,
                              keep_blank_values=True)
        vars = MultiDict.from_fieldstorage(fs)
        FakeCGIBody.update_environ(env, vars)
        env['webob._parsed_post_vars'] = (vars, self.body_file)
        return vars



    @property
    def POST(self):
        """
        Like ``.str_POST``, but may decode values and keys
        """
        vars = self.str_POST
        vars = UnicodeMultiDict(vars, encoding=self.charset,
                                errors=self.unicode_errors,
                                decode_keys=self.decode_param_names)
        return vars



    @property
    def str_GET(self):
        """
        Return a MultiDict containing all the variables from the
        QUERY_STRING.
        """
        env = self.environ
        source = env.get('QUERY_STRING', '')
        if 'webob._parsed_query_vars' in env:
            vars, qs = env['webob._parsed_query_vars']
            if qs == source:
                return vars
        if not source:
            vars = TrackableMultiDict(__tracker=self._update_get, __name='GET')
        else:
            vars = TrackableMultiDict(parse_qsl(
                source, keep_blank_values=True,
                strict_parsing=False), __tracker=self._update_get, __name='GET')
        env['webob._parsed_query_vars'] = (vars, source)
        return vars

    def _update_get(self, vars, key=None, value=None):
        env = self.environ
        qs = urllib.urlencode(vars.items())
        env['QUERY_STRING'] = qs
        env['webob._parsed_query_vars'] = (vars, qs)


    @property
    def GET(self):
        """
        Like ``.str_GET``, but may decode values and keys
        """
        vars = self.str_GET
        vars = UnicodeMultiDict(vars, encoding=self.charset,
                                errors=self.unicode_errors,
                                decode_keys=self.decode_param_names)
        return vars


    str_postvars = deprecated_property(str_POST, 'str_postvars', 'use str_POST instead')
    postvars = deprecated_property(POST, 'postvars', 'use POST instead')
    str_queryvars = deprecated_property(str_GET, 'str_queryvars', 'use str_GET instead')
    queryvars = deprecated_property(GET, 'queryvars', 'use GET instead')


    @property
    def str_params(self):
        """
        A dictionary-like object containing both the parameters from
        the query string and request body.
        """
        return NestedMultiDict(self.str_GET, self.str_POST)


    @property
    def params(self):
        """
        Like ``.str_params``, but may decode values and keys
        """
        params = self.str_params
        params = UnicodeMultiDict(params, encoding=self.charset,
                                  errors=self.unicode_errors,
                                  decode_keys=self.decode_param_names)
        return params


    @property
    def str_cookies(self):
        """
        Return a *plain* dictionary of cookies as found in the request.
        """
        env = self.environ
        source = env.get('HTTP_COOKIE', '')
        if 'webob._parsed_cookies' in env:
            vars, var_source = env['webob._parsed_cookies']
            if var_source == source:
                return vars
        vars = {}
        if source:
            cookies = Cookie(source)
            for name in cookies:
                value = cookies[name].value
                if value is None:
                    continue
                vars[name] = value
        env['webob._parsed_cookies'] = (vars, source)
        return vars

    @property
    def cookies(self):
        """
        Like ``.str_cookies``, but may decode values and keys
        """
        vars = self.str_cookies
        vars = UnicodeMultiDict(vars, encoding=self.charset,
                                errors=self.unicode_errors,
                                decode_keys=self.decode_param_names)
        return vars


    def copy(self):
        """
        Copy the request and environment object.

        This only does a shallow copy, except of wsgi.input
        """
        env = self.environ.copy()
        new_req = self.__class__(env)
        new_req.copy_body()
        return new_req

    def copy_get(self):
        """
        Copies the request and environment object, but turning this request
        into a GET along the way.  If this was a POST request (or any other verb)
        then it becomes GET, and the request body is thrown away.
        """
        env = self.environ.copy()
        env['wsgi.input'] = StringIO('')
        env['CONTENT_LENGTH'] = '0'
        if 'CONTENT_TYPE' in env:
            del env['CONTENT_TYPE']
        env['REQUEST_METHOD'] = 'GET'
        return self.__class__(env)

    def make_body_seekable(self):
        """
        This forces ``environ['wsgi.input']`` to be seekable.  That
        is, if it doesn't have a `seek` method already, the content is
        copied into a StringIO or temporary file.

        The choice to copy to StringIO is made from
        ``self.request_body_tempfile_limit``
        """
        input = self.body_file
        if hasattr(input, 'seek'):
            # It has a seek method, so we don't need to do anything
            return
        self.copy_body()

    def copy_body(self):
        """
        Copies the body, in cases where it might be shared with
        another request object and that is not desired.

        This copies the body in-place, either into a StringIO object
        or a temporary file.
        """
        length = self.content_length
        if length == 0:
            # No real need to copy this, but of course it is free
            self.body_file = StringIO('')
            return
        tempfile_limit = self.request_body_tempfile_limit
        body = None
        input = self.body_file
        if hasattr(input, 'seek'):
            # Just in case someone has read parts of the body already
            ## FIXME: Should we use .tell() to try to put the body
            ## back to its previous position?
            input.seek(0)
        if length in (-1, None):
            body = self.body
            length = len(body)
            self.content_length = length
        if tempfile_limit and length > tempfile_limit:
            fileobj = tempfile.TemporaryFile()
            if body is None:
                while length:
                    data = input.read(min(length, 4096))
                    fileobj.write(data)
                    length -= len(data)
            else:
                fileobj.write(body)
            fileobj.seek(0)
        else:
            if body is None:
                body = input.read(length)
            fileobj = StringIO(body)
        self.body_file = fileobj

    def remove_conditional_headers(self, remove_encoding=True, remove_range=True,
                                        remove_match=True, remove_modified=True):
        """
        Remove headers that make the request conditional.

        These headers can cause the response to be 304 Not Modified,
        which in some cases you may not want to be possible.

        This does not remove headers like If-Match, which are used for
        conflict detection.
        """
        check_keys = []
        if remove_range:
            check_keys += ['HTTP_IF_RANGE', 'HTTP_RANGE']
        if remove_match:
            check_keys.append('HTTP_IF_NONE_MATCH')
        if remove_modified:
            check_keys.append('HTTP_IF_MODIFIED_SINCE')
        if remove_encoding:
            check_keys.append('HTTP_ACCEPT_ENCODING')

        for key in check_keys:
            if key in self.environ:
                del self.environ[key]


    accept = accept_property('Accept', '14.1', MIMEAccept, MIMENilAccept, 'MIME Accept')
    accept_charset = accept_property('Accept-Charset', '14.2')
    accept_encoding = accept_property('Accept-Encoding', '14.3', NilClass=NoAccept)
    accept_language = accept_property('Accept-Language', '14.4')

    authorization = converter(
        environ_getter('HTTP_AUTHORIZATION', None, '14.8'),
        parse_auth, serialize_auth,
    )


    def _cache_control__get(self):
        """
        Get/set/modify the Cache-Control header (section `14.9
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.9>`_)
        """
        env = self.environ
        value = env.get('HTTP_CACHE_CONTROL', '')
        cache_header, cache_obj = env.get('webob._cache_control', (None, None))
        if cache_obj is not None and cache_header == value:
            return cache_obj
        cache_obj = CacheControl.parse(value, updates_to=self._update_cache_control, type='request')
        env['webob._cache_control'] = (value, cache_obj)
        return cache_obj

    def _cache_control__set(self, value):
        env = self.environ
        value = value or ''
        if isinstance(value, dict):
            value = CacheControl(value, type='request')
        if isinstance(value, CacheControl):
            str_value = str(value)
            env['HTTP_CACHE_CONTROL'] = str_value
            env['webob._cache_control'] = (str_value, value)
        else:
            env['HTTP_CACHE_CONTROL'] = str(value)
            env['webob._cache_control'] = (None, None)

    def _cache_control__del(self, value):
        env = self.environ
        if 'HTTP_CACHE_CONTROL' in env:
            del env['HTTP_CACHE_CONTROL']
        if 'webob._cache_control' in env:
            del env['webob._cache_control']

    def _update_cache_control(self, prop_dict):
        self.environ['HTTP_CACHE_CONTROL'] = serialize_cache_control(prop_dict)

    cache_control = property(_cache_control__get, _cache_control__set, _cache_control__del, doc=_cache_control__get.__doc__)


    if_match = etag_property('HTTP_IF_MATCH', AnyETag, '14.24')
    if_none_match = etag_property('HTTP_IF_NONE_MATCH', NoETag, '14.26')

    date = converter_date(environ_getter('HTTP_DATE', None, '14.8'))
    if_modified_since = converter_date(environ_getter('HTTP_IF_MODIFIED_SINCE', None, '14.25'))
    if_unmodified_since = converter_date(environ_getter('HTTP_IF_UNMODIFIED_SINCE', None, '14.28'))
    if_range = converter(
        environ_getter('HTTP_IF_RANGE', None, '14.27'),
        parse_if_range, serialize_if_range, 'IfRange object')


    max_forwards = converter(
        environ_getter('HTTP_MAX_FORWARDS', None, '14.31'),
        parse_int, serialize_int, 'int')

    pragma = environ_getter('HTTP_PRAGMA', None, '14.32')

    range = converter(
        environ_getter('HTTP_RANGE', None, '14.35'),
        parse_range, serialize_range, 'Range object')

    referer = environ_getter('HTTP_REFERER', None, '14.36')
    referrer = referer

    user_agent = environ_getter('HTTP_USER_AGENT', None, '14.43')

    def __repr__(self):
        try:
            name = '%s %s' % (self.method, self.url)
        except KeyError:
            name = '(invalid WSGI environ)'
        msg = '<%s at 0x%x %s>' % (
            self.__class__.__name__,
            abs(id(self)), name)
        return msg

    def __str__(self, skip_body=False):
        url = self.url
        host = self.host_url
        assert url.startswith(host)
        url = url[len(host):]
        parts = ['%s %s %s' % (self.method, url, self.environ['SERVER_PROTOCOL'])]
        self.headers.setdefault('Host', self.host)
        parts += map('%s: %s'.__mod__, sorted(self.headers.items()))
        if not skip_body and self.method in ('PUT', 'POST'):
            parts += ['', self.body]
        return '\n'.join(parts)

    @classmethod
    def from_file(cls, fp):
        """Reads a request from a file-like object (it must implement
        ``.read(size)`` and ``.readline()``).

        It will read up to the end of the request, not the end of the
        file.

        This reads the request as represented by ``str(req)``; it may
        not read every valid HTTP request properly."""
        kw = {}
        headers = kw['headers'] = {}
        environ = kw['environ'] = {}
        start_line = fp.readline()
        try:
            method, resource, http_version = start_line.split(None, 2)
        except ValueError:
            raise ValueError('Bad HTTP request line: %r' % start_line)
        method = method.upper()
        environ['SERVER_PROTOCOL'] = http_version
        kw['method'] = method
        kw['path'] = resource
        last_header = None
        while 1:
            line = fp.readline()
            line = line.strip()
            if not line:
                # end of headers
                break
            if line and (line.startswith(' ') or line.startswith('\t')):
                # Continuation
                assert last_header is not None
                headers[last_header] = '%s, %s' % (headers[last_header], line.strip())
            else:
                try:
                    last_header, value = line.split(':', 1)
                except ValueError:
                    raise ValueError('Bad header line: %r' % line)
                last_header = last_header.lower()
                if last_header in headers:
                    headers[last_header] = '%s, %s' % (headers[last_header], value.strip())
                else:
                    headers[last_header] = value.strip()
        content_length = int(headers.get('content-length', 0))
        kw['body'] = fp.read(content_length)
        return cls.blank(**kw)

    def call_application(self, application, catch_exc_info=False):
        """
        Call the given WSGI application, returning ``(status_string,
        headerlist, app_iter)``

        Be sure to call ``app_iter.close()`` if it's there.

        If catch_exc_info is true, then returns ``(status_string,
        headerlist, app_iter, exc_info)``, where the fourth item may
        be None, but won't be if there was an exception.  If you don't
        do this and there was an exception, the exception will be
        raised directly.
        """
        captured = []
        output = []
        def start_response(status, headers, exc_info=None):
            if exc_info is not None and not catch_exc_info:
                raise exc_info[0], exc_info[1], exc_info[2]
            captured[:] = [status, headers, exc_info]
            return output.append
        app_iter = application(self.environ, start_response)
        if output or not captured:
            try:
                output.extend(app_iter)
            finally:
                if hasattr(app_iter, 'close'):
                    app_iter.close()
            app_iter = output
        if catch_exc_info:
            return (captured[0], captured[1], app_iter, captured[2])
        else:
            return (captured[0], captured[1], app_iter)

    # Will be filled in later:
    ResponseClass = None

    def get_response(self, application, catch_exc_info=False):
        """
        Like ``.call_application(application)``, except returns a
        response object with ``.status``, ``.headers``, and ``.body``
        attributes.

        This will use ``self.ResponseClass`` to figure out the class
        of the response object to return.
        """
        if catch_exc_info:
            status, headers, app_iter, exc_info = self.call_application(
                application, catch_exc_info=True)
            del exc_info
        else:
            status, headers, app_iter = self.call_application(
                application, catch_exc_info=False)
        return self.ResponseClass(
            status=status, headerlist=list(headers), app_iter=app_iter,
            request=self)

    @classmethod
    def blank(cls, path, environ=None, base_url=None, headers=None, POST=None, **kw):
        """
        Create a blank request environ (and Request wrapper) with the
        given path (path should be urlencoded), and any keys from
        environ.

        The path will become path_info, with any query string split
        off and used.

        All necessary keys will be added to the environ, but the
        values you pass in will take precedence.  If you pass in
        base_url then wsgi.url_scheme, HTTP_HOST, and SCRIPT_NAME will
        be filled in from that value.

        Any extra keyword will be passed to ``__init__`` (e.g.,
        ``decode_param_names``).
        """
        env = environ_from_url(path)
        environ_add_POST(env, POST)
        if base_url:
            scheme, netloc, path, query, fragment = urlparse.urlsplit(base_url)
            if query or fragment:
                raise ValueError(
                    "base_url (%r) cannot have a query or fragment"
                    % base_url)
            if scheme:
                env['wsgi.url_scheme'] = scheme
            if netloc:
                if ':' not in netloc:
                    if scheme == 'http':
                        netloc += ':80'
                    elif scheme == 'https':
                        netloc += ':443'
                    else:
                        raise ValueError(
                            "Unknown scheme: %r" % scheme)
                host, port = netloc.split(':', 1)
                env['SERVER_PORT'] = port
                env['SERVER_NAME'] = host
                env['HTTP_HOST'] = netloc
            if path:
                env['SCRIPT_NAME'] = urllib.unquote(path)
        if environ:
            env.update(environ)
        obj = cls(env, **kw)
        if headers is not None:
            obj.headers.update(headers)
        return obj


def environ_from_url(path):
    if SCHEME_RE.search(path):
        scheme, netloc, path, qs, fragment = urlparse.urlsplit(path)
        if fragment:
            raise TypeError("Path cannot contain a fragment (%r)" % fragment)
        if qs:
            path += '?' + qs
        if ':' not in netloc:
            if scheme == 'http':
                netloc += ':80'
            elif scheme == 'https':
                netloc += ':443'
            else:
                raise TypeError("Unknown scheme: %r" % scheme)
    else:
        scheme = 'http'
        netloc = 'localhost:80'
    if path and '?' in path:
        path_info, query_string = path.split('?', 1)
        path_info = urllib.unquote(path_info)
    else:
        path_info = urllib.unquote(path)
        query_string = ''
    env = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': path_info or '',
        'QUERY_STRING': query_string,
        'SERVER_NAME': netloc.split(':')[0],
        'SERVER_PORT': netloc.split(':')[1],
        'HTTP_HOST': netloc,
        'SERVER_PROTOCOL': 'HTTP/1.0',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': scheme,
        'wsgi.input': StringIO(''),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    return env

def environ_add_POST(env, data):
    if data is None:
        return
    env['REQUEST_METHOD'] = 'POST'
    if hasattr(data, 'items'):
        data = data.items()
    if not isinstance(data, str):
        data = urllib.urlencode(data)
    env['wsgi.input'] = StringIO(data)
    env['CONTENT_LENGTH'] = str(len(data))
    env['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'


class AdhocAttrMixin(object):
    def __setattr__(self, attr, value, DEFAULT=object()):
        ## FIXME: I don't know why I need this guard (though experimentation says I do)
        if getattr(self.__class__, attr, DEFAULT) is not DEFAULT or attr.startswith('_'):
            object.__setattr__(self, attr, value)
        else:
            self.environ.setdefault('webob.adhoc_attrs', {})[attr] = value

    def __getattr__(self, attr, DEFAULT=object()):
        ## FIXME: I don't know why I need this guard (though experimentation says I do)
        if getattr(self.__class__, attr, DEFAULT) is not DEFAULT:
            return object.__getattribute__(self, attr)
        try:
            return self.environ['webob.adhoc_attrs'][attr]
        except KeyError:
            raise AttributeError(attr)

    def __delattr__(self, attr, DEFAULT=object()):
        ## FIXME: I don't know why I need this guard (though experimentation says I do)
        if getattr(self.__class__, attr, DEFAULT) is not DEFAULT:
            return object.__delattr__(self, attr)
        try:
            del self.environ['webob.adhoc_attrs'][attr]
        except KeyError:
            raise AttributeError(attr)


class Request(AdhocAttrMixin, BaseRequest):
    """ The default request implementation """



#########################
## Helper classes and monkeypatching
#########################


def _cgi_FieldStorage__repr__patch(self):
    """ monkey patch for FieldStorage.__repr__

    Unbelievably, the default __repr__ on FieldStorage reads
    the entire file content instead of being sane about it.
    This is a simple replacement that doesn't do that
    """
    if self.file:
        return "FieldStorage(%r, %r)" % (self.name, self.filename)
    return "FieldStorage(%r, %r, %r)" % (self.name, self.filename, self.value)

cgi.FieldStorage.__repr__ = _cgi_FieldStorage__repr__patch

class FakeCGIBody(object):
    def __init__(self, vars, content_type):
        self.vars = vars
        self.content_type = content_type
        self._body = None
        self.position = 0

    def seek(self, pos):
        ## FIXME: this isn't strictly necessary, but it's important
        ## when modifying POST parameters.  I wish there was a better
        ## way to do this.
        self._body = None
        self.position = pos

    def tell(self):
        return self.position

    def read(self, size=-1):
        body = self._get_body()
        if size == -1:
            v = body[self.position:]
            self.position = len(body)
            return v
        else:
            v = body[self.position:self.position+size]
            self.position = min(len(body), self.position+size)
            return v

    def _get_body(self):
        if self._body is None:
            if self.content_type.lower().startswith('application/x-www-form-urlencoded'):
                self._body = urllib.urlencode(self.vars.items())
            elif self.content_type.lower().startswith('multipart/form-data'):
                self._body = _encode_multipart(self.vars, self.content_type)
            else:
                assert 0, ('Bad content type: %r' % self.content_type)
        return self._body

    def readline(self, size=None):
        # We ignore size, but allow it to be hinted
        rest = self._get_body()[self.position:]
        next = rest.find('\r\n')
        if next == -1:
            return self.read()
        self.position += next+2
        return rest[:next+2]

    def readlines(self, hint=None):
        # Again, allow hint but ignore
        body = self._get_body()
        rest = body[self.position:]
        self.position = len(body)
        result = []
        while 1:
            next = rest.find('\r\n')
            if next == -1:
                result.append(rest)
                break
            result.append(rest[:next+2])
            rest = rest[next+2:]
        return result

    def __iter__(self):
        return iter(self.readlines())

    def __repr__(self):
        inner = repr(self.vars)
        if len(inner) > 20:
            inner = inner[:15] + '...' + inner[-5:]
        if self.position:
            inner += ' at position %s' % self.position
        return '<%s at 0x%x viewing %s>' % (
            self.__class__.__name__,
            abs(id(self)), inner)

    @classmethod
    def update_environ(cls, environ, vars):
        obj = cls(vars, environ.get('CONTENT_TYPE', 'application/x-www-form-urlencoded'))
        environ['CONTENT_LENGTH'] = '-1'
        environ['wsgi.input'] = obj


def _encode_multipart(vars, content_type):
    """Encode a multipart request body into a string"""
    boundary_match = re.search(r'boundary=([^ ]+)', content_type, re.I)
    if not boundary_match:
        raise ValueError('Content-type: %r does not contain boundary' % content_type)
    boundary = boundary_match.group(1).strip('"')
    lines = []
    for name, value in vars.iteritems():
        lines.append('--%s' % boundary)
        ## FIXME: encode the name like this?
        assert name is not None, 'Value associated with no name: %r' % value
        disp = 'Content-Disposition: form-data; name="%s"' % urllib.quote(name)
        if getattr(value, 'filename', None):
            disp += '; filename="%s"' % urllib.quote(value.filename)
        lines.append(disp)
        ## FIXME: should handle value.disposition_options
        if getattr(value, 'type', None):
            ct = 'Content-type: %s' % value.type
            if value.type_options:
                ct += ''.join(['; %s="%s"' % (ct_name, urllib.quote(ct_value))
                               for ct_name, ct_value in sorted(value.type_options.items())])
            lines.append(ct)
        lines.append('')
        if hasattr(value, 'value'):
            lines.append(value.value)
        else:
            lines.append(value)
    lines.append('--%s--' % boundary)
    return '\r\n'.join(lines)
