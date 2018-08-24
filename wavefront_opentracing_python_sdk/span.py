from __future__ import division

import threading
import time
from opentracing import Span
from wavefront_opentracing_python_sdk import WavefrontSpanContext
from wavefront_python_sdk.common.utils import is_blank


class WavefrontSpan(Span):
    def __init__(self, tracer, operation_name, context, start_time, parents,
                 follows, tags):
        """

        :param tracer:
        :param operation_name:
        :param context:
        :type context: WavefrontSpanContext
        :param start_time:
        :param parents:
        :param follows:
        :param tags:
        """
        super(WavefrontSpan, self).__init__(tracer=tracer, context=context)
        self._context = context
        self.operation_name = operation_name
        self.start_time = start_time
        self.duration_time = 0
        self.parents = parents
        self.follows = follows
        self.tags = tags
        self._finished = False
        self.update_lock = threading.Lock()

    @property
    def context(self):
        return self._context

    def set_tag(self, key, value):
        with self.update_lock:
            if not is_blank(key) and value:
                self.tags.append((key, value))
        return self

    def set_baggage_item(self, key, value):
        new_context = self._context.with_baggage_item(key=key, value=value)
        with self.update_lock:
            self._context = new_context
        return self

    def get_baggage_item(self, key):
        return self._context.get_baggage_item(key)

    def set_operation_name(self, operation_name):
        with self.update_lock:
            self.operation_name = operation_name
        return self

    def finish(self, finish_time=None):
        if finish_time:
            self._do_finish(finish_time - self.start_time)
        else:
            self._do_finish(time.time() - self.start_time)

    def _do_finish(self, duration_time):
        with self.update_lock:
            if self._finished:
                return
            self.duration_time = duration_time
            self._finished = True
        self.tracer.report_span(self)

    @property
    def trace_id(self):
        return self._context.trace_id

    @property
    def span_id(self):
        return self._context.span_id

    def get_operation_name(self):
        return self.operation_name

    def get_start_time(self):
        return self.start_time

    def get_duration_time(self):
        return self.duration_time

    def get_parents(self):
        if not self.parents:
            return []
        return self.parents

    def get_follows(self):
        if not self.follows:
            return []
        return self.follows

    def get_tags(self):
        if not self.tags:
            return []
        return self.tags