from leapp.actors import Actor
from leapp.exceptions import StopActorExecutionError
from leapp.libraries.common.reporting import report_generic
from leapp.models import Report, Cupsmigrationmodel
from leapp.tags import ApplicationsPhaseTag, IPUWorkflowTag

import os
from re import compile, findall, search, sub, MULTILINE

"""
CUPS configuration files
"""
CUPSD_CONF = '/etc/cups/cupsd.conf'
CUPSFILES_CONF = '/etc/cups/cups-files.conf'

"""
Names for better navigation through change list
"""

INCLUDE = 0
DIGEST = 1
ENV = 2
PRINTCAP = 3

CERTKEY = 0

KEY = 0
NAMES = 1
NEWNAME = 2
SOURCE = 3
TARGET = 4

"""
List of changed directives

Scheme:
Dictionary key # Directives # Input configuration file # Output configuration file

Some changes happened only in one configuration file, so the last member of list is 'None'.
"""
cupsd_changes_list = [
                      ['include', ['Include'], None, CUPSD_CONF, None],
                      ['digest', ['Digest', 'BasicDigest'], 'Basic', CUPSD_CONF, None],
                      ['env', ['SetEnv', 'PassEnv'], None, CUPSD_CONF, CUPSFILES_CONF],
                      ['printcap', ['PrintcapFormat'], None, CUPSD_CONF, CUPSFILES_CONF]
                    ]

cupsfiles_changes_list = [
                          ['certkey', ['ServerCertificate', 'ServerKey'], 'ServerKeychain', CUPSFILES_CONF, None]
                          ]

"""
Changed directives and values
"""
changed_directives = ['Include', 'SetEnv', 'PassEnv', 'ServerCertificate', 'ServerKey', 'PrintcapFormat']
changed_values = ['Digest', 'BasicDigest']

class CupsMigrate(Actor):
    """
    cups_migrate actor

    Migrates configuration directives and reports if interface scripts are used.
    """

    name = 'cups_migrate'
    consumes = (Cupsmigrationmodel,)
    produces = (Report,)
    tags = (ApplicationsPhaseTag, IPUWorkflowTag)

    def remove_string(self, directive, value, content):
      """
      remove_string

      parameters:
      - directive - string
      - value - string
      - content - string

      returns string
      """
      removal_regexp = directive + '\s+' + value + '\s*\n'
      removal_pattern = compile(removal_regexp)
      content = sub(removal_pattern, '', content)

      return content

    def migrate_serverkeychain_path(self, path, new_directive, new_content):
      """
      migrate_serverkeychain_path

      parameter:
      - path - string
      - new_directive - string
      - new_content - string

      returns string
      """

      # path can be relative to CUPS server root, our supported default is
      # /etc/cups, so put it before it - that's how CUPS solves it in the code
      if not path.startswith('/'):
        path = '/etc/cups' + path
      # move certificate or key to supported default path - /etc/cups/ssl - if it is not
      # already
      if not path.startswith('/etc/cups/ssl'):
        os.rename(path, '/etc/cups/ssl/' + path.rsplit('/', 1)[1])
        # if file was moved to default directory, no need to keep directive 
        # in configuration file
        new_content = self.remove_string(new_directive, path, new_content)
      else:
        if os.path.isfile(path):
          # if path starts with /etc/cups/ssl, remove the filename from the path,
          # because ServerKeychain wants directory
          new_path = path.rsplit('/', 1)[0]
          new_content = new_content.replace(path, new_path)


      return new_content

    def find_values(self, directive, content):
      """
      migrate_serverkeychain

      parameters:
      - directive - string
      - new_content - string

      returns list of strings
      """

      # we need to get values
      value_regexp = '^\s*' + directive + '\s+(.+?)\s' 
      value_pattern = compile(value_regexp, MULTILINE)
      found_values = findall(value_pattern, content)

      return found_values

    def find_and_replace(self, directives, new_directive, file):
      """
      find_and_replace
  
      parameters:
      - directives - list of strings
      - new-directive - string
      - file - string
  
      returns boolean
      """

      result = False

      for directive in directives:
        # regexp and new string differs if we replace directive or value - directive needs to have at least one
        # white character at the end, but value needs to have one white character at start and zero or N white
        # characters at the end + new line character
        if directive in changed_directives:
          directive_regexp = directive + '\s'
          new_directive_string = new_directive + ' '
        elif directive in changed_values:
          directive_regexp = '\s' + directive + '\s*\n'
          new_directive_string = ' ' + new_directive + '\n'
        pattern = compile(directive_regexp)

        try:
          with open(file, 'r') as conf:
            content = conf.read()
        except IOError:
          return result

        new_content = sub(pattern, new_directive_string, content)
        if new_directive == 'ServerKeychain':
          # ServerKeyChain migration needs more attention - like moving the files into specific directory
          found_values = self.find_values(new_directive, new_content)
          for value in found_values:
            new_content = self.migrate_serverkeychain_path(value, new_directive, new_content)

        try:
          with open(file, 'w') as conf:
            conf.write(new_content)
          result = True
        except IOError:
          return result

      return result

    def migrate_includes(self, include_files):
      """
      concatenate_file
  
      parameters:
      - include_files - list of strings
  
      Returns boolean
      """

      try:
        with open(include_files[0], 'r') as cupsd_conf:
          cupsd_contents = cupsd_conf.read()
      except IOError:
        return False
        
      # concatenation of files
      for conf in include_files[1:]:
        if os.path.exists(conf) is True:
          try:
            with open(conf, 'r') as opened_conf:
              includefile_contents = opened_conf.read()
          except IOError:
            return False
          try:
            with open(include_files[0], 'w') as cupsd_conf:
              cupsd_contents = cupsd_contents + includefile_contents
              cupsd_conf.write(cupsd_contents)
          except IOError:
            return False
        else:
          return False

      # remove Include directives from cupsd.conf
      found_values = self.find_values('Include', cupsd_contents)
      for value in found_values:
        cupsd_contents = self.remove_string('Include', value, cupsd_contents)

      try:
        with open(include_files[0], 'w') as cupsd_conf:
          cupsd_conf.write(cupsd_contents)
        return True
      except IOError:
        return False

    def move(self, directives, source, target):
      """
      move()
  
      parameters:
      - directives - list of strings
      - source - string
      - target - string
  
      returns boolean
      """

      try:
        with open(source, 'r') as opened_source:
          source_content = opened_source.read()
      except IOError:
        return False

      try:
        with open(target, 'r') as opened_target:
          target_content = opened_target.read()
      except IOError:
        return False

      # grap directive and its value from old config and put it into new config
      for directive in directives:
        regexp = '(' + directive + '\s+.+\s*\n?)'
        pattern = compile(regexp)
        found_lines = findall(pattern, source_content)
        for line in found_lines:
          try:
            with open(target, 'w') as opened_target:
              opened_target.write(target_content + line)
          except IOError:
            return False

          target_content = target_content + line
          source_content = source_content.replace(line, '')
          try:
            with open(source, 'w') as opened_source:
              opened_source.write(source_content)
          except IOError:
            return False

      return True

    def process(self):
      for model in self.consume(Cupsmigrationmodel):
        if model.migrateable is False:
          report_generic(
                          title='CUPS will not be migrated.',
                          summary='CUPS is not installed or its configuration is up-to-date.',
                          severity='low'
                        )
          raise StopActorExecution('CUPS will not be migrated')

        include_files = model.include_files
        interface = model.migration_matrix.interface
        digest = model.migration_matrix.digest
        include = model.migration_matrix.include
        certkey = model.migration_matrix.certkey
        env = model.migration_matrix.env
        printcap = model.migration_matrix.printcap


        if interface is True:
          report_generic(
                          title='Print queues with interface scripts are used on the machine.',
                          summary='There are files in /etc/cups/interfaces directory, which indicates usage of print queues with interface scripts. Interface script were removed from CUPS due security issues, so print queues with them will not work in newer CUPS version. Please try to install your printer with printer driver.',
                          severity='high'
                        )
        if include is True:
          result = self.migrate_includes(include_files)
          if result is not True:
            raise StopActorExecutionError('Include directive could not be migrated due IOError')

        if digest is True:
          result = self.find_and_replace(cupsd_changes_list[DIGEST][NAMES],
                                         cupsd_changes_list[DIGEST][NEWNAME],
                                         cupsd_changes_list[DIGEST][SOURCE])
          if result is not True:
            raise StopActorExecutionError('Digest directives could not be migrated due IOError')

        if certkey is True:
          result = self.find_and_replace(cupsfiles_changes_list[CERTKEY][NAMES],
                                         cupsfiles_changes_list[CERTKEY][NEWNAME],
                                         cupsfiles_changes_list[CERTKEY][SOURCE])
          if result is not True:
            raise StopActorExecutionError('ServerCertificate and ServerKey directives could not be migrated due IOError')

        if env is True:
          result = self.move(cupsd_changes_list[ENV][NAMES],
                             cupsd_changes_list[ENV][SOURCE],
                             cupsd_changes_list[ENV][TARGET])
          if result is not True:
            raise StopActorExecutionError('PassEnv/SetEnv directives could not be migrated due IOError')

        if printcap is True:
          result = self.move(cupsd_changes_list[PRINTCAP][NAMES],
                             cupsd_changes_list[PRINTCAP][SOURCE],
                             cupsd_changes_list[PRINTCAP][TARGET])
          if result is not True:
            raise StopActorExecutionError('PrintcapFormat directive could not be migrated due IOError')

        report_generic(
                        title='CUPS was migrated.',
                        summary='The migration successfully ended.',
                        severity='medium'
                      )
