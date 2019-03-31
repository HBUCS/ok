import logging
import os
import shutil
import subprocess
import sys
import tempfile

from server import models, db


def execute(command,
            env=None,
            split_lines=False,
            ignore_errors=False,
            extra_ignore_errors=(),
            translate_newlines=True,
            with_errors=True,
            none_on_ignored_error=False):
    """Execute a command and return the output.
    Args:
        command (list of unicode):
            The command to run.
        env (dict, optional):
            The environment variables to use when running the process.
        split_lines (bool, optional):
            Whether to return the output as a list (split on newlines) or a
            single string.
        ignore_errors (bool, optional):
            Whether to ignore non-zero return codes from the command.
        extra_ignore_errors (tuple of int, optional):
            Process return codes to ignore.
        translate_newlines (bool, optional):
            Whether to convert platform-specific newlines (such as \\r\\n) to
            the regular newline (\\n) character.
        with_errors (bool, optional):
            Whether the stderr output should be merged in with the stdout
            output or just ignored.
        none_on_ignored_error (bool, optional):
            Whether to return ``None`` if there was an ignored error (instead
            of the process output).
    Returns:
        unicode or list of unicode:
        Either the output of the process, or a list of lines in the output,
        depending on the value of ``split_lines``.
    """
    if isinstance(command, list):
        logging.debug(subprocess.list2cmdline(command))
    else:
        logging.debug(command)

    if env:
        env.update(os.environ)
    else:
        env = os.environ.copy()

    env['LC_ALL'] = 'en_US.UTF-8'
    env['LANGUAGE'] = 'en_US.UTF-8'

    if with_errors:
        errors_output = subprocess.STDOUT
    else:
        errors_output = subprocess.PIPE

    if sys.platform.startswith('win'):
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=errors_output,
                             shell=False,
                             universal_newlines=translate_newlines,
                             env=env)
    else:
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=errors_output,
                             shell=False,
                             close_fds=True,
                             universal_newlines=translate_newlines,
                             env=env)
    if split_lines:
        data = p.stdout.readlines()
    else:
        data = p.stdout.read()

    rc = p.wait()

    if rc and not ignore_errors and rc not in extra_ignore_errors:
        raise Exception('Failed to execute command: %s\n%s' % (command, data))

    if rc and none_on_ignored_error:
        return None

    return data


def is_exe_in_path(name):
    """Check whether an executable is in the user's search path.
    Args:
        name (unicode):
            The name of the executable, without any platform-specific
            executable extension. The extension will be appended if necessary.
    Returns:
        boolean:
        True if the executable can be found in the execution path.
    """
    if sys.platform == 'win32' and not name.endswith('.exe'):
        name += '.exe'

    for dirname in os.environ['PATH'].split(os.pathsep):
        if os.path.exists(os.path.join(dirname, name)):
            return True

    return False


def ensure_dirs_exist(path):
    """Ensure directories exist to an absolute path.
    Args:
        path (unicode):
            The absolute path for which directories should be created if they
            don't exist.
    Raises:
        ValueError:
            If the path is not absolute.
        OSError:
            If making the directory failed.
    """
    if not os.path.isabs(path):
        raise ValueError

    folder_path = os.path.dirname(path)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


tmpdirs = []
tmpfiles = []


def cleanup_tempfiles():
    """Clean up all temporary files.
    This will delete all the files created by :py:func:`make_tempfile`.
    """
    global tmpdirs
    global tmpfiles

    for tmpdir in tmpdirs:
        try:
            logging.debug('Removing temporary directory %s', tmpdir)
            shutil.rmtree(tmpdir)
        except:
            pass

    for tmpfile in tmpfiles:
        try:
            logging.debug('Removing temporary file %s', tmpfile)
            os.unlink(tmpfile)
        except:
            pass

    tmpdirs = []
    tmpfiles = []


def make_tempfile(content=None, extension=''):
    """Create a temporary file and return the path.
    Args:
        content (bytes, optional):
            Optional content to put in the file.
        extension (unicode, optional):
            An optional file extension to add to the end of the filename.
    Returns:
        unicode:
        The name of the new file.
    """
    global tmpfiles
    fd, tmpfile = tempfile.mkstemp(suffix=extension)

    if content:
        if isinstance(content, str):
            content = content.encode()
        os.write(fd, content)

    os.close(fd)
    tmpfiles.append(tmpfile)
    return tmpfile


def make_tempdir():
    """Create a temporary directory and return the path.
    Returns:
        unicode:
        The name of the new directory.
    """
    global tmpdirs

    tmpdir = tempfile.mkdtemp()
    tmpdirs.append(tmpdir)
    return tmpdir


class Tool:
    def __init__(self, backup, settings):
        self.settings = settings or {}
        self.backup = backup
        file_contents = [m for m in self.backup.messages if m.kind == 'file_contents']
        if not file_contents:
            raise ValueError("No files to review")
        self.contents = file_contents[0].contents
        self.output = None

    def handle_files(self):
        raise NotImplementedError()

    @classmethod
    def check_dependencies(cls):
        raise NotImplementedError()

    def comment(self, filename, line, message):
        comment = models.Comment(
            backup=self.backup,
            author_id=0,
            filename=filename,
            line=line,
            message=message
        )
        db.session.add(comment)
        db.session.commit()


class RepositoryTool(Tool):
    def __init__(self, backup, settings):
        super(RepositoryTool, self).__init__(backup=backup, settings=settings)
        self.workdir = make_tempdir()
        for filename, data in self.contents.items():
            path = os.path.join(self.workdir, filename)
            ensure_dirs_exist(path)
            with open(path, 'w') as fp:
                fp.write(data)
