from leapp.actors import Actor
from leapp.libraries.common.reporting import report_generic
from leapp.models import Report, InstalledRedHatSignedRPM, Cupsmigrationmodel, Matrix
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag

import os
from re import compile, findall, MULTILINE

"""
CUPS configuration files
"""
CUPSD_CONF = '/etc/cups/cupsd.conf'
CUPSFILES_CONF = '/etc/cups/cups-files.conf'

"""
Names for better navigation through change list
"""
KEY = 0
DIRECTIVES = 1
SOURCE = 2
TARGET = 3

"""
List of changed directives

Scheme:
Dictionary key # Directives # Input configuration file # Output configuration file

Some changes happened only in one configuration file, so the last member of list is 'None'.
"""
cupsd_changes_list = [
                      ['include', ['Include'], CUPSD_CONF, None],
                      ['digest', ['Digest', 'BasicDigest'], CUPSD_CONF, None],
                      ['env', ['SetEnv', 'PassEnv'], CUPSD_CONF, CUPSFILES_CONF],
                      ['printcap', ['PrintcapFormat'], CUPSD_CONF, CUPSFILES_CONF]
                    ]

cupsfiles_changes_list = [
                          ['certkey', ['ServerCertificate', 'ServerKey'], CUPSFILES_CONF, None]
                          ]

class CupsCheck(Actor):
    """
    cups_check actor

    Actor checks if cups package is installed and if one or more following
    situations appears in configuration files:
    - interface scripts
    - use of 'Digest' or 'BasicDigest' authentication
    - use of 'Include' directive
    - use of 'ServerCertificate' and 'ServerKey' directives
    - use of 'SetEnv' or 'PassEnv' directives
    - use of 'PrintcapFormat' directive

    The actor creates python dictionary from gathered data.
    """

    name = 'cups_check'
    consumes = (InstalledRedHatSignedRPM,)
    produces = (Report, Cupsmigrationmodel)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def has_interface_script(self):
      """
      has_interface_script

      Checks if any file is in /etc/cups/interfaces, which means there could be
      print queues using interface script.

      returns boolean
      """
      if os.path.exists('/etc/cups/interfaces'):
        if len(os.listdir('/etc/cups/interfaces')) > 0:
          return True

      return False

    def has_directive(self, directives_list, filename):
      """
      has_directive

      Checks if configuration file has directive set.

      parameters:
      - directives_list - list of strings
      - filename - string

      returns boolean
      """
      found = False

      with open(filename, 'r') as opened_config:
        file_contents = opened_config.read()
        for directive in directives_list:
          # Digest/BasicDigest are directive values, so regular expression differs
          if directive == 'Digest' or directive == 'BasicDigest':
            regexp_string = '\s+'
          else:
            regexp_string = '^\s*'
          regexp_string = regexp_string + directive + '\s'
          pattern = compile(regexp_string, MULTILINE)
          matched_list = findall(pattern, file_contents)
          if len(matched_list) > 0:
            found = True
            break
        opened_config.close()

      return found

    def look_for_affected_features(self, include_files_list=[CUPSD_CONF]):
      """
      look_for_affected_features

      parameters:
      - include_file_list - list of strings

      returns dictionary
      """

      matrix = {
                  'interface' : False,
                  'digest' : False,
                  'include' : False,
                  'certkey' : False,
                  'env' : False,
                  'printcap' : False
                }

      matrix['interface'] = self.has_interface_script()

      for change_list in cupsd_changes_list:
        for config_file in include_files_list:
          # If we already found the directive somewhere - in regular configuration file or
          # included one - we do not need to search anymore, the migration will happen.

          # Names like KEY, DIRECTIVES, SOURCE are just enum constants corresponding with
          # scheme in libraries/py - just for better understanding what lies on
          # specific indexes of the list (hope)
          if matrix[change_list[KEY]] is False:
            matrix[change_list[KEY]] = self.has_directive(change_list[DIRECTIVES], config_file)

      for change_list in cupsfiles_changes_list:
        matrix[change_list[KEY]] = self.has_directive(change_list[DIRECTIVES], change_list[SOURCE])

      return matrix

    def get_include_files_list(self):
      """
      get_include_files_list

      we need all included files in list

      returns list of strings
      """
      paths = [CUPSD_CONF]
      pattern = compile('^\s*Include\s+(.+?)\s', MULTILINE)

      for found_path in paths:
        with open(found_path, 'r') as opened_config:
          file_contents = opened_config.read()
          matched_list = findall(pattern, file_contents)
          if len(matched_list) > 0:
            for new_path in matched_list:
              if new_path not in paths:
                paths.append(new_path)
          opened_config.close()

      return paths

    def process(self):
      installed_cups = False
      include_files_list = [CUPSD_CONF]
      migrateable = False
      migration_matrix = {
                            'interface' : False,
                            'digest' : False,
                            'include' : False,
                            'certkey' : False,
                            'env' : False,
                            'printcap' : False
                          }

      for rpm_pkgs in self.consume(InstalledRedHatSignedRPM):
        for pkg in rpm_pkgs.items:
          if pkg.name == 'cups':
            installed_cups = True

      if installed_cups is False:
        report_generic(
                        title='CUPS will not be migrated.',
                        summary='CUPS is not installed.',
                        severity='low'
                      )
        migrateable = False
      else:
        include_files_list = self.get_include_files_list()
        
        migration_matrix = self.look_for_affected_features(include_files_list=include_files_list)

        if True in migration_matrix.values():
          report_generic(
                          title='CUPS will be migrated.',
                          summary='Current CUPS configuration contains deprecated features which needs migration .',
                          severity='medium'
                        )
          migrateable = True
        else:
          report_generic(
                          title='CUPS will not be migrated.',
                          summary='Current CUPS configuration is up-to-date .',
                          severity='medium'
                        )
          migrateable = False

        self.produce(Cupsmigrationmodel(
                                        migration_matrix=Matrix(
                                                interface=migration_matrix['interface'],
                                                digest=migration_matrix['digest'],
                                                include=migration_matrix['include'],
                                                certkey=migration_matrix['certkey'],
                                                env=migration_matrix['env'],
                                                printcap=migration_matrix['printcap']
                                              ),
                                        migrateable=migrateable,
                                        include_files=include_files_list))

