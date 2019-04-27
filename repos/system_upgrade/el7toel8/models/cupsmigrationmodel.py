from leapp.models import Model, fields
from leapp.topics import SystemInfoTopic

class Matrix(Model):
    topic = SystemInfoTopic
    interface = fields.Boolean()
    digest = fields.Boolean()
    include = fields.Boolean()
    certkey = fields.Boolean()
    env = fields.Boolean()
    printcap = fields.Boolean()

class Cupsmigrationmodel(Model):
    topic = SystemInfoTopic
    migration_matrix = fields.Model(Matrix)
    migrateable = fields.Boolean()
    include_files = fields.List(fields.String())
