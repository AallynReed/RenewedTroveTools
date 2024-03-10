import asyncio
import concurrent.futures
import sys
import threading
import time
import traceback


class StackMonitor(threading.Thread):
    def __init__(self, loop, block_threshold=1, check_freq=2):
        super().__init__(
            name=f"{type(self).__name__}-{threading._counter()}", daemon=True
        )

        self.loop = loop
        self._do_run = threading.Event()
        self._do_run.set()

        self.block_threshold = block_threshold
        self.check_frequency = check_freq

        self.last_stack = None
        self.still_blocked = False
        self._last_frame = None

    @staticmethod
    async def dummy_coro():
        return True

    def test_loop_availability(self):
        t0 = time.perf_counter()
        fut = asyncio.run_coroutine_threadsafe(self.dummy_coro(), self.loop)
        t1 = time.perf_counter()

        try:
            fut.result(self.block_threshold)
            t2 = time.perf_counter()
        except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
            t2 = time.perf_counter()

            frame = sys._current_frames()[self.loop._thread_id]
            stack = traceback.format_stack(frame)

            if (
                stack == self.last_stack
                and frame is self._last_frame
                and frame.f_lasti == self._last_frame.f_lasti
            ):

                self.still_blocked = True
                print("Still blocked...")
                return
            else:
                self.still_blocked = False

            print(f"Future took longer than {self.block_threshold}s to return")
            print("".join(stack))

            self.last_stack = stack
            self._last_frame = frame

        else:
            if self.still_blocked:
                print("No longer blocked")
                self.still_blocked = False

            self.last_stack = None
            return t2 - t1

    def run(self):
        while self._do_run.is_set():
            if self.loop.is_running():
                self.test_loop_availability()
            time.sleep(self.check_frequency)

    def stop(self):
        self._do_run.clear()
