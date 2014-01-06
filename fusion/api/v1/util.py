from functools import wraps

def tenant_local(handler):
    '''
    Decorator for a handler method that sets the correct tenant_id in the
    request context.
    '''
    @wraps(handler)
    def handle_stack_method(controller, req, tenant_id, **kwargs):
        req.context.tenant_id = tenant_id
        return handler(controller, req, **kwargs)

    return handle_stack_method
