from leapp.models import Model, fields
from leapp.topics import SystemInfoTopic


class CupsChangedFeatures(Model):
    topic = SystemInfoTopic

    interface = fields.Nullable(fields.Boolean())
    """
    True if interface scripts are used, False otherwise
    """

    digest = fields.Nullable(fields.Boolean())
    """
    True if Digest/BasicDigest directive values are used, False otherwise
    """

    include = fields.Nullable(fields.Boolean())
    """
    True if Include directive is used, False otherwise
    """

    certkey = fields.Nullable(fields.Boolean())
    """
    True if ServerKey/ServerCertificate directives are used, False otherwise
    """

    env = fields.Nullable(fields.Boolean())
    """
    True if PassEnv/SetEnv directives are used, False otherwise
    """

    printcap = fields.Nullable(fields.Boolean())
    """
    True if PrintcapFormat directive is used, False otherwise
    """

    include_files = fields.Nullable(fields.List(fields.String()))
    """
    Paths to included files, contains /etc/cups/cupsd.conf by default
    """
