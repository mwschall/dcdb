from django.db.models import Aggregate, CharField


# https://stackoverflow.com/a/31337612
# noinspection PyAbstractClass
class GroupConcat(Aggregate):
    function = 'GROUP_CONCAT'
    template = "%(function)s(%(distinct)s%(expressions)s%(separator)s)"

    def __init__(self, expression, separator=',', distinct=False, **extra):
        # cater to lowest common denominator
        assert separator == ',' or not distinct, \
            'SQLite cannot specify a custom separator with distinct clause.'

        super().__init__(
            expression,
            separator=separator,
            distinct='DISTINCT ' if distinct else '',
            output_field=CharField(),
            **extra)

    def get_separator(self, tmpl):
        separator = self.extra['separator']
        return tmpl % separator if separator != ',' else ''

    def as_mysql(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler, connection,
            separator=self.get_separator(" SEPARATOR '%s'"),
            **extra_context
        )

    def as_postgresql(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler, connection,
            function='string_agg',
            separator=self.get_separator(", '%s'"),
            **extra_context
        )

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler, connection,
            # sqlite expects only one argument when using DISTINCT
            separator=self.get_separator(", '%s'") if not self.extra['distinct'] else '',
            **extra_context
        )


# noinspection PyAbstractClass
class NAGroupConcat(GroupConcat):
    contains_aggregate = False
