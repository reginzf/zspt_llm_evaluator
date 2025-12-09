from functools import wraps
import time


def check(n=1, msg=None, interval=5, self=None):
    # 装饰器，跑了n次还是错误的话，返回异常和msg,检查失败后默认等待5s
    def check_decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            res = None
            # 执行测试点，检查assert
            for i in range(n):
                try:
                    res = func(*args, **kwargs)
                except AssertionError as e:
                    # 检查失败，先尝试写个log
                    if self:
                        self.log.info(f'run:{i},{func.__name__} check failed, error:{e}')
                    # 最后检查没过，抛出错误
                    if i == n - 1:
                        # 先检查全局变量，这个msg可以随时修改
                        temp = globals().get('msg', None)
                        raise AssertionError(temp) if temp else AssertionError(msg)
                    # 继续跑
                    time.sleep(interval)
                    continue
                except Exception as e:
                    # 其他错误直接抛出
                    raise e
                # 检查成功，直接退出
                if self:
                    self.log.info(f'{func.__name__} check success')
                break
            return res

        return wrapped_function

    return check_decorator
