from enum import Enum

from pydantic_settings import BaseSettings


class Constants(str, Enum):
    TAOMININGPOOL_API_URL: str = "https://api.taopoolmining.com"


class AuthRoute:
    GET_NONCE: str = "/api/v1/auth/nonce"
    VERIFY_SIGNATURE: str = "/api/v1/auth/verify"
    CHECK_AUTH: str = "/api/v1/auth/checkAuth"


class DeveloperKeyRoute:
    CREATE_INVOICE: str = "/api/v1/invoice/create"
    GET_INVOICE: str = "/api/v1/invoice"
    GET_DEV_KEYS: str = "/api/v1/developer-key/get/list"


class PoolRoute:
    CREATE_POOL: str = "/api/v1/pool/create"
    GET_POOL_LIST: str = "/api/v1/pool/get/list"
    GET_POOL: str = "/api/v1/pool"


class ApiRoute(BaseSettings):
    auth: AuthRoute = AuthRoute()
    key: DeveloperKeyRoute = DeveloperKeyRoute()
    pool: PoolRoute = PoolRoute()


apiRoutes = ApiRoute()
