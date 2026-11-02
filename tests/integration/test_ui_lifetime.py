import gc
from threading import get_ident

from raceframe.ui.lifetime import ensure_gui_collection
from raceframe.ui.workers import TaskWorker


def test_background_allocations_are_collected_on_gui_thread(qtbot, qapp):
    manager = ensure_gui_collection()
    original_interval = manager.timer.interval()
    manager.timer.setInterval(10)
    gui_thread = get_ident()
    destroyed_on = []

    class Cycle:
        def __init__(self):
            self.reference = self

        def __del__(self):
            destroyed_on.append(get_ident())

    def allocate(progress, record, cancel):
        for _ in range(3000):
            Cycle()
        cancel.wait(0.05)

    worker = TaskWorker(allocate)
    try:
        assert not gc.isenabled()
        assert ensure_gui_collection() is manager
        with qtbot.waitSignal(worker.finished, timeout=5000):
            worker.start()
        worker.wait()
        manager.collect()
        assert len(destroyed_on) == 3000
        assert set(destroyed_on) == {gui_thread}
    finally:
        manager.timer.setInterval(original_interval)
        worker.wait()
        worker.deleteLater()
