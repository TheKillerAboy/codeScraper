import asyncio
import logging
import os
import webbrowser

from fire import Fire
from pathlib import Path
import sys
from bs4 import BeautifulSoup
import aiohttp as aiohttp
import yaml
import aiofiles as aiof
from boltons import strutils



class Scrapper:
    if getattr(sys, 'frozen', False):
        CONFIG_FILE_DIR = Path(sys._MEIPASS)/'config.yaml'
    else:
        CONFIG_FILE_DIR = Path(sys.argv[0])/'..'/'config.yaml'
    def __init__(self):
        self.load_config()
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

        self.source_dir = self.make_directory(None if 'source_dir' not in kwargs else kwargs['source_dir'], Path(sys.argv[0])/'..')

        self.file_extensions = self.update_non_exist_keys(None if 'file_extensions' not in kwargs else kwargs['file_extensions'], self.config['file-extensions']['defaults'])

        self.programming_language = self.config['programming-language']['default'] if 'programming_language' not in kwargs else kwargs['programming_language']

        self.template_dir = self.make_directory(None if 'template_dir' not in kwargs else kwargs['template_dir'], self.config['template-file'][self.programming_language])
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

    def load_config(self):
        with open(self.CONFIG_FILE_DIR,'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

    async def get_contest_problems(self):
        self.logger.info(f'Finding Problems for contest_id: {self.contest_id}')
        async with aiohttp.ClientSession() as session:
            async with session.get(self.config['codeforces-urls']['contest-url'].format(contest_id=self.contest_id)) as response:
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

    async def get_problem_data(self, problem_id):
        self.logger.info(f'Collecting I/O for contest_id: {self.contest_id}, problem_id: {problem_id}')
        loop = asyncio.get_event_loop()
        tasks = []
        async with aiohttp.ClientSession() as session:
            async with session.get(self.config['codeforces-urls']['problem-url'].format(contest_id=self.contest_id, problem_id=problem_id)) as response:

                soup = BeautifulSoup(await response.text(), 'html.parser')
                title = soup.select_one('div.title').text

                for i, input in enumerate(soup.select('div.sample-test>div.input')):
                    data = input.select_one('pre').text
                    tasks.append(loop.create_task(self.write_file(title,'input',data,number=i)))

                for i, output in enumerate(soup.select('div.sample-test>div.output')):
                    data = input.select_one('pre').text
                    tasks.append(loop.create_task(self.write_file(title,'output',data,number=i)))

                tasks.append(loop.create_task(self.write_file(title,self.programming_language,self.template_data)))

        await asyncio.gather(*tasks)

    async def run(self, *args, **kwargs):
        await self.handle_inputs(*args, **kwargs)

        loop = asyncio.get_event_loop()
        tasks = []
        async for problem_id in self.get_contest_problems():
            tasks.append(loop.create_task(self.get_problem_data(problem_id)))
        await asyncio.gather(*tasks)

class FireOperator:
    def __init__(self):
        self.scrapper = Scrapper()
        self.loop = asyncio.get_event_loop()

    def get_contest(self, *args, **kwargs):
        self.loop.run_until_complete(self.scrapper.run(*args, **kwargs))

    def open_config(self):
        webbrowser.open_new_tab(Scrapper.CONFIG_FILE_DIR)

if __name__ == '__main__':
    Fire(FireOperator)