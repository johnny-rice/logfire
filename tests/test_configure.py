from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Mapping

import pytest
import requests
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from requests.adapters import HTTPAdapter

import logfire
from logfire._config import (
    GLOBAL_CONFIG,
    ConsoleOptions,
    LogfireConfig,
    LogfireConfigError,
    configure,
)
from logfire.testing import IncrementalIdGenerator, TestExporter, TimeGenerator


class StubAdapter(HTTPAdapter):
    """
    A Transport Adapter that stores all requests sent, and provides pre-canned responses.
    """

    def __init__(self, requests: list[requests.PreparedRequest], responses: Iterable[requests.Response]) -> None:
        self.requests = requests
        self.responses = iter(responses)
        super().__init__()

    def send(
        self,
        request: requests.PreparedRequest,
        stream: bool = False,
        timeout: None | float | tuple[float, float] | tuple[float, None] = None,
        verify: bool | str = True,
        cert: None | bytes | str | tuple[bytes | str, bytes | str] = None,
        proxies: Mapping[str, str] | None = None,
    ) -> requests.Response:
        self.requests.append(request)
        return next(self.responses)


def test_propagate_config_to_tags() -> None:
    time_generator = TimeGenerator()
    exporter = TestExporter()

    tags1 = logfire.tags('tag1', 'tag2')

    configure(
        send_to_logfire=False,
        console=ConsoleOptions(enabled=False),
        ns_timestamp_generator=time_generator,
        id_generator=IncrementalIdGenerator(),
        processors=[SimpleSpanProcessor(exporter)],
    )

    tags2 = logfire.tags('tag3', 'tag4')

    for lf in (logfire, tags1, tags2):
        with lf.span('root'):
            with lf.span('child'):
                logfire.info('test1')
                tags1.info('test2')
                tags2.info('test3')

    # insert_assert(exporter.exported_spans_as_dict(_include_start_spans=True))
    assert exporter.exported_spans_as_dict(_include_start_spans=True) == [
        {
            'name': 'root (start)',
            'context': {'trace_id': 1, 'span_id': 2, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 1, 'is_remote': False},
            'start_time': 1000000000,
            'end_time': 1000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'root',
                'logfire.msg': 'root',
                'logfire.span_type': 'start_span',
                'logfire.start_parent_id': '0',
            },
        },
        {
            'name': 'child (start)',
            'context': {'trace_id': 1, 'span_id': 4, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 3, 'is_remote': False},
            'start_time': 2000000000,
            'end_time': 2000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'child',
                'logfire.msg': 'child',
                'logfire.span_type': 'start_span',
                'logfire.start_parent_id': '1',
            },
        },
        {
            'name': 'test1',
            'context': {'trace_id': 1, 'span_id': 5, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 3, 'is_remote': False},
            'start_time': 3000000000,
            'end_time': 3000000000,
            'attributes': {
                'logfire.span_type': 'log',
                'logfire.level': 'info',
                'logfire.msg_template': 'test1',
                'logfire.msg': 'test1',
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
            },
        },
        {
            'name': 'test2',
            'context': {'trace_id': 1, 'span_id': 6, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 3, 'is_remote': False},
            'start_time': 4000000000,
            'end_time': 4000000000,
            'attributes': {
                'logfire.span_type': 'log',
                'logfire.level': 'info',
                'logfire.msg_template': 'test2',
                'logfire.msg': 'test2',
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.tags': ('tag1', 'tag2'),
            },
        },
        {
            'name': 'test3',
            'context': {'trace_id': 1, 'span_id': 7, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 3, 'is_remote': False},
            'start_time': 5000000000,
            'end_time': 5000000000,
            'attributes': {
                'logfire.span_type': 'log',
                'logfire.level': 'info',
                'logfire.msg_template': 'test3',
                'logfire.msg': 'test3',
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.tags': ('tag3', 'tag4'),
            },
        },
        {
            'name': 'child',
            'context': {'trace_id': 1, 'span_id': 3, 'is_remote': False},
            'parent': {'trace_id': 1, 'span_id': 1, 'is_remote': False},
            'start_time': 2000000000,
            'end_time': 6000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'child',
                'logfire.span_type': 'span',
                'logfire.msg': 'child',
            },
        },
        {
            'name': 'root',
            'context': {'trace_id': 1, 'span_id': 1, 'is_remote': False},
            'parent': None,
            'start_time': 1000000000,
            'end_time': 7000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'root',
                'logfire.span_type': 'span',
                'logfire.msg': 'root',
            },
        },
        {
            'name': 'root (start)',
            'context': {'trace_id': 2, 'span_id': 9, 'is_remote': False},
            'parent': {'trace_id': 2, 'span_id': 8, 'is_remote': False},
            'start_time': 8000000000,
            'end_time': 8000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'root',
                'logfire.msg': 'root',
                'logfire.tags': ('tag1', 'tag2'),
                'logfire.span_type': 'start_span',
                'logfire.start_parent_id': '0',
            },
        },
        {
            'name': 'child (start)',
            'context': {'trace_id': 2, 'span_id': 11, 'is_remote': False},
            'parent': {'trace_id': 2, 'span_id': 10, 'is_remote': False},
            'start_time': 9000000000,
            'end_time': 9000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'child',
                'logfire.msg': 'child',
                'logfire.tags': ('tag1', 'tag2'),
                'logfire.span_type': 'start_span',
                'logfire.start_parent_id': '8',
            },
        },
        {
            'name': 'test1',
            'context': {'trace_id': 2, 'span_id': 12, 'is_remote': False},
            'parent': {'trace_id': 2, 'span_id': 10, 'is_remote': False},
            'start_time': 10000000000,
            'end_time': 10000000000,
            'attributes': {
                'logfire.span_type': 'log',
                'logfire.level': 'info',
                'logfire.msg_template': 'test1',
                'logfire.msg': 'test1',
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
            },
        },
        {
            'name': 'test2',
            'context': {'trace_id': 2, 'span_id': 13, 'is_remote': False},
            'parent': {'trace_id': 2, 'span_id': 10, 'is_remote': False},
            'start_time': 11000000000,
            'end_time': 11000000000,
            'attributes': {
                'logfire.span_type': 'log',
                'logfire.level': 'info',
                'logfire.msg_template': 'test2',
                'logfire.msg': 'test2',
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.tags': ('tag1', 'tag2'),
            },
        },
        {
            'name': 'test3',
            'context': {'trace_id': 2, 'span_id': 14, 'is_remote': False},
            'parent': {'trace_id': 2, 'span_id': 10, 'is_remote': False},
            'start_time': 12000000000,
            'end_time': 12000000000,
            'attributes': {
                'logfire.span_type': 'log',
                'logfire.level': 'info',
                'logfire.msg_template': 'test3',
                'logfire.msg': 'test3',
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.tags': ('tag3', 'tag4'),
            },
        },
        {
            'name': 'child',
            'context': {'trace_id': 2, 'span_id': 10, 'is_remote': False},
            'parent': {'trace_id': 2, 'span_id': 8, 'is_remote': False},
            'start_time': 9000000000,
            'end_time': 13000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'child',
                'logfire.tags': ('tag1', 'tag2'),
                'logfire.span_type': 'span',
                'logfire.msg': 'child',
            },
        },
        {
            'name': 'root',
            'context': {'trace_id': 2, 'span_id': 8, 'is_remote': False},
            'parent': None,
            'start_time': 8000000000,
            'end_time': 14000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'root',
                'logfire.tags': ('tag1', 'tag2'),
                'logfire.span_type': 'span',
                'logfire.msg': 'root',
            },
        },
        {
            'name': 'root (start)',
            'context': {'trace_id': 3, 'span_id': 16, 'is_remote': False},
            'parent': {'trace_id': 3, 'span_id': 15, 'is_remote': False},
            'start_time': 15000000000,
            'end_time': 15000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'root',
                'logfire.msg': 'root',
                'logfire.tags': ('tag3', 'tag4'),
                'logfire.span_type': 'start_span',
                'logfire.start_parent_id': '0',
            },
        },
        {
            'name': 'child (start)',
            'context': {'trace_id': 3, 'span_id': 18, 'is_remote': False},
            'parent': {'trace_id': 3, 'span_id': 17, 'is_remote': False},
            'start_time': 16000000000,
            'end_time': 16000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'child',
                'logfire.msg': 'child',
                'logfire.tags': ('tag3', 'tag4'),
                'logfire.span_type': 'start_span',
                'logfire.start_parent_id': '15',
            },
        },
        {
            'name': 'test1',
            'context': {'trace_id': 3, 'span_id': 19, 'is_remote': False},
            'parent': {'trace_id': 3, 'span_id': 17, 'is_remote': False},
            'start_time': 17000000000,
            'end_time': 17000000000,
            'attributes': {
                'logfire.span_type': 'log',
                'logfire.level': 'info',
                'logfire.msg_template': 'test1',
                'logfire.msg': 'test1',
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
            },
        },
        {
            'name': 'test2',
            'context': {'trace_id': 3, 'span_id': 20, 'is_remote': False},
            'parent': {'trace_id': 3, 'span_id': 17, 'is_remote': False},
            'start_time': 18000000000,
            'end_time': 18000000000,
            'attributes': {
                'logfire.span_type': 'log',
                'logfire.level': 'info',
                'logfire.msg_template': 'test2',
                'logfire.msg': 'test2',
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.tags': ('tag1', 'tag2'),
            },
        },
        {
            'name': 'test3',
            'context': {'trace_id': 3, 'span_id': 21, 'is_remote': False},
            'parent': {'trace_id': 3, 'span_id': 17, 'is_remote': False},
            'start_time': 19000000000,
            'end_time': 19000000000,
            'attributes': {
                'logfire.span_type': 'log',
                'logfire.level': 'info',
                'logfire.msg_template': 'test3',
                'logfire.msg': 'test3',
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.tags': ('tag3', 'tag4'),
            },
        },
        {
            'name': 'child',
            'context': {'trace_id': 3, 'span_id': 17, 'is_remote': False},
            'parent': {'trace_id': 3, 'span_id': 15, 'is_remote': False},
            'start_time': 16000000000,
            'end_time': 20000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'child',
                'logfire.tags': ('tag3', 'tag4'),
                'logfire.span_type': 'span',
                'logfire.msg': 'child',
            },
        },
        {
            'name': 'root',
            'context': {'trace_id': 3, 'span_id': 15, 'is_remote': False},
            'parent': None,
            'start_time': 15000000000,
            'end_time': 21000000000,
            'attributes': {
                'code.filepath': 'test_configure.py',
                'code.lineno': 123,
                'code.function': 'test_propagate_config_to_tags',
                'logfire.msg_template': 'root',
                'logfire.tags': ('tag3', 'tag4'),
                'logfire.span_type': 'span',
                'logfire.msg': 'root',
            },
        },
    ]


def test_set_request_headers() -> None:
    time_generator = TimeGenerator()

    session = requests.Session()
    response = requests.Response()
    response._content = b'\n\x00'
    response.status_code = 200
    responses = [response] * 5
    adapter = StubAdapter(requests=[], responses=responses)
    session.adapters['https://'] = adapter

    configure(
        send_to_logfire=True,
        console=ConsoleOptions(enabled=False),
        ns_timestamp_generator=time_generator,
        id_generator=IncrementalIdGenerator(),
        default_otlp_span_exporter_request_headers={'X-Test': 'test'},
        default_otlp_span_exporter_session=session,
        default_processor=SimpleSpanProcessor,
        logfire_token='123',
    )

    with logfire.span('root'):
        with logfire.span('child'):
            logfire.info('test1')

    # insert_assert([r.headers.get('X-Test', None) for r in adapter.requests])
    assert [r.headers.get('X-Test', None) for r in adapter.requests] == ['test', 'test', 'test', 'test', 'test']


def test_read_config_from_pyproject_toml(tmp_path: Path) -> None:
    (tmp_path / 'pyproject.toml').write_text(
        f"""
        [tool.logfire]
        logfire_api_root = "https://api.logfire.io"
        send_to_logfire = false
        project_name = "test"
        logfire_console_colors = "never"
        logfire_console_include_timestamp = false
        console_colors = "never"
        logfire_dir = "{tmp_path}"
        collect_system_metrics = false
        """
    )

    configure(config_dir=tmp_path)

    assert GLOBAL_CONFIG.logfire_api_root == 'https://api.logfire.io'
    assert GLOBAL_CONFIG.send_to_logfire is False
    assert GLOBAL_CONFIG.project_name == 'test'
    assert GLOBAL_CONFIG.console.colors == 'never'
    assert GLOBAL_CONFIG.console.include_timestamps is False
    assert GLOBAL_CONFIG.logfire_dir == tmp_path
    assert GLOBAL_CONFIG.collect_system_metrics is False


def test_logfire_config_console_options() -> None:
    assert LogfireConfig().console == ConsoleOptions()
    assert LogfireConfig(console=ConsoleOptions(enabled=False)).console == ConsoleOptions(enabled=False)
    assert LogfireConfig(console=ConsoleOptions(colors='never', verbose=True)).console == ConsoleOptions(
        colors='never', verbose=True
    )

    os.environ['LOGFIRE_CONSOLE_COLORS'] = 'never'
    assert LogfireConfig().console == ConsoleOptions(colors='never')
    os.environ['LOGFIRE_CONSOLE_COLORS'] = 'test'
    with pytest.raises(
        LogfireConfigError,
        match="Expected console_colors to be one of \\('auto', 'always', 'never'\\), got 'test'",
    ):
        LogfireConfig()

    os.environ.pop('LOGFIRE_CONSOLE_COLORS')

    os.environ['LOGFIRE_CONSOLE_VERBOSE'] = '1'
    assert LogfireConfig().console == ConsoleOptions(verbose=True)
    os.environ['LOGFIRE_CONSOLE_VERBOSE'] = 'test'
    assert LogfireConfig().console == ConsoleOptions(verbose=False)
    os.environ.pop('LOGFIRE_CONSOLE_VERBOSE')
