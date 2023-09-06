from traceback import format_exc

from ttcore.bottle import make_public
from ttcore.utils import mkdir
from ttcore.peewee import query_search
from peewee import IntegrityError
from playhouse.shortcuts import model_to_dict

peewee2type = {
    "<class 'peewee.DateTimeField'>": "datetime",
    "<class 'peewee.DateField'>": "date",
    "<class 'peewee.TimeField'>": "time",
    "<class 'peewee.TimestampField'>": "timestamp",
    "<class 'peewee.IntegerField'>": "int",
    "<class 'peewee.TextField'>": "str",
    "<class 'peewee.BooleanField'>": "bool",
    "<class 'peewee.AutoField'>": "int",
    "<class 'peewee.CharField'>": "str",
    "<class 'peewee.BigIntegerField'>": "bigint",
    "<class 'peewee.SmallIntegerField'>": "small",
    "<class 'peewee.DecimalField'>": "decimal",
}


class AdminModel:
    search_fields = ["pid"]
    required_fields = ["pid"]
    non_edit_fields = ["pid", "id"]
    upload_fields = []

    def __init__(self, model, data_path=None):
        self.model = model
        self.model_name = self.model.__name__
        self.model_fields = list(self.model._meta.fields.keys())
        self.search_fields = self.get_existing_fields(self.search_fields)
        self.required_fields = self.get_existing_fields(self.required_fields)
        self.non_edit_fields = self.get_existing_fields(self.non_edit_fields)
        self.upload_fields = self.get_existing_fields(self.upload_fields)
        self.data_path = "data" if not data_path else data_path
        mkdir(f"{self.data_path}/tmp")

    def get_existing_fields(self, fields):
        return [field for field in fields if hasattr(self.model, field)]

    def create_data_handler(self, data):
        return data

    def update_data_handler(self, data):
        return data

    def get_all_fields(self):
        all_fields = {}

        for field, field_type in self.model._meta.fields.items():
            all_fields[field] = peewee2type.get(str(type(field_type)), None)

        return all_fields

    def dict(self):
        return dict(
            model=self.model_name,
            search_fields=self.search_fields,
            required_fields=self.required_fields,
            non_edit_fields=self.non_edit_fields,
            upload_fields=self.upload_fields,
            all_fields=self.get_all_fields(),
        )


class TigerAdmin:
    def __init__(self):
        self.models = []

    def get_admin_model(self, name):
        for model in self.models:
            if model.model_name == name:
                return model

    def admin_search_instance(self, name: str, filters: dict = {}, page: int = 1, paginate_by: int = 20,
                              q: str = "",  order_by: str = ""):
        ok_order_by = ["asc created", "desc created", "asc updated", "desc updated"]
        if order_by and order_by not in ok_order_by:
            return dict(msg=f'Order_by can be equal {", ".join(ok_order_by)}'), 400

        admin_model = self.get_admin_model(name)
        if not admin_model:
            return dict(msg=f"{name} model doesn't exist in the admin scope"), 400

        model = admin_model.model

        qs = model.select().order_by(model.created.desc())

        if q != "":
            qs = qs.where(query_search(
                qs,
                q,
                [getattr(model, field) for field in admin_model.search_fields]
            ))

        for field, value in filters.items():
            if field not in admin_model.model_fields:
                continue
            if field is not False and not field:
                continue

            qs = qs.where(getattr(model, field) == value)

        if order_by != "":
            order, column = tuple(order_by.split(" "))
            qs = qs.order_by(getattr(getattr(model, column), order)())

        return dict(
            msg="ok",
            data=[model_to_dict(model) for model in qs.paginate(page, paginate_by)],
            page=page,
            no_objects=qs.count(),
            paginate_by=paginate_by,
        )

    def admin_create_instance(self, name: str, data: dict):
        admin_model = self.get_admin_model(name)
        if not admin_model:
            return dict(msg=f"{name} model doesn't exist in the admin scope"), 400

        model = admin_model.model
        res_data = {}

        data = admin_model.create_data_handler(data)

        for key, value in data.items():
            if key not in admin_model.model_fields:
                continue

            res_data[key] = value

        for field in admin_model.required_fields:
            if field not in res_data:
                return dict(msg=f"{field} field is required"), 400

        try:
            res_model = model.create(**res_data)
        except IntegrityError:
            return dict(msg="Model with such unique constraint already exists", error=format_exc()), 400
        except: # noqa
            return dict(msg="Something went wrong", error=format_exc()), 400

        return dict(msg="ok")

    def admin_update_instance(self, name: str, identifier: dict, data: dict):
        admin_model = self.get_admin_model(name)
        if not admin_model:
            return dict(msg=f"{name} model doesn't exist in the admin scope"), 400

        model = admin_model.model
        check = True

        data = admin_model.update_data_handler(data)

        for key, value in identifier.items():
            if key not in admin_model.model_fields:
                return dict(msg=f"Wrong identifier. {key} field doesn't exist."), 400

            check = check and getattr(model, key) == value

        res_model = model.select().where(check).get()

        try:
            for key, value in data.items():
                if key not in admin_model.model_fields:
                    continue

                if key in admin_model.non_edit_fields:
                    continue

                setattr(res_model, key, value)

            res_model.save()
        except IntegrityError:
            return dict(msg="Model with such unique constraint already exists", error=format_exc()), 400
        except: # noqa
            return dict(msg="Something went wrong", error=format_exc()), 400

        return dict(msg="ok", data=model_to_dict(res_model))

    def admin_get_models(self):
        return dict(msg="ok", data=[model.dict() for model in self.models])

    def add(self, admin_model):
        if admin_model in self.models:
            return

        self.models.append(admin_model)

    def install(self, auth_func=None, roles=None, prefix=""):
        make_public([
            self.admin_get_models,
            self.admin_search_instance,
            self.admin_create_instance,
            self.admin_update_instance,
        ], auth_func=auth_func, roles=roles, prefix=prefix)
