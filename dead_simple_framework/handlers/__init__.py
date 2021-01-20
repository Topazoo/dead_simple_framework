''' Custom handlers for special routes '''

from .default import DefaultRouteHandler
from .permissions import PermissionsRouteHandler, DefaultPermissionsRouteHandler, Permissions
from ..api.main import RouteHandler
from .login import LoginRouteHandler
from .users import UserRouteHandler
