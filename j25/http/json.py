from j25.exceptions import HttpExceptions as HTTP
from j25.utils.JSONCustomEncoder import JSONCustomEncoder
import simplejson

def json_formatter(result, request, session, appPackage, controllerInstance):
    #do processing if needed (template rendering potentially?)
    data = render_json(result)
    headers = controllerInstance.get_headers()
    headers['Content-Type'] = 'application/json'
    headers['Content-Length'] = len(data)
    headers['Cache-Control'] = 'no-cache'
    # HTTP.OK in certain cases
    if request.method == 'POST':
        controllerInstance.set_response_code(HTTP.CREATED)
    else:
        controllerInstance.set_response_code(HTTP.OK)
    return data

def render_json(obj):
    data = simplejson.dumps(obj, cls=JSONCustomEncoder, ensure_ascii=False)
    return data