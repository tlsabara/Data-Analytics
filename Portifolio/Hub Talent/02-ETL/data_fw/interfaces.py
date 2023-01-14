from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
import random


class InterfaceCrawler(ABC):
    ACCEPTED_KWARGS = []

    def __new__(cls, *args, **kwargs) -> object:
        invalid = [1 if k not in cls.ACCEPTED_KWARGS else 0 for k in kwargs]
        try:
            invalid.index(1)
        except ValueError as e:
            if len(args) > 1:
                raise ValueError('Invalid usage. ARGS cannot be used.')
            return super().__new__(cls)
        else:
            raise ValueError('Invalid usage. One or more KWARGS Unreconized.')

    def __init__(self, **kwargs) -> None:
        print('init', kwargs)
        self.__clock_start: time = None
        self.__clock_stop: time = None
        self.__exec_locker: bool = False
        self.async_load_return = None
        self.async_extract_return = None
        self.async_transform_return = None
        self.__async_queue: asyncio.Queue = None
        self.__async_tasklist: list[asyncio.Task] = []
        for k, val in kwargs.items():
            setattr(self, k, val)

    def start_crawler(self) -> None:
        self.__timer_start()

        self.__before_exec_extract()
        self._data_extract()
        self.__after_exec_extract()

        self.__before_exec_transform()
        self._data_transform()
        self.__after_exec_transform()

        self.__before_exec_load()
        self._data_load()
        self.__after_exec_load()

        self.__timer_stop()

    async def _async_mount(self):
        ...

    def async_exec(self) -> None:
        asyncio.run(self._async_controller())

    async def _async_controller(self) -> None:
        self.__async_queue = asyncio.Queue()
        await self._async_mount()
        await asyncio.gather(*self.__async_tasklist)

    async def _async_add_task(self, task, *args, **kwargs):
        self.__async_tasklist.append(
            asyncio.create_task(
                task(etl_mode=kwargs.get('etl_mode'), n=kwargs.get('n'))
            )
        )

    async def _async_chain(self, etl_mode: str = None, async_chain: list | tuple = None, *args, **kwargs) -> None:
        accpt = ['load', 'transform', 'extract', 'chain']
        if etl_mode not in accpt:
            self.__exec_locker = False
            raise ValueError(f'Unreconized value of etl_mode = {etl_mode}')
        # print('etl_mode', etl_mode)
        # print('kw', kwargs)
        # print('--')

        if etl_mode == 'load':
            async def inner_async(self, *args, **kwargs):
                self.__timer_start()
                # await self.__async_queue.get()
                self.async_load_return = await self._async_load(*args, **kwargs)
                self.__timer_stop()
                print(self.report())
                return self

            thrd = await inner_async(self, *args, **kwargs)
            await self.__async_queue.put(thrd)
            return

        if etl_mode == 'transform':
            async def inner_async(self, *args, **kwargs):
                self.__timer_start()
                await self.__async_queue.get()
                self.async_transform_return = await self._async_transform(*args, **kwargs)
                self.__async_queue.task_done()
                self.__timer_stop()

            return await inner_async(self, *args, **kwargs)

        if etl_mode == 'extract':
            async def inner_async(self, *args, **kwargs):
                self.__timer_start()
                await self.__async_queue.get()
                self.async_extract_return = await self._async_extract(*args, **kwargs)
                self.__async_queue.task_done()
                self.__timer_stop()
                self.__async_queue.task_done()

            return await inner_async(self, *args, **kwargs)

        if etl_mode == 'chain' and isinstance(async_chain, (list | tuple)):
            async def inner_async(self, *async_chain):
                self.__timer_start()
                await self.__async_queue.get()
                await asyncio.gather(*async_chain)
                self.__async_queue.task_done()
                self.__timer_stop()

            return await inner_async(self, *async_chain)
        else:
            raise ValueError('Type of async_chain is invalid.')

    @abstractmethod
    def _data_load(self) -> InterfaceCrawler:
        return self

    @abstractmethod
    def _data_transform(self) -> InterfaceCrawler:
        return self

    @abstractmethod
    def _data_extract(self) -> InterfaceCrawler:
        return self

    def __timer_start(self):
        self.__clock_start = time.perf_counter()
        self.__exec_locker = True
        return self

    def __timer_stop(self):
        self.__clock_stop = time.perf_counter()
        self.__exec_locker = False
        return self

    async def _async_load(self, *args, **kwargs):
        ...

    async def _async_transform(self, *args, **kwargs):
        ...

    async def _async_extract(self, *args, **kwargs):
        ...

    @property
    def duration(self):
        if self.__exec_locker:
            return "\033[91m" + 'executando'
        return self.__clock_stop - self.__clock_start

    def _before_exec_extract(self):
        ...

    def _after_exec_extract(self):
        ...

    def _before_exec_transform(self):
        ...

    def _after_exec_transform(self):
        ...

    def _before_exec_load(self):
        ...

    def _after_exec_load(self):
        ...

    def report(self):
        return "\033[91m" + f'- CRAWLER REPORT - - - - - - - - - -\n' \
               f'> Crowler class:{self.__class__.__name__}\n' \
               f'> Execution Time: {self.duration}\n' \
               f'- - - - - - - - - - - - - - - - - - '


class CrawlerUtils:
    def __new__(cls):
        raise PermissionError("CrawlerUtils can't be instance.")

    @staticmethod
    def acepted_parameters(*args):
        """
        Decorador para gravar os parametros aceitos pelo Crowler
        :param args:
        :return:
        """

        def cls_coletor(crowler_class: object):
            if not issubclass(crowler_class, InterfaceCrawler):
                raise TypeError(f'{crowler_class} must be instance or subinstance of InterfaceCrawler')

            if isinstance(args[0], str):
                crowler_class.ACCEPTED_KWARGS = [i for i in args]
            if isinstance(args[0], list):
                crowler_class.ACCEPTED_KWARGS = [i for i in args[0]]

            return crowler_class

        return cls_coletor


if __name__ == '__main__':
    @CrawlerUtils.acepted_parameters(
        'Casa',
        'Cachorro',
        'Familia',
        'dddd',
        'll'
    )
    class Test1(InterfaceCrawler):
        def _data_load(self) -> InterfaceCrawler:
            pass

        def _data_transform(self) -> InterfaceCrawler:
            pass

        def _data_extract(self) -> InterfaceCrawler:
            pass

        async def _async_mount(self) -> None:
            etl_mode = 'load'

            for n in range(500):
                await self._async_add_task(
                    self._async_chain, etl_mode=etl_mode, n=n
                )

        async def _async_load(self, *args, **kwargs):
            run = True
            limit = 30
            times = 0
            while run:
                await asyncio.sleep(1)
                run = not random.randint(1, 11) % 3 == 0 or times == limit
                times += 1
            print(f'exec: {kwargs["n"]}')


    t = Test1(ll='goleiro')
    t.async_exec()
