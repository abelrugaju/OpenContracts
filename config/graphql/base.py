import inspect
import logging
import traceback
from abc import ABC

import django.db.models
import graphene
from graphene import Int
from graphene.relay import Node
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required
from graphql_relay import from_global_id, to_global_id

from config.graphql.custom_connections import (
    CustomDjangoFilterConnectionField,
    CustomPermissionFilteredConnection,
)
from opencontractserver.shared.resolvers import resolve_single_oc_model_from_id
from opencontractserver.types.enums import PermissionTypes
from opencontractserver.utils.permissioning import (
    set_permissions_for_obj_to_user,
    user_has_permission_for_obj,
)

logger = logging.getLogger(__name__)


class OpenContractsNode(Node):
    class Meta:
        name = "Node"

    @classmethod
    def get_node_from_global_id(cls, info, global_id, only_type=None):

        _type, _id = from_global_id(global_id)

        graphene_type = info.schema.get_type(_type)
        if graphene_type is None:
            raise Exception(f'Relay Node "{_type}" not found in schema')

        graphene_type = graphene_type.graphene_type
        logger.info(f"Graphene type: {graphene_type}")

        if only_type:
            assert (
                graphene_type == only_type
            ), f"Must receive a {only_type._meta.name} id."

        # We make sure the ObjectType implements the "Node" interface, parent of
        # this subclass of Node. Using inspect module: https://www.geeksforgeeks.org/inspect-module-in-python/
        if inspect.getmro(cls)[1] not in graphene_type._meta.interfaces:
            raise Exception(
                f'ObjectType "{_type}" does not implement the "{super()}" interface.'
            )

        # Here's where we replace the base Graphene Relay get_node code with a custom
        # resolver that is permission-aware... it was kind of a pain in the @ss to figure this out...
        return resolve_single_oc_model_from_id(
            model_type=graphene_type._meta.model,
            user=info.context.user,
            graphql_id=global_id,
        )


class CountableConnection(CustomPermissionFilteredConnection):
    class Meta:
        abstract = True

    total_count = Int()
    edge_count = Int()

    def resolve_total_count(root, info, **kwargs):
        return root.length

    def resolve_edge_count(root, info, **kwargs):
        return len(root.edges)


class DRFDeletion(graphene.Mutation):
    class IOSettings(ABC):
        lookup_field = "id"

    class Arguments(ABC):
        id = graphene.String(required=False)

    ok = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @login_required
    def mutate(cls, root, info, *args, **kwargs):

        ok = False

        id = from_global_id(kwargs.get(cls.IOSettings.lookup_field, None))[1]
        obj = cls.IOSettings.model.objects.get(pk=id)

        # if there's a user lock
        if hasattr(obj, "user_lock") and obj.user_lock is not None:
            if info.context.user.id == obj.user_lock_id:
                raise PermissionError(
                    f"Specified object is locked by {info.context.user.username}. Cannot be "
                    f"deleted by another user."
                )

        # NOTE - we are explicitly ALLOWING deletion of something that's been locked by the backend. If an important
        # or processing job goes sour, we want a frontend user to be able to intervene and delete it without
        # needing someone to drop in the admin dash.

        # Check user permissions
        if not user_has_permission_for_obj(
            info.context.user,
            obj,
            PermissionTypes.DELETE,
            include_group_permissions=True,
        ):
            raise PermissionError(
                "You do no have sufficient permissions to delete requested object"
            )

        obj.delete()
        ok = True
        message = "Success!"

        return cls(ok=ok, message=message)


class DRFMutation(graphene.Mutation):
    class IOSettings(ABC):
        pk_fields: list[str | int] = []
        lookup_field = "id"
        model: django.db.models.Model = None
        graphene_model: DjangoObjectType = None
        serializer = None

    class Arguments(ABC):
        pass

    ok = graphene.Boolean()
    message = graphene.String()
    obj_id = graphene.ID()

    @classmethod
    @login_required
    def mutate(cls, root, info, *args, **kwargs):

        ok = False
        obj_id = None

        try:
            logger.info("Test if context has user")
            if info.context.user:
                logger.info(f"User id: {info.context.user.id}")
                # We're using the DRF Serializers to build data and edit / save objs
                # We want to pass an ID into the creator field, not the user obj
                kwargs["creator"] = info.context.user.id
            else:
                logger.info("No user")
                raise ValueError("No user in this request...")

            # logger.info(f"DRFMutation - kwargs: {kwargs}")
            serializer = cls.IOSettings.serializer

            if hasattr(cls.IOSettings, "pk_fields"):
                for pk_field in cls.IOSettings.pk_fields:
                    if pk_field in kwargs:
                        if isinstance(kwargs[pk_field], list):
                            pk_value = []
                            for global_id in kwargs[pk_field]:
                                pk_value.append(
                                    from_global_id(kwargs.get(global_id, None))[1]
                                )
                        else:
                            logger.info(f"pk field is: {kwargs.get(pk_field, None)}")
                            pk_value = from_global_id(kwargs.get(pk_field, None))[1]
                        kwargs[pk_field] = pk_value

            if cls.IOSettings.lookup_field in kwargs:
                logger.info("Lookup_field specified - update")
                obj = cls.IOSettings.model.objects.get(
                    pk=from_global_id(kwargs.get(cls.IOSettings.lookup_field, None))[1]
                )

                logger.info(f"Retrieved obj: {obj}")

                # Check the object isn't locked by another user
                if hasattr(obj, "user_lock") and obj.user_lock is not None:
                    if info.context.user.id == obj.user_lock_id:
                        raise PermissionError(
                            f"Specified object is locked by {info.context.user.username}. Cannot be "
                            f"updated / edited by another user."
                        )

                # Check that the object hasn't been locked by the backend
                if hasattr(obj, "backend_lock") and obj.backend_lock:
                    raise PermissionError(
                        "This object has been locked by the backend for processing. You cannot edit "
                        "it at the moment."
                    )

                # Check that the user has update permissions
                if not user_has_permission_for_obj(
                    info.context.user,
                    obj,
                    PermissionTypes.UPDATE,
                    include_group_permissions=True,
                ):
                    raise PermissionError(
                        "You do not have permission to modify this object"
                    )

                obj_serializer = serializer(obj, data=kwargs, partial=True)
                obj_serializer.is_valid(raise_exception=True)
                obj_serializer.save()
                ok = True
                message = "Success"
                obj_id = to_global_id(
                    cls.IOSettings.graphene_model.__class__.__name__, obj.id
                )
                logger.info("Succeeded updating obj")

            else:
                # logger.info(
                #     f"No lookup field specified... create obj with kwargs: {kwargs}"
                # )
                obj_serializer = serializer(data=kwargs)
                obj_serializer.is_valid(raise_exception=True)
                obj = obj_serializer.save()
                # logger.info(f"Created obj for: {info.context.user}")

                # If we created new obj... give user proper permissions
                set_permissions_for_obj_to_user(
                    info.context.user, obj, [PermissionTypes.ALL]
                )
                # logger.info("Permissioned obj")

                ok = True
                message = "Success"
                obj_id = to_global_id(
                    cls.IOSettings.graphene_model.__class__.__name__, obj.id
                )

        except Exception as e:
            logger.error(traceback.format_exc())
            message = f"Mutation failed due to error: {e}"

        return cls(ok=ok, message=message, obj_id=obj_id)


class CustomDjangoObjectType(DjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        model=None,
        registry=None,
        skip_registry=False,
        only_fields=None,
        fields=None,
        exclude_fields=None,
        exclude=None,
        filter_fields=None,
        filterset_class=None,
        connection=None,
        connection_class=None,
        use_connection=None,
        interfaces=(),
        convert_choices_to_enum=None,
        _meta=None,
        **options,
    ):
        if filter_fields is not None and filterset_class is None:
            from graphene_django.filter.utils import get_filterset_class

            filterset_class = get_filterset_class(model, filter_fields)

        super().__init_subclass_with_meta__(
            model=model,
            registry=registry,
            skip_registry=skip_registry,
            only_fields=only_fields,
            fields=fields,
            exclude_fields=exclude_fields,
            exclude=exclude,
            filter_fields=filter_fields,
            filterset_class=filterset_class,
            connection=connection,
            connection_class=connection_class,
            use_connection=use_connection,
            interfaces=interfaces,
            convert_choices_to_enum=convert_choices_to_enum,
            _meta=_meta,
            **options,
        )

        # Replace any DjangoFilterConnectionField with CustomDjangoFilterConnectionField
        if cls._meta.fields:
            for name, field in cls._meta.fields.items():
                if isinstance(field, DjangoFilterConnectionField):
                    new_field = CustomDjangoFilterConnectionField(
                        type(field.node),
                        filters=field.filterset_class.Meta.fields
                        if field.filterset_class
                        else None,
                        filterset_class=field.filterset_class,
                    )
                    cls._meta.fields[name] = new_field

    @classmethod
    def get_node(cls, info, id):
        return super().get_node(info, id)
