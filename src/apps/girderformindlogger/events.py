# -*- coding: utf-8 -*-
"""
This module contains the Girder events framework. It maintains a global mapping
of events to listeners, and contains utilities for callers to handle or trigger
events identified by a name.

Listeners should bind to events by calling:

    ``girderformindlogger.events.bind('event.name', 'my.handler', handlerFunction)``

And events should be fired in one of two ways; if the event should be handled
synchronously, fire it with:

    ``girderformindlogger.events.trigger('event.name', info)``

And if the event should be handled asynchronously, use:

    ``girderformindlogger.events.daemon.trigger('event.name', info, callback)``

For obvious reasons, the asynchronous method does not return a value to the
caller. Instead, the caller may optionally pass the callback argument as a
function to be called when the task is finished. That callback function will
receive the Event object as its only argument.
"""

import contextlib
import threading
from collections import OrderedDict

import six
from six.moves import queue

from apps import girderformindlogger
from apps.girderformindlogger.utility import config


class Event(object):
    """
    An Event object is created when an event is triggered. It is passed to
    each of the listeners of the event, which have a chance to add information
    to the event, and also optionally stop the event from being further
    propagated to other listeners, and also optionally instruct the caller that
    it should not execute its default behavior.
    """

    # We might have a lot of events, so we use __slots__ to make them smaller
    __slots__ = (
        "asynchronous",
        "info",
        "name",
        "propagate",
        "defaultPrevented",
        "responses",
        "currentHandlerName",
    )

    def __init__(self, name, info, asynchronous=False):
        self.name = name
        self.info = info
        self.propagate = True
        self.defaultPrevented = False
        self.responses = []
        self.currentHandlerName = None
        self.asynchronous = asynchronous

    def preventDefault(self):
        """
        This can be used to instruct the triggerer of the event that the default
        behavior it would normally perform should not be performed. The
        semantics of this action are specific to the context of the event
        being handled, but a common use of this method is for a plugin to
        provide an alternate behavior that will replace the normal way the
        event is handled by the core system.
        """
        self.defaultPrevented = True
        return self

    def stopPropagation(self):
        """
        Listeners should call this on the event they were passed in order to
        stop any other listeners to the event from being executed.
        """
        self.propagate = False
        return self

    def addResponse(self, response):
        """
        Listeners that wish to return data back to the caller who triggered this
        event should call this to append their own response to the event.

        :param response: The response value, which can be any type.
        """
        self.responses.append(response)
        return self


class ForegroundEventsDaemon(object):
    """
    This is the implementation used for ``girderformindlogger.events.daemon`` if the
    config file chooses to disable using the background thread for the daemon.
    It executes all bound handlers in the current thread, and provides
    no-op start() and stop() implementations to remain compatible with the
    API of AsyncEventsThread.
    """

    def start(self):
        pass

    def stop(self):
        pass

    def trigger(self, eventName=None, info=None, callback=None):
        if eventName is None:
            event = Event(None, info, asynchronous=False)
        else:
            event = trigger(eventName, info, asynchronous=False, daemon=True)

        if callable(callback):
            callback(event)


class AsyncEventsThread(threading.Thread):
    """
    This class is used to execute the pipeline for events asynchronously.
    This should not be invoked directly by callers; instead, they should use
    girderformindlogger.events.daemon.trigger().
    """

    def __init__(self):
        threading.Thread.__init__(self)

        self.daemon = True
        self.terminate = False
        self.eventQueue = queue.Queue()
        self.queueNotEmpty = threading.Condition()

    def run(self):
        """
        Loops over all queued events. If the queue is empty, this thread gets
        put to sleep until someone calls trigger() on it with a new event to
        dispatch.
        """
        girderformindlogger.logprint.info(
            "Started asynchronous event manager thread."
        )

        while not self.terminate:
            try:
                eventName, info, callback = self.eventQueue.get(block=False)
                if eventName is None:
                    event = Event(None, info, asynchronous=True)
                else:
                    event = trigger(
                        eventName, info, asynchronous=True, daemon=True
                    )

                if callable(callback):
                    callback(event)
            except queue.Empty:
                self.queueNotEmpty.acquire()
                self.queueNotEmpty.wait()
                self.queueNotEmpty.release()
            except Exception:
                # Must continue the event loop even if handler failed
                girderformindlogger.logger.exception(
                    'In handler for event "%s":' % eventName
                )

        girderformindlogger.logprint.info(
            "Stopped asynchronous event manager thread."
        )

    def trigger(self, eventName=None, info=None, callback=None):
        """
        Adds a new event on the queue to trigger asynchronously.

        :param eventName: The event name to pass to the girderformindlogger.events.trigger
        :param info: The info object to pass to girderformindlogger.events.trigger
        :param callback: Optional callable to be called upon completion of
            all bound event handlers. It takes one argument, which is the
            event object itself.
        """
        self.queueNotEmpty.acquire()
        self.eventQueue.put((eventName, info, callback))
        self.queueNotEmpty.notify()
        self.queueNotEmpty.release()

    def stop(self):
        """
        Gracefully stops this thread. Will finish the currently processing
        event before stopping.
        """
        self.queueNotEmpty.acquire()
        self.terminate = True
        self.queueNotEmpty.notify()
        self.queueNotEmpty.release()

    def __del__(self):
        # Make sure we stop this thread if it's getting GCed, i.e. daemon was reassigned
        self.stop()
        # We had been calling the super class's __del__, but it doesn't have
        # such a method, so doing so would raise an AttributeError.
        # super(AsyncEventsThread, self).__del__()


def bind(eventName, handlerName, handler):
    """
    Bind a listener (handler) to the event identified by eventName. It is
    convention that plugins will use their own name as the handlerName, so that
    the trigger() caller can see which plugin(s) responded to the event.

    :param eventName: The name that identifies the event.
    :type eventName: str
    :param handlerName: The name that identifies the handler calling bind().
    :type handlerName: str
    :param handler: The function that will be called when the event is fired.
                    It must accept a single argument, which is the Event that
                    was created by trigger(). This function should not return
                    a value; any data that it needs to pass back to the
                    triggerer should be passed via the addResponse() method of
                    the Event.
    :type handler: function
    """
    if eventName in _deprecated:
        girderformindlogger.logger.warning(
            'event "%s" is deprecated; %s'
            % (eventName, _deprecated[eventName])
        )

    if eventName not in _mapping:
        _mapping[eventName] = OrderedDict()

    if handlerName in _mapping[eventName]:
        girderformindlogger.logger.warning(
            "Event binding already exists: %s -> %s" % (eventName, handlerName)
        )
    else:
        _mapping[eventName][handlerName] = handler


def unbind(eventName, handlerName):
    """
    Removes the binding between the event and the given listener.

    :param eventName: The name that identifies the event.
    :type eventName: str
    :param handlerName: The name that identifies the handler calling bind().
    :type handlerName: str
    """
    _mapping.get(eventName, {}).pop(handlerName, None)


def unbindAll():
    """
    Clears the entire event map. All bound listeners will be unbound.

     .. warning:: This will also disable internal event listeners, which are
       necessary for normal Girder functionality. This function should generally
       never be called outside of testing.
    """
    _mapping.clear()


@contextlib.contextmanager
def bound(eventName, handlerName, handler):
    """
    A context manager to temporarily bind an event handler within its scope.

    Parameters are the same as those to :py:func:`girderformindlogger.events.bind`.
    """
    bind(eventName, handlerName, handler)
    try:
        yield
    finally:
        unbind(eventName, handlerName)


def trigger(eventName, info=None, pre=None, asynchronous=False, daemon=False):
    """
    Fire an event with the given name. All listeners bound on that name will be
    called until they are exhausted or one of the handlers calls the
    stopPropagation() method on the event.

    :param eventName: The name that identifies the event.
    :type eventName: str
    :param info: The info argument to pass to the handler function. The type of
        this argument is opaque, and can be anything.
    :param pre: A function that will be executed prior to the handler being
        executed. It will receive a dict with a "handler" key, (the function),
        "info" key (the info arg to this function), and "eventName" and
        "handlerName" values.
    :type pre: function or None
    :param asynchronous: Whether this event is executing on the background thread
        (True) or on the request thread (False).
    :type asynchronous: bool
    :param daemon: Whether this was triggered via ``girderformindlogger.events.daemon``.
    :type daemon: bool
    """
    e = Event(eventName, info, asynchronous=asynchronous)
    for name, handler in six.viewitems(_mapping.get(eventName, {})):
        if daemon and not asynchronous:
            girderformindlogger.logprint.warning(
                'WARNING: Handler "%s" for event "%s" was triggered on the daemon, but is '
                "actually running synchronously." % (name, eventName)
            )
        e.currentHandlerName = name
        if pre is not None:
            pre(
                info=info,
                handler=handler,
                eventName=eventName,
                handlerName=name,
            )
        handler(e)

        if e.propagate is False:
            break

    return e


_deprecated = {}
_mapping = {}
daemon = ForegroundEventsDaemon()


def setupDaemon():
    global daemon
    if config.getConfig()["server"].get("disable_event_daemon", False):
        daemon = ForegroundEventsDaemon()
    else:
        daemon = AsyncEventsThread()
