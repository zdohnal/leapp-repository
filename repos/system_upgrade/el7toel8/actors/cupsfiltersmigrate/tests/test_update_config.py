import pytest

from leapp.libraries.actor.library import NEW_MACROS
from leapp.libraries.actor.library import update_config


testdata = (
    '\n',
    'bleblaba\n',
    'fdnfdf\nLocalQueueNamingRemoteCUPS RemoteName\n',
    'fnfngbfg\nCreateIPPPrinterQueues All\n',
    'CreateIPPPrinterQueues All\nLocalQueueNamingRemoteCUPS RemoteName\n'
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
        found = False
        if macro in self.content and self.path == path:
            found = True
        return found


def test_update_config_file_errors():
    path = 'foo'

    f = MockFile(path, content='')

    with pytest.raises(IOError):
        update_config('bar', f.exists, f.append)

    assert f.content == ''


@pytest.mark.parametrize('content', testdata)
def test_update_config_append_into_file(content):
    path = 'bar'
    f = MockFile(path, content)

    macros = []
    for macro in NEW_MACROS:
        if not f.exists(path, macro):
            macros.append(macro)

    fmt_input = ''
    if macros:
        fmt_input = "\n{comment_line}\n{content}\n".format(comment_line='# content added by Leapp',
                                                           content='\n'.join(macros))
    update_config(path, f.exists, f.append)

    assert f.content == content + fmt_input
