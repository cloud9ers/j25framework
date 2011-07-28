APP_ROOT = '/kalamna'

def router(map):
    #map.connect('master', '/{controller}/{action}') # master app example
    with map.submapper(path_prefix=APP_ROOT) as m:
        m.connect("home", "/", controller="main", action="index")
        m.connect(None, "/{controller}/get_user_by_name/{name}", action="get_user_by_name", format="json")
        m.connect(None, "/{controller}/get_user_by_id/{id}", action="get_user_by_id", format="json")
        m.connect(None, "/{controller}/get_users", action="get_users", format="json")
        m.connect(None, "/{controller}/test", action="test_post", format="json", conditions=dict(method="POST"))
        m.connect(None, "/{controller}/test", action="test_get", format="json", conditions=dict(method="GET"))
#        m.connect(None, "/{controller}/test_format{.format}", action="test_format", format="json")
#        m.connect(None, "/{controller}/test_format", action="test_format", format="json")
#        m.connect(None, "/{controller}/test_format", action="test_format")
        m.connect(None, "/{controller}/{action}/{id}")
        m.connect(None, "/{controller}/{action}")
        # ADD CUSTOM ROUTES HERE
        #m.connect(None, "/error/{action}/{id}", controller="error")
        #m.connect("home", "/{controller}/{action}/{id}", controller="batates")
