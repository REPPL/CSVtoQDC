import csv
import logging
import os
import uuid

from datetime import datetime
from itertools import cycle


class Code:
    """Class for a single code or category of codes.
    """

    def generate_uuid(self):
        """Generates a random unique identifier.
        """
        return str(uuid.uuid4())

    def __init__(self, name, colour=None, isCodable=True,
                 isCategory=False, description=None):
        self.guid = self.generate_uuid()
        self.name = name
        self._colour = colour
        self._isCodable = isCodable
        self._isCategory = isCategory
        self._description = description

    @property
    def isCodable(self):
        """Returns 'true' or 'false' depending on whether
        this code is 'codable'.(Default == 'true')
        """
        if self._isCodable:
            return 'true'
        else:
            return 'false'

    @property
    def isCategory(self):
        """Returns '/' if this code is a category (i.e, collection of codes)
        or '' if it is a code. (Default == '')
        """
        if self._isCategory:
            return ''
        else:
            return '/'

    @property
    def description(self):
        """Returns the XML for description.
        """
        if self._description:
            return f'><Description>{self._description}</Description></Code>'
        else:
            return f'{self.isCategory}>'

    @property
    def colour(self):
        """Returns XML code for colour if a colour has been specified.
        Returns '' otherwise.
        """
        if self._colour:
            return f'color="{self._colour}" '
        else:
            return ''

    @property
    def text(self):
        """Returns XML for this code. (Incl. colour, unique ID, etc.)
        """
        return f"""
<Code {self.colour}guid="{self.guid}" isCodable="{self.isCodable}" name="{self.name}"{self.description}
    """.strip()


class CodeClosure:
    """Requires for properly formatting XML.
    """
    def __init__(self):
        self.text = '</Code>'


class Codebook:
    """Class for the QDC codebook.
    """

    HEADER = """
<?xml version="1.0" encoding="UTF-8" standalone="no" ?><CodeBook origin="NVivo 12 For Mac" xmlns="urn:QDA-XML:codebook:1:0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="urn:QDA-XML:codebook:1:0 Codebook.xsd"><Codes>
    """.strip()

    FOOTER = """
</Codes></CodeBook>
    """.strip()

    # LIME, RED, YELLOW, BLUE, TEAL, AQUA, FUCHSIA, GREEN
    # https://html-color.codes/
    COLOURS = [
        '#00FF00', '#FF0000', '#FFFF00', '#0000FF',
        '#008080', '#00FFFF', '#FF00FF', '#008000'
    ]

    GENERIC = 'nodes'

    DIRECTORY = {
        'import': 'import',
        'export': 'export',
        'errors': 'export/errors'}

    def __init__(self, project_name):
        self.error_logger = Codebook.set_error_logger(project_name)
        projects = self.read_project_files()
        if project_name in projects.keys():
            self.name = project_name
            self._clsts = projects[self.name]
            self._codes = self.load_clsts()
        else:
            self.name = None

    @staticmethod
    def set_error_logger(project_name):
        """Acknowledgement:
        https://stackoverflow.com/questions/55169364/
        python-how-to-write-error-in-the-console-in-txt-file
        """

        logger = logging.getLogger(project_name)
        logger.setLevel(logging.INFO)
        directory = f'{Codebook.DIRECTORY["errors"]}'
        if not os.path.exists(directory):
            os.makedirs(directory)
        fh = logging.FileHandler(f'{directory}/{project_name}.txt')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '\n\n%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    def read_project_files(self):
        """Reads available projects and corresponding CSV files.
        """
        projects = {}
        directory = f'{os.getcwd()}/{Codebook.DIRECTORY["import"]}'
        for path, p, _ in os.walk(directory):
            for project in p:
                projects[project] = []
                for path, _, f in os.walk(f'{directory}/{project}'):
                    for code_list in f:
                        try:
                            lst = code_list.split('.')
                            projects[project].append(lst[0]).lower()
                        except AttributeError as e:
                            self.error_logger.exception(e)
                # Remove empty entries
                code_list = [cl for cl in projects[project] if cl]
                projects[project] = code_list
        print(projects)
        for project, code_lists in projects.items():
            projects[project] = sorted(code_lists)
        return projects

    def load_clsts(self):
        """
        """
        directory = f'{os.getcwd()}/{Codebook.DIRECTORY["import"]}/{self.name}'
        descriptions = {}
        codes = []
        if Codebook.GENERIC in self._clsts:
            temp = [lst for lst in self._clsts if lst != Codebook.GENERIC]
            with open(f'{directory}/{Codebook.GENERIC}.csv') as f:
                for row in csv.reader(f):
                    try:
                        label = row[0].lower()
                        description = row[1]
                    except Exception as e:
                        self.error_logger.exception(e)
                        label = row[0].lower()
                        description = None
                    temp.append(label)
                    descriptions[label] = description
        else:
            temp = self._clsts
        colours = cycle(Codebook.COLOURS)
        for code in sorted(temp):
            if code in self._clsts:
                codes.append(
                    Code(code.title(), colour=next(colours), isCategory=True))
                with open(f'{directory}/{code}.csv') as f:
                    for row in csv.reader(f):
                        try:
                            label, description = row
                            codes.append(Code(
                                label.title(), description=description))
                        except ValueError as e:
                            self.error_logger.exception(e)
                            codes.append(
                                Code(row[0].title(), colour='#C0C0C0'))
                codes.append(CodeClosure())
            else:
                codes.append(
                    Code(code.title(), description=descriptions[code]))
        return codes

    @property
    def codes(self):
        """Returns text string with XML for all codes
        in this codebook.
        """
        return ''.join(code.text for code in self._codes)

    @property
    def text(self):
        """Returns text string with XML for this codebook.
        (This includes header and footer text.)
        """
        return f'{Codebook.HEADER}{self.codes}{Codebook.FOOTER}'

    def __str__(self):
        return self.text

    def write(self):
        """Writes codebook as QDC to export directory.
        """
        if not self.name:
            return False
        directory = f'{os.getcwd()}/{Codebook.DIRECTORY["export"]}/{self.name}'
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            filename = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f'{directory}/{filename}.qdc'
            with open(f'{filename}', 'w') as f:
                f.write(self.text)
            return filename
        except Exception as e:
            self.error_logger.exception(e)


def main():
    pass


if __name__ == '__main__':
    main()
