import pytest

from leapp.libraries.actor.library import NEW_MACROS
from leapp.libraries.actor.library import update_config


testdata = (
    (
        '\n',
        ('\n\n# content added by Leapp\n'
         'LocalQueueNamingRemoteCUPS RemoteName\n'
         'CreateIPPPrinterQueues All\n')
    ),
    (
        'bleblaba\n',
        ('bleblaba\n\n# content added by Leapp\n'
         'LocalQueueNamingRemoteCUPS RemoteName\n'
         'CreateIPPPrinterQueues All\n')
    ),
    (
        'fdnfdf\nLocalQueueNamingRemoteCUPS RemoteName\n',
        ('fdnfdf\nLocalQueueNamingRemoteCUPS RemoteName\n\n'
         '# content added by Leapp\nCreateIPPPrinterQueues All\n')
    ),
    (
        'fnfngbfg\nCreateIPPPrinterQueues All\n',
        ('fnfngbfg\nCreateIPPPrinterQueues All\n\n'
         '# content added by Leapp\n'
         'LocalQueueNamingRemoteCUPS RemoteName\n')
    ),
    (
        ('CreateIPPPrinterQueues All\n'
         'LocalQueueNamingRemoteCUPS RemoteName\n'),
        ('CreateIPPPrinterQueues All\n'
         'LocalQueueNamingRemoteCUPS RemoteName\n')
    ),
    (
        ('# CreateIPPPrinterQueues All\n'
         '# LocalQueueNamingRemoteCUPS RemoteName\n'),
        ('# CreateIPPPrinterQueues All\n'
         '# LocalQueueNamingRemoteCUPS RemoteName\n\n'
         '# content added by Leapp\n'
         'LocalQueueNamingRemoteCUPS RemoteName\n'
         'CreateIPPPrinterQueues All\n')
    ),
    (
        'dfggfd\n# CreateIPPPrinterQueues bluff\n',
        ('dfggfd\n# CreateIPPPrinterQueues bluff\n\n'
         '# content added by Leapp\n'
         'LocalQueueNamingRemoteCUPS RemoteName\n'
         'CreateIPPPrinterQueues All\n')
    ),
    (
        'dfggfd\n CreateIPPPrinterQueues bluff\n',
        ('dfggfd\n CreateIPPPrinterQueues bluff\n\n'
         '# content added by Leapp\n'
         'LocalQueueNamingRemoteCUPS RemoteName\n')
    ),
    (
        'dfggfd\n LocalQueueNamingRemoteCUPS blaf\n',
        ('dfggfd\n LocalQueueNamingRemoteCUPS blaf\n\n'
         '# content added by Leapp\n'
         'CreateIPPPrinterQueues All\n')
    ),
    (
        ('   CreateIPPPrinterQueues All\n'
         '       LocalQueueNamingRemoteCUPS RemoteName\n'),
        ('   CreateIPPPrinterQueues All\n'
         '       LocalQueueNamingRemoteCUPS RemoteName\n')
    )
)


class MockFile(object):
    def __init__(self, path, content=None):
        self.path = path
        self.content = content
        self.error = False

    def append(self, path, content):
        if path != self.path:
            self.error = True
        if not self.error:
            self.content += content
            return self.content
        raise IOError('Error during writing to file: {}.'.format(path))

    def exists(self, path, macro):
        for line in self.content.split('\n'):
            if line.lstrip().startswith(macro) and self.path == path:
                return True
        return False


def test_update_config_file_errors():
    path = 'foo'

    f = MockFile(path, content='')

    with pytest.raises(IOError):
        update_config('bar', f.exists, f.append)

    assert f.content == ''


@pytest.mark.parametrize('content,expected', testdata)
def test_update_config_append_into_file(content, expected):
    path = 'bar'
    f = MockFile(path, content)

    update_config(path, f.exists, f.append)

    assert f.content == expected
