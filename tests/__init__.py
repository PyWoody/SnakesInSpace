import copy
import httpx
import os

DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


class GenericSideEffect:

    def __init__(self, data):
        self.orig_data = data
        self.data = copy.deepcopy(self.orig_data)

    def __call__(self, request, route):
        return httpx.Response(200, json=self.data)

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()

    def reset(self):
        self.data = copy.deepcopy(self.orig_data)


def attribute_test(response, data, parents=''):
    for k, v in data.items():
        if isinstance(v, dict):
            if parents:
                _parents = f'{parents}.{k}'
            else:
                _parents = k
            attribute_test(response, v, parents=_parents)
        elif isinstance(v, list):
            for idx, child in enumerate(v):
                if isinstance(child, dict):
                    if parents:
                        _parents = f'{parents}.{k}[{idx}]'
                    else:
                        _parents = f'{k}[{idx}]'
                    attribute_test(response, child, parents=_parents)
                else:
                    if parents:
                        assert eval(f'response.{parents}.{k}[{idx}]') == v[idx]
                    else:
                        assert eval(f'response.{k}[{idx}]') == v[idx]
        else:
            if parents:
                assert eval(f'response.{parents}.{k}') == v
            else:
                assert eval(f'response.{k}') == v
