from src.core.app_enum import UserType

min_permissions = {
    "/Resource/predictResourceRate": UserType.CUSTOMER,
    "/Resource/getResourceRate": UserType.CUSTOMER,
    "/Task/createTask": UserType.CUSTOMER,
    "/Task/getTask": UserType.CUSTOMER,
    "/User/createUser": UserType.ADMIN,
    "/User/createUserWithKey": UserType.ADMIN,
    "/Key/createKey": UserType.ADMIN,
    "/Key/deleteKeyByOrderId": UserType.ADMIN,
    "/Key/getKey": UserType.ADMIN,
    "/Key/updateKeyPeriod": UserType.ADMIN,
    "/Key/updateKeyFrequency": UserType.ADMIN,
}
