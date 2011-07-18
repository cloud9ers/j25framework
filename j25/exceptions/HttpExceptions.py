#The client's request was successfully received, understood, and accepted
OK = '200 OK'
CREATED = '201 Created'
ACCEPTED = '202 Accepted'
NO_CONTENT = '204 No Content'

MOVED = '301 Moved Permanently'
#Client Error
BAD_REQUEST = '400 Bad Request'
UNAUTHORIZED = '401 Unauthorized'
PAYMENT_REQUIRED = '402 Payment Required'
FORBIDDEN = '403 Forbidden'
NOTFOUND= '404 Not Found'
METHOD_NOT_ALLOWED = '405 Method Not Allowed'
REQUEST_TIMEOUT = '408 Request Timeout'
GONE = '410 Gone'
# Server Error
INTERNAL_SERVER_ERROR = '500 Internal Server Error'
NOTIMPLEMENTED = '501 Not Implemented'
SERVICE_UNAVAILABLE = '503 Service Unavailable'

class HTTPResponse(Exception):
    '''
    The parent of all HTTP Exceptions
    '''
    status = OK

class Http204(HTTPResponse):
    '''
    The server has fulfilled the request but does not need to return an entity-body.
    '''
    status = NO_CONTENT
    
class Http301(HTTPResponse):
    '''
    HTTP 301 means Moved Permanently.
    The requested resource has been assigned a new permanent URI 
    and any future references to this resource SHOULD use one of the returned URIs. 
    Clients with link editing capabilities ought to automatically re-link references to the Request-URI
    to one or more of the new references returned by the server, where possible. 
    This response is cacheable unless indicated otherwise.
    The new permanent URI SHOULD be given by the Location field in the response. 
    Unless the request method was HEAD, the entity of the response SHOULD contain a short hypertext note with a hyperlink to the new URI(s).
    If the 301 status code is received in response to a request other than GET or HEAD,
    the user agent MUST NOT automatically redirect the request unless it can be confirmed by the user,
    since this might change the conditions under which the request was issued. 
    '''
    status = MOVED
    
class Http400(HTTPResponse):
    '''
    HTTP 400 means Bad Request.
    The request could not be understood by the server due to malformed syntax. 
    The client SHOULD NOT repeat the request without modifications. 
    '''
    status = BAD_REQUEST
    
class Http401(HTTPResponse):
    '''
    HTTP 401 means Unauthorized.
    The request requires user authentication. 
    The response MUST include a WWW-Authenticate header field containing a challenge
    applicable to the requested resource. 
    The client MAY repeat the request with a suitable Authorization header field. 
    If the request already included Authorization credentials,
    then the 401 response indicates that authorization has been refused for those credentials.
    '''
    status = UNAUTHORIZED
  
class Http404(HTTPResponse):
    '''
    HTTP 404 means Not Found.
    The server has not found anything matching the Request-URI. 
    No indication is given of whether the condition is temporary or permanent. 
    The 410 (Gone) status code SHOULD be used if the server knows,
    through some internally configurable mechanism, 
    that an old resource is permanently unavailable and has no forwarding address.
    This status code is commonly used when the server does not wish to reveal exactly why the request has been refused, or when no other response is applicable. 
    '''
    status = NOTFOUND

class Http403(HTTPResponse):
    '''
    HTTP 403 means Forbidden.
    403 Forbidden is a HTTP status code returned by a web server when a user agent requests a resource that the server does not allow them to. 
    '''
    status = FORBIDDEN
    
class Http410(HTTPResponse):
    '''
    HTTP 410 means GONE.
    The requested resource is no longer available at the server and no forwarding address is known. 
    This condition is expected to be considered permanent.
    Clients with link editing capabilities SHOULD delete references to the Request-URI after user approval.
    If the server does not know, or has no facility to determine, whether or not the condition is permanent, 
    the status code 404 (Not Found) SHOULD be used instead. This response is cachable unless indicated otherwise.
    The 410 response is primarily intended to assist the task of web maintenance by notifying the recipient that
    the resource is intentionally unavailable and that the server owners desire that remote links to that resource be removed.
    Such an event is common for limited-time, promotional services and for resources belonging to individuals no longer working
    at the server's site. It is not necessary to mark all permanently unavailable resources as "gone" 
    or to keep the mark for any length of time -- that is left to the discretion of the server owner. 
    '''
    status = GONE
    
class Http500(HTTPResponse):
    '''
    HTTP 500 means Internal Server Error.
    The server encountered an unexpected condition which prevented it from fulfilling the request. 
    '''
    status = INTERNAL_SERVER_ERROR
    
HttpNoContent = Http204
HttpMovedPermanently = Http301  
HttpBadRequest = Http400
HttpUnauthorized = Http401 
httpNotFound = Http404
HttpGone = Http410
HttpInternalError = Http500