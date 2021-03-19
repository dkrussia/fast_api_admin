from pprint import pprint
from typing import TypeVar

from fastapi import FastAPI
from fastapi import APIRouter, Request, HTTPException, Depends, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, schema

from app.admin.crud.base import CRUDBase
from app.admin.schemas import user as user_schemas
from app.auth.crud.user_token import pwd_context
from app.auth.models import User
from core.database import Base
from fastapi_sqlalchemy import db

CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ModelType = TypeVar("ModelType", bound=Base)

admin_router = APIRouter()


class CRUDUser(CRUDBase):
    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        password = obj_in_data.pop('password')
        obj_in_data["hashed_password"] = pwd_context.hash(password)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.session.add(db_obj)
        db.session.commit()
        db.session.refresh(db_obj)
        return db_obj


crud_user_admin = CRUDUser(User)


def headers_form_schema(schema):
    headers = []
    for name, prop in schema.schema()['properties'].items():
        headers.append({"value": name, 'text': prop["title"], 'type': prop['type']})
    return headers


def create_list_endpoint(entity: str, crud: CRUDBase, request_schema: BaseModel, response_schema: BaseModel,
                         is_headers: bool):
    def list_endpoint(request: Request):
        result = {}

        if is_headers:
            headers = []
            json_schema = response_schema.schema()
            for field_name, values in json_schema["properties"].items():
                if field_name == entity and values['type'] == 'array':
                    if ref := values['items']['$ref'].split('#/definitions/')[1]:
                        schema_fields = json_schema['definitions'][ref]['properties']
                        for name, prop in schema_fields.items():
                            headers.append({"value": name, 'text': prop["title"], 'type': prop['type']})
            result.update({"headers": headers})

        items = response_schema.parse_obj({entity: crud.get_all()})
        result.update(items)
        return result

    return list_endpoint


def get_by_id_endpoint(entity: str, crud: CRUDBase, request_schema: BaseModel, response_schema: BaseModel,
                       is_headers: bool):
    def get_endpoint(request: Request, item_id: int):
        result = {}

        if is_headers:
            headers = headers_form_schema(response_schema)
            result.update({"headers": headers})

        item = response_schema.from_orm(crud.get(item_id))
        result.update({entity: item})

        return result

    return get_endpoint


def get_form_endpoint(entity: str, crud: CRUDBase, request_schema: BaseModel, response_schema: BaseModel,
                      is_headers: bool):
    def form_endpoint(request: Request):
        result = {}
        headers = headers_form_schema(response_schema)
        result.update({"headers": headers})
        return result

    return form_endpoint


def create_endpoint(entity: str, crud: CRUDBase, request_schema: BaseModel, response_schema: BaseModel,
                    is_headers: bool):
    def form_endpoint(request: Request, item: request_schema):
        item = crud.create(obj_in=item)
        item = response_schema.from_orm(item)
        return item

    return form_endpoint

def create_update_endpoint(entity: str, crud: CRUDBase, request_schema: BaseModel, response_schema: BaseModel,
                    is_headers: bool):
    def update_endpoint(request: Request, item_id: int, dict_item: request_schema):
        item = db.session.query(crud.model).get(item_id)
        item = crud.update(db_obj=item, obj_in=dict_item)
        item = response_schema.from_orm(item)
        return item
    return update_endpoint

def create_remove_endpoint(entity: str, crud: CRUDBase, request_schema: BaseModel, response_schema: BaseModel,
                    is_headers: bool):
    def remove_endpoint(request: Request, item_id: int):
        crud.remove(id=item_id)
        return Response(status_code=204)
    return remove_endpoint

entities = [
    {
        'entity': 'users',
        'crud': crud_user_admin,
        'endpoints':
            [
                {
                    'name': 'list',
                    'request_schema': None,
                    'response_schema': user_schemas.UserList,
                    'func': create_list_endpoint,
                    'method': 'get',
                    'is_headers': True
                },
                {
                    'name': 'get_by_id',
                    'request_schema': None,
                    'response_schema': user_schemas.User,
                    'func': get_by_id_endpoint,
                    'path': '/users/get/{item_id}',
                    'method': 'get',
                    'is_headers': True
                },
                {
                    'name': 'get_form',
                    'request_schema': None,
                    'response_schema': user_schemas.UserCreate,
                    'func': get_form_endpoint,
                    'path': '/users/form',
                    'method': 'get',
                    'is_headers': True
                },
                {
                    'name': 'create',
                    'request_schema': user_schemas.UserCreate,
                    'response_schema': user_schemas.User,
                    'func': create_endpoint,
                    'method': 'put',
                },
                {
                    'name': 'update',
                    'request_schema': user_schemas.UserUpdate,
                    'response_schema': user_schemas.User,
                    'func': create_update_endpoint,
                    'path': '/users/update/{item_id}',
                    'method': 'post',
                },
                {
                    'name': 'remove',
                    'request_schema': None,
                    'response_schema': None,
                    'func': create_remove_endpoint,
                    'path': '/users/remove/{item_id}',
                    'method': 'delete',
                }
            ]
    }
]


# 'get_multi': {
#
# },

def create_admin_endpoints(app: FastAPI):
    for entity in entities:
        for endpoint in entity['endpoints']:
            path = endpoint.get('path', None) or f'/{entity["entity"]}/{endpoint["name"]}'
            admin_router.add_api_route(
                path=path,
                endpoint=endpoint['func'](
                    entity=entity["entity"],
                    crud=entity['crud'],
                    request_schema=endpoint['request_schema'],
                    response_schema=endpoint['response_schema'],
                    is_headers=endpoint.get('is_headers', False)
                ),
                # response_model=endpoint['response_schema'],
                methods=[endpoint['method']]
            )

            app.include_router(admin_router, prefix='/admin')
