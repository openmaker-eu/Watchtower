from application.Connections import Connection
from psycopg2.extensions import AsIs


class Model:
    def __init__(self, model):
        for key in self.fields():
            self.__setattr__(key, model[key])

    @staticmethod
    def fields():
        raise NotImplementedError

    @staticmethod
    def model_id_column():
        raise NotImplementedError

    @staticmethod
    def table_name():
        raise NotImplementedError

    @staticmethod
    def hidden_fields():
        raise NotImplementedError

    @staticmethod
    def create_query_builder(create_dict):
        columns = []
        values_params = {}
        values = []
        for k, v in create_dict.items():
            values_params['k_' + k] = v
            values.append('%(k_' + k + ')s')
            columns.append(k)
        return {
            'query_cols': ", ".join(columns),
            'query_vals_param': values_params,
            'query_vals': ", ".join(values)
        }

    @classmethod
    def create(cls, create_dict):
        with Connection.Instance().get_cursor() as cur:
            builder = cls.create_query_builder(create_dict)
            params = {
                'table': AsIs(cls.table_name()),
                'columns': AsIs(builder['query_cols']),
                'values': builder['query_vals']
            }
            sql = (
                "INSERT INTO %(table)s "
                "(%(columns)s) "
                "VALUES ({0}) "
                "RETURNING *;"
            ).format(builder['query_vals'])
            cur.execute(sql, {**params, **builder['query_vals_param']})
            model = cur.fetchone()

            if model is not None:
                model = cls({key: model[i] for i, key in enumerate(cls.fields())})
            return model

    @classmethod
    def update_by_id(cls, update_dict, model_id):
        with Connection.Instance().get_cursor() as cur:
            builder = cls.update_query_builder(update_dict)
            params = {
                'table': AsIs(cls.table_name()),
                'object_id_column': AsIs(cls.model_id_column()),
                'object_id': model_id
            }
            sql = (
                "UPDATE %(table)s "
                "SET {0} "
                "WHERE %(object_id_column)s = %(object_id)s"
            ).format(builder['query_str'])
            cur.execute(sql, {**params, **builder['query_vals']})

    @classmethod
    def find_by_id(cls, model_id):
        with Connection.Instance().get_cursor() as cur:
            params = {
                'table': AsIs(cls.table_name()),
                'id': model_id,
                'id_column': AsIs(cls.model_id_column())
            }
            sql = (
                "SELECT * "
                "FROM %(table)s "
                "WHERE %(id_column)s = %(id)s;"
            )
            cur.execute(sql, params)
            model = cur.fetchone()

            if model is not None:
                model = cls({key: model[i] for i, key in enumerate(cls.fields())})
            return model

    @staticmethod
    def find_query_builder(find_tuple_array):
        if find_tuple_array is None:
            return {
                'query_param': {},
                'query_str': "1 = 1"
            }

        find_query_array = []
        find_values_array = {}
        for tuple_array in find_tuple_array:
            left_side = tuple_array[0]
            operand = "="
            right_side = None
            if len(tuple_array) == 3:
                operand = tuple_array[1]
                right_side = tuple_array[2]
            if len(tuple_array) == 2:
                right_side = tuple_array[1]

            find_query_array.append("%(k_{0})s {1} %(v_{0})s".format(left_side, operand))
            find_values_array['k_' + left_side] = AsIs(left_side)
            find_values_array['v_' + left_side] = right_side
        return {
            'query_param': find_values_array,
            'query_str': " AND ".join(find_query_array)
        }

    @classmethod
    def find_all(cls, filters=None, order_by=None, order_dir="ASC", is_object=True):
        if order_by is None:
            order_by = cls.model_id_column()
        builder = cls.find_query_builder(filters)

        with Connection.Instance().get_cursor() as cur:
            params = {
                'table': AsIs(cls.table_name()),
                'filter': AsIs(filters),
                'order_by': AsIs(order_by),
                'order_dir': AsIs(order_dir)
            }
            sql = (
                "SELECT * "
                "FROM %(table)s "
                "WHERE {0} "
                "ORDER BY %(order_by)s %(order_dir)s;"
            ).format(builder['query_str'])
            cur.execute(sql, {**params, **builder['query_param']})
            var = cur.fetchall()

            models = var if len(var) > 0 else []
            if len(models) > 0:
                dict_list = []
                for model in models:
                    if is_object:
                        dict_list.append(cls({key: model[i] for i, key in enumerate(cls.fields())}))
                    else:
                        dict_list.append(cls({key: model[i] for i, key in enumerate(cls.fields())})._dict())
                models = dict_list
            return models

    @staticmethod
    def update_query_builder(update_dict):
        update_query_array = []
        update_values_array = {}
        for k, v in update_dict.items():
            update_query_array.append("%(k_{0})s = %(v_{0})s".format(k))
            update_values_array['k_' + k] = AsIs(k)
            update_values_array['v_' + k] = v
        return {
            'query_vals': update_values_array,
            'query_str': " ,".join(update_query_array)
        }

    def update(self, update_dict):
        with Connection.Instance().get_cursor() as cur:
            builder = self.update_query_builder(update_dict)
            params = {
                'table': AsIs(self.table_name()),
                'object_id_column': AsIs(self.model_id_column()),
                'object_id': self.__getattribute__(self.model_id_column())
            }
            sql = (
                "UPDATE %(table)s "
                "SET {0} "
                "WHERE %(object_id_column)s = %(object_id)s"
            ).format(builder['query_str'])
            cur.execute(sql, {**params, **builder['query_vals']})
            for k, v in update_dict.items():
                self.__setattr__(k, v)

    """
    def delete(self):
    """

    def exists(self, filters=""):
        with Connection.Instance().get_cursor() as cur:
            params = {
                'table': AsIs(self.table_name),
                'filter': AsIs(filters)
            }
            sql = (
                "SELECT * "
                "FROM %(table)s "
                "%(filter)s;"
            )
            cur.execute(sql, params)
            var = cur.fetchone()
            if var is not None:
                return True
            else:
                return False

    def _dict(self):
        return {key: self.__getattribute__(key) for key in self.__slots__}

    def __str__(self):
        return self._dict().__str__()

    def get_relations(self, relation_table, relation_column):
        with Connection.Instance().get_cursor() as cur:
            params = {
                'table': AsIs(relation_table),
                'relation_column': AsIs(relation_column),
                'id_column': AsIs(self.model_id_column()),
                'id_value': self.__getattribute__(self.model_id_column())
            }
            sql = (
                "SELECT %(relation_column)s "
                "FROM %(table)s "
                "WHERE %(id_column)s = %(id_value)s;"
            )
            cur.execute(sql, params)
            var = cur.fetchall()

            if var is not None:
                return [i[0] for i in var]
            return []

    def add_relation(self, relation_table, relation_column, relation_value):
        with Connection.Instance().get_cursor() as cur:
            params = {
                'table': AsIs(relation_table),
                'relation_column': AsIs(relation_column),
                'relation_value': relation_value,
                'id_column': AsIs(self.model_id_column()),
                'id_value': self.__getattribute__(self.model_id_column())
            }
            sql = (
                "INSERT INTO %(table)s "
                "(%(relation_column)s, %(id_column)s) "
                "VALUES (%(relation_value)s, %(id_value)s);"
            )
            cur.execute(sql, params)

    def delete_relation(self, relation_table, relation_column, relation_value):
        with Connection.Instance().get_cursor() as cur:
            params = {
                'table': AsIs(relation_table),
                'relation_column': AsIs(relation_column),
                'relation_value': relation_value,
                'id_column': AsIs(self.model_id_column()),
                'id_value': self.__getattribute__(self.model_id_column())
            }
            sql = (
                "DELETE FROM %(table)s "
                "WHERE (%(relation_column)s = (%(relation_value)s "
                "AND "
                "%(id_column)s) = %(id_value)s);"
            )
            cur.execute(sql, params)
