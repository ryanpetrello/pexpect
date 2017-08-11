from cStringIO import StringIO
import time

from .exceptions import EOF, TIMEOUT


class Expecter(object):

    def __init__(self, spawn, patterns, searchwindowsize=-1):
        self.spawn = spawn
        self.patterns = patterns
        if searchwindowsize == -1:
            searchwindowsize = spawn.searchwindowsize
        self.searchwindowsize = searchwindowsize
        self.timeout_index = self.eof_index = -1
        for index, s in enumerate(self.patterns):
            if s == EOF:
                self.eof_index = index
            if s == TIMEOUT:
                self.timeout_index = index

    def new_data(self, data):
        spawn = self.spawn

        pos = spawn.buffer.tell()
        spawn.buffer.write(data)
        if self.searchwindowsize:
            spawn.buffer.seek(max(0, pos - self.searchwindowsize))
            window = spawn.buffer.read(self.searchwindowsize + len(data))
        else:
            window = spawn.buffer.getvalue()

        def search(searches, data):
            first_match = None
            for index, s in enumerate(searches):
                if s in (EOF, TIMEOUT):
                    continue
                match = s.search(data)
                if match is None:
                    continue
                n = match.start()
                if first_match is None or n < first_match:
                    best_index = index
                    first_match = n
            if first_match is None:
                return -1
            return best_index

        return search(self.patterns, window)

    def expect_loop(self, timeout=-1):
        """Blocking expect"""
        spawn = self.spawn
        spawn.match = None

        if timeout is not None:
            end_time = time.time() + timeout

        try:
            incoming = ''
            spawn.buffer = StringIO()
            while True:
                idx = self.new_data(incoming)
                # Keep reading until exception or return.
                if idx > -1:
                    spawn.match = idx
                    return idx
                # No match at this point
                if (timeout is not None) and (timeout < 0):
                    spawn.match = None
                    return self.timeout_index
                # Still have time left, so read more data
                incoming = spawn.read_nonblocking(spawn.maxread, timeout)
                if self.spawn.delayafterread is not None:
                    time.sleep(self.spawn.delayafterread)
                if timeout is not None:
                    timeout = end_time - time.time()
        except:
            return self.eof_index


class searcher_string(object):
    def __init__(self, strings):
        pass


class searcher_re(object):
    def __init__(self, patterns):
        pass
