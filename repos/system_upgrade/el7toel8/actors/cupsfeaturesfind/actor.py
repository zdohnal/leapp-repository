from leapp.actors import Actor
from leapp.libraries.actor import library
from leapp.models import Report, InstalledRedHatSignedRPM, CupsChangedFeatures
from leapp.tags import FactsPhaseTag, IPUWorkflowTag


class CupsFeaturesFind(Actor):
    """
    Gather facts about CUPS features which needs to be migrated

    Actor checks if cups package is installed and if one or more following
    situations appears in configuration files:
    - interface scripts
    - use of 'Digest' or 'BasicDigest' authentication
    - use of 'Include' directive
    - use of 'ServerCertificate' and 'ServerKey' directives
    - use of 'SetEnv' or 'PassEnv' directives
    - use of 'PrintcapFormat' directive

    The actor creates list from gathered data.
    """

    name = 'cups_features_find'
    consumes = (InstalledRedHatSignedRPM,)
    produces = (Report, CupsChangedFeatures)
    tags = (FactsPhaseTag, IPUWorkflowTag)

    def process(self):
        library.find_features()
