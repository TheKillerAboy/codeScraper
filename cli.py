import asyncio
import glob
import logging
import os
import string
import subprocess
import webbrowser

from fire import Fire
from pathlib import Path
import sys
from bs4 import BeautifulSoup
import aiohttp as aiohttp
import yaml
import aiofiles as aiof
from boltons import strutils

if getattr(sys, 'frozen', False):
    CONFIG_FILE_DIR = Path(sys._MEIPASS) / 'config.yaml'
else:
    CONFIG_FILE_DIR = Path(sys.argv[0]) / '..' / 'config.yaml'

CONFIG_FILE_DIR = CONFIG_FILE_DIR.resolve()

with open(CONFIG_FILE_DIR,'r') as f:
    CONFIG = yaml.load(f, Loader=yaml.FullLoader)

class Scrapper:
    def __init__(self):
        self.init_logger()

    def init_logger(self):
        self.logger = logging.getLogger('Scrapper')
        self.logger.setLevel(logging.INFO)

        self.logger_handler = logging.StreamHandler(stream=sys.stdout)
        self.logger_handler.setLevel(logging.INFO)

        self.logger_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        self.logger_handler.setFormatter(self.logger_formatter)

        self.logger.addHandler(self.logger_handler)

    async def handle_inputs(self, *args, **kwargs):
        self.contest_id = args[0]

        self.source_dir = self.make_directory(None if 'source_dir' not in kwargs else kwargs['source_dir'], (Path(sys.argv[0])/'..').resolve())

        self.file_extensions = self.update_non_exist_keys(None if 'file_extensions' not in kwargs else kwargs['file_extensions'], CONFIG['file-extensions']['defaults'])

        self.programming_language = CONFIG['programming-language']['default'] if 'programming_language' not in kwargs else kwargs['programming_language']

        self.template_dir = self.make_directory(None if 'template_dir' not in kwargs else kwargs['template_dir'], CONFIG['template-file'][self.programming_language])
        self.template_data = ''
        if self.template_dir is not None:
            async with aiof.open(self.template_dir,'r') as f:
                self.template_data = ''.join(await f.readlines())


    @staticmethod
    def make_directory(val, default):
        if val is None:
            return default
        elif not isinstance(val, Path):
            return Path(val)
        return val

    @staticmethod
    def update_non_exist_keys(ori, new):
        if ori is None:
            return new
        for key in new:
            if key not in ori:
                ori[key] = new
        return ori

    async def get_contest_problems(self):
        self.logger.info(f'Finding Problems for contest_id: {self.contest_id}')
        async with aiohttp.ClientSession() as session:
            async with session.get(CONFIG['codeforces-urls']['contest-url'].format(contest_id=self.contest_id)) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                table = soup.find('table',{'class':'problems'})
                for i, tr in enumerate(table.find_all('tr', recursive=True)):
                    td = tr.find('td')
                    if td is not None:
                        a = td.find('a')
                        yield a['href'][a['href'].rfind('/')+1:]
                        await asyncio.sleep(0.1)

    async def write_file(self, name, type, data ,number=None):
        filename = f'{strutils.slugify(name)}.' \
                   f'{strutils.slugify(self.file_extensions[type])}' \
                   f'{"" if number is None else f".{strutils.slugify(str(number))}"}'

        self.logger.info(f'Writing I/O for {filename}')

        async with aiof.open(self.source_dir/filename, 'w') as f:
            await f.write(data)

    async def get_problem_data(self, problem_id, *args, create_template=True, create_inputs=True, create_outputs=True,**kwargs):
        self.logger.info(f'Collecting I/O for contest_id: {self.contest_id}, problem_id: {problem_id}')
        loop = asyncio.get_event_loop()
        tasks = []
        async with aiohttp.ClientSession() as session:
            async with session.get(CONFIG['codeforces-urls']['problem-url'].format(contest_id=self.contest_id, problem_id=problem_id)) as response:

                soup = BeautifulSoup(await response.text(), 'html.parser')
                title = soup.select_one('div.title').text

                if create_inputs:
                    for i, input in enumerate(soup.select('div.sample-test>div.input')):
                        data = input.select_one('pre').text
                        tasks.append(loop.create_task(self.write_file(title,'input',data,number=i)))

                if create_outputs:
                    for i, output in enumerate(soup.select('div.sample-test>div.output')):
                        data = output.select_one('pre').text
                        tasks.append(loop.create_task(self.write_file(title,'output',data,number=i)))
                if create_template:
                    tasks.append(loop.create_task(self.write_file(title,self.programming_language,self.template_data)))

        await asyncio.gather(*tasks)

    async def run(self, *args, **kwargs):
        await self.handle_inputs(*args, **kwargs)

        loop = asyncio.get_event_loop()
        tasks = []
        async for problem_id in self.get_contest_problems():
            tasks.append(loop.create_task(self.get_problem_data(problem_id, *args, **kwargs)))
        await asyncio.gather(*tasks)

class FireOperator:
    def __init__(self):
        self.scrapper = Scrapper()
        self.loop = asyncio.get_event_loop()

    def get_contest(self, *args, **kwargs):
        self.loop.run_until_complete(self.scrapper.run(*args, **kwargs))

    def open_config(self):
        try:
            webbrowser.open_new_tab(CONFIG_FILE_DIR)
        except:
            print(f'Can\'t open file, directory: {CONFIG_FILE_DIR.resolve().absolute()}')

    def run_inputs(self, full_cpp_file):
        def get_command(command, **formating):
            if sys.platform not in CONFIG['commands'][command]:
                print(f'Edit Config: no {command} command for {sys.platform}')
                sys.exit()
            return CONFIG['commands'][command][sys.platform].format(**formating)

        def tokenize(data):
            data = (''.join(map(lambda k: k if k not in string.whitespace else ' ', data))).replace('  ',' ')
            data = list(filter(lambda k:k !='',data.split(' ')))
            return data

        def read_output_file(file):
            with open(file,'r') as f:
                data = ''.join(f.readlines())
            return data

        full_cpp_file = Path(full_cpp_file).resolve().absolute()
        directory = full_cpp_file.parent
        base_file = full_cpp_file.stem
        full_exe_file = directory/(f'{base_file}'+get_command('extension'))

        compile_cmd = get_command('gpp-compile',cpp=f'"{full_cpp_file}"',exe=f'"{full_exe_file}"')
        print(f'Compiling {full_exe_file.name}')

        cmd_p = subprocess.Popen(compile_cmd, shell=True)
        cmd_p.wait()

        if cmd_p.returncode != 0:
            print(f'Compiling Failed: {full_exe_file.name}')
            exit()
        else:
            print(f'Compiling Complete: {full_exe_file.name}')

        for full_input_file in map(Path,glob.glob(str(directory/f'{base_file}.in.*'), recursive=False)):
            run_inputs_cmd = get_command('run-inputs',input=f'"{full_input_file}"',exe=f'"{full_exe_file}"')

            print('-----------')
            print(full_input_file.name)
            print('-----------')

            input_p = subprocess.Popen(run_inputs_cmd, shell=True, stdout=subprocess.PIPE)
            input_p.wait()
            output = input_p.communicate()[0]
            sys.stdout.write(output.decode())

            file_index = full_input_file.suffix

            program_outputs = tokenize(output.decode())
            try:
                output_data = read_output_file(directory/f'{base_file}.out{file_index}')
                expected_outputs = tokenize(output_data)

                correct = 'Correct' if program_outputs == expected_outputs else 'Incorrect'

            except FileNotFoundError:
                correct = f'Output {base_file}.out{file_index} not found'

            print('-----------')
            print(correct)

            if correct == 'Incorrect':
                print('-----------\nExpected Output:')
                print(output_data)

            if(input_p.returncode!=0):
                print(f'Error has occurred with input file {full_input_file.name}')

            print('-----------\n\n')


if __name__ == '__main__':
    Fire(FireOperator)