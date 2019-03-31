import os
import plistlib
import shlex

from . import execute, is_exe_in_path, RepositoryTool, make_tempfile


class Clang(RepositoryTool):
    @classmethod
    def check_dependencies(cls):
        return is_exe_in_path('clang')

    def handle_files(self):
        for filename in self.contents.keys():
            if not filename.lower().endswith(('.c', '.cpp', '.cxx', '.m', '.mm')):
                continue

            path = os.path.join(self.workdir, filename)

            additional_args = []
            configured_args = self.settings.get('cmdline_args')

            if configured_args:
                additional_args = shlex.split(configured_args)

            outfile = make_tempfile()

            command = ['clang', '-S', '--analyze']

            if filename.endswith('.m'):
                command.append('-ObjC')
            elif filename.endswith('.mm'):
                command.append('-ObjC++')

            command += additional_args
            command += [path, '-Xanalyzer', '-analyzer-output=plist', '-o',
                        outfile]

            self.output = execute(command, ignore_errors=True)

            results = plistlib.load(outfile)

            for diagnostic in results['diagnostics']:
                file_index = diagnostic['location']['file']
                _filename = results['files'][file_index]

                if _filename != filename:
                    continue

                line, num_lines = self._find_linenums(diagnostic)
                self.comment(diagnostic['description'], line, num_lines)

    def _find_linenums(self, diagnostic):
        """Find and return the given line numbers.
        Args:
            diagnostic (dict):
                The diagnostic to find the line numbers for.
        Returns:
            tuple of int:
            A 2-tuple, consisting of the line number and the number of lines
            covered by the given diagnostic.
        """
        for path_node in diagnostic.get('path', []):
            if path_node['kind'] == 'event' and 'ranges' in path_node:
                line_range = path_node['ranges'][0]
                first_line = line_range[0]['line']
                last_line = line_range[1]['line']

                return first_line, last_line - first_line + 1

        first_line = diagnostic['location']['line']
        return first_line, 1
