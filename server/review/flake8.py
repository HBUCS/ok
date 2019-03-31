from . import execute, Tool, make_tempfile, is_exe_in_path


class Flake8(Tool):
    @classmethod
    def check_dependencies(cls):
        return is_exe_in_path('flake8')

    def handle_files(self):
        for filename, data in self.contents.items():
            if not filename.lower().endswith('.py'):
                continue
            path = make_tempfile(data)
            output = execute(
                [
                    'flake8',
                    '--exit-zero',
                    '--max-line-length=%s' % self.settings['max_line_length'],
                    '--ignore=%s' % self.settings['ignore'],
                    path,
                ],
                split_lines=True)

            for line in output:
                line = line[len(path) + 1:]
                line_num, column, message = line.split(':', 2)
                self.comment(filename, int(line_num), message.strip())
