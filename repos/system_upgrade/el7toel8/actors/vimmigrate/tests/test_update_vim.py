import pytest

from leapp.libraries.actor import library


packages = [
    {
        'vim-minimal': '/etc/virc',
        'vim-enhanced': '/etc/vimrc'
    },
    {
        'vim-minimal': '/etc/virc',
        'vim-enhanced': ''
    },
    {
        'vim-minimal': '',
        'vim-enhanced': '/etc/vimrc'
    },
    {
        'vim-minimal': '',
        'vim-enhanced': ''
    },
    {
        'vim-minimal': '/etc/virc',
        'ble': ''
    },
    {
        'vim-minimal': '',
        'ble': ''
    },
    {
        'vim-enhanced': '/etc/vimrc',
        'moo': ''
    },
    {
        'vim-enhanced': '',
        'moo': ''
    },
    {
        'you': '',
        'hele': ''
    }
]


class MockLogger(object):
    def __init__(self):
        self.debugmsg = None
        self.errmsg = None

    def debug(self, message):
        self.debugmsg += message

    def error(self, message):
        self.errmsg += message


class MockPackage(object):
    def __init__(self, name, config):
        self.name = name
        self.config = config


class MockPackageSet(object):
    def __init__(self):
        self.installed_packages = None

    def add_packages(self, pkgs):
        if self.installed_packages is None:
            self.installed_packages = {}

        for rpm, config in pkgs.items():
            self.installed_packages.append(MockPackage(rpm, config))

    def is_installed(self, pkg):
        for rpm in self.installed_packages:
            if pkg == rpm.name:
                return True
        return False

    def append_content(self, path, content):
        found = False

        for rpm in self.installed_packages:
            if path == rpm.config:
                found = True
        if not found:
            raise IOError('Error during writing to file: {}.'.format(path))


class ExpectedOutput(object):
    def __init__(self):
        self.expected_debugmsg = ''
        self.expected_errmsg = ''

    def create(self, rpms):
        error_list = []

        for pkg, config in rpms.items():
            if pkg in library.vim_configs.keys():
                self.expected_debugmsg += 'Updating Vim configuration file {}.'.format(config)
                if config == '':
                    error_list.append((config, 'Error during writing to file: {}'.format(config)))

        if error_list:
            self.expected_errmsg = ('The files below have not been modified '
                                    '(error message included):' + ''.join(
                                    ['\n    - {}: {}'.format(err[0], err[1])
                                    for err in error_list]))


@pytest.mark.parametrize('rpms', packages)
def test_update_vim(rpms):
    logger = MockLogger()
    installed_packages = MockPackageSet()

    installed_packages.add_packages(rpms)

    expected = ExpectedOutput()
    expected.create(rpms)

    library.update_vim(logger.debug,
                       logger.error,
                       installed_packages.is_installed,
                       installed_packages.append_content)

    assert expected.debugmsg == logger.debugmsg
    assert expected.errmsg == logger.errmsg
