class HttpResponse(object):
    @classmethod
    def get_http_response(cls):
        tup = _MAPPINGS[cls]
        return "%s %s" % (tup[0], tup[1])  

class OK(HttpResponse): pass

class CREATED(HttpResponse): pass

class ACCEPTED(HttpResponse): pass

_MAPPINGS = {OK:       (200, 'OK'),
             CREATED:  (201, 'Created'),
             ACCEPTED: (202, 'Accepted')
             }