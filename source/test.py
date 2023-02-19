import os
import sys

from CSVtoQDC.app import Codebook


def main():
    os.system('clear')
    projects = []
    for line in sys.argv[1:]:
        if not line.startswith('--'):
            continue
        else:
            projects.append(line[2:])
    if projects:
        print(f'\nGenerating Codebook for {len(projects)} project(s):\n')
        for i, project in enumerate(projects):
            print(f'{i+1}. Generating codebook for project "{project}" ...\n')
            filename = Codebook(project).write()
            if filename:
                print(f'--> Success! Saved as "... {filename[-40:]}"')
            else:
                print("--> Oops ... something went wrong!")
        print('\n')
    else:
        print('\nNo project specified (use --project_name).\n')


if __name__ == "__main__":
    main()
