from concurrent.futures import ThreadPoolExecutor


class BackgroundThreadPool:
    thread_pool = None #initailly the thread pool will be empty class state management
    @classmethod
    def initialize_thread_pool(cls):
        if cls.thread_pool is None:
            cls.thread_pool = ThreadPoolExecutor(max_workers=10) #lazy initialization
            return cls.thread_pool
        else:
            raise RuntimeError('BackgroundThreadPool is already initialized')
    @classmethod
    def execute_task(cls,func,*args,**kwargs):
        try:
            if cls.thread_pool is None:
                raise RuntimeError('BackgroundThreadPool not initialized')
            else:
                 future = cls.thread_pool.submit(func,*args,**kwargs)
                 print("Task is successfully executed")
                 return future
        except Exception as e:
            raise e
    @classmethod
    def shutdown(cls):
        if cls.thread_pool is not None:
            cls.thread_pool.shutdown(wait=True)
        else:
            raise RuntimeError('BackgroundThreadPool not initialized')