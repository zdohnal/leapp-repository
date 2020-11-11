from leapp.libraries.stdlib import api
from leapp.models import CupsChangedFeatures
from leapp import reporting


def _get_input_model(model):
    """
    Gets data model from an actor.

    :param obj model: object of model which data will be consumed
    """
    return next(api.consume(model), None)


def check_interface_scripts(facts, report_func):
    """
    Checks if the data model tells interface scripts are used
    and produces a report.

    :param obj facts: model object containing info about CUPS configuration
    :param func report_func: creates report
    """
    title = ('CUPS no longer supports usage of interface scripts')
    summary = ('Interface scripts are no longer supported due '
               'security issues - an attacker could provide '
               'malicious script which will be run during printing')
    hint = ('Please install the queue with PPD file for the printer '
            'if available or install the queue with generic PPD, '
            'add *cupsFilter2 directive into PPD of installed '
            'queue (in /etc/cups/ppd) and reinstall the queue with modified PPD. '
            'The interface script needs to have permissions 750 and '
            'ownership root:lp. How to write *cupsFilter2 directive '
            'is described at https://www.cups.org/doc/spec-ppd.html#cupsFilter2 '
            'and the script needs to be put into /usr/lib/cups/filter '
            'or you need to use an absolute path to the script '
            'in *cupsFilter2 directive')
    if facts.interface:
        args = [
            reporting.Title(title),
            reporting.Summary(summary),
            reporting.Tags([reporting.Tags.DRIVERS]),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Remediation(hint=hint)
        ]

        report_func(args)


def check_include_directive(facts, report_func):
    """
    Checks if the data model tells include directives are used
    and produces a report.

    :param obj facts: model object containing info about CUPS configuration
    :param func report_func: creates report
    """
    title = ('CUPS no longer supports usage of Include directive')
    summary = ('Include directive was removed due security reasons. '
               'Contents of found included files will be appended to '
               'cupsd.conf')
    if facts.include:
        args = [
            reporting.Title(title),
            reporting.Summary(summary),
            reporting.Tags([reporting.Tags.SERVICES]),
            reporting.Severity(reporting.Severity.MEDIUM),
            reporting.RelatedResource('files',
                                      ' '.join(f for f in facts.include_files))
        ]

        report_func(args)


def check_printcap_directive(facts, report_func):
    """
    Checks if the data model tells printcapformat directive is used
    and produces a report.

    :param obj facts: model object containing info about CUPS configuration
    :param func report_func: creates report
    """
    title = ('PrintcapFormat directive is no longer in cupsd.conf')
    summary = ('The directive was moved into /etc/cups/cups-files.conf '
               'because it is deprecated. The migration script will take '
               'PrintcapFormat directive from cupsd.conf if used '
               'and put it into cups-files.conf')
    if facts.printcap:
        args = [
            reporting.Title(title),
            reporting.Summary(summary),
            reporting.Tags([reporting.Tags.SERVICES]),
            reporting.Severity(reporting.Severity.LOW),
            reporting.RelatedResource('files',
                                      ('/etc/cups/cupsd.conf '
                                       '/etc/cups/cups-files.conf'))
        ]

        report_func(args)


def check_env_directives(facts, report_func):
    """
    Checks if the data model tells PassEnv/SetEnv directives are used
    and produces a report.

    :param obj facts: model object containing info about CUPS configuration
    :param func report_func: creates report
    """
    title = ('PassEnv/SetEnv directives are no longer in cupsd.conf')
    summary = ('The directives were moved into /etc/cups/cups-files.conf '
               'due security reasons. The migration script will take '
               'the directives from cupsd.conf if used put them into '
               '/etc/cups/cups-files.conf')
    if facts.env:
        args = [
            reporting.Title(title),
            reporting.Summary(summary),
            reporting.Tags([reporting.Tags.SERVICES]),
            reporting.Severity(reporting.Severity.MEDIUM),
            reporting.RelatedResource('files',
                                      ('/etc/cups/cupsd.conf '
                                       '/etc/cups/cups-files.conf'))
        ]

        report_func(args)


def check_certkey_directives(facts, report_func):
    """
    Checks if the data model tells ServerKey/ServerCertificate directives
    are used and produces a report.

    :param obj facts: model object containing info about CUPS configuration
    :param func report_func: creates report
    """
    title = ('ServerKey/ServerCertificate directives are substitued '
             'by ServerKeychain directive')
    summary = ('The directives were substitued by ServerKeychain directive, '
               'which now takes a directory as value (/etc/cups/ssl is default). '
               'The previous directives took a file as value. '
               'The migration script will copy the files specified in '
               'directive values into /etc/cups/ssl directory '
               'if they are not there already')
    if facts.certkey:
        args = [
            reporting.Title(title),
            reporting.Summary(summary),
            reporting.Tags([reporting.Tags.SERVICES,
                            reporting.Tags.AUTHENTICATION]),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.RelatedResource('file',
                                      '/etc/cups/cups-files.conf')
        ]

        report_func(args)


def check_digest_values(facts, report_func):
    """
    Checks if the data model tells Digest/BasicDigest values
    of AuthType/DefaultAuthType directives are used
    and produces a report.

    :param obj facts: model object containing info about CUPS configuration
    :param func report_func: creates report
    """
    title = ('CUPS no longer supports Digest and BasicDigest '
             'directive values')
    summary = ('The directive values were removed due deprecation, '
               'The migration script will set Basic authentication')
    if facts.digest:
        args = [
            reporting.Title(title),
            reporting.Summary(summary),
            reporting.Tags([reporting.Tags.SERVICES,
                            reporting.Tags.AUTHENTICATION]),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.RelatedResource('file',
                                      '/etc/cups/cupsd.conf')
        ]

        report_func(args)


def make_reports(consume_function=_get_input_model,
                 report_func=reporting.create_report,
                 debug_log=api.current_logger().debug):
    """
    Creates reports if needed

    :param func consume_function: gets data model from an actor
    :param func report_func: creates report
    """
    facts = consume_function(CupsChangedFeatures)

    if facts:
        check_interface_scripts(facts, report_func)
        check_include_directive(facts, report_func)
        check_printcap_directive(facts, report_func)
        check_env_directives(facts, report_func)
        check_certkey_directives(facts, report_func)
        check_digest_values(facts, report_func)
    else:
        debug_log('No facts gathered about CUPS - skipping reports.')
