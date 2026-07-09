"""Pure-Python signal/slot system — replaces PySide6.QtCore.Signal.
Used by all CustomTkinter widgets to avoid PySide6/Tkinter conflicts.
"""


class Signal:
    """A simple signal that emits values to connected slots."""

    def __init__(self, *types):
        self._types = types
        self._slots = []

    def connect(self, slot):
        """Connect a slot function."""
        self._slots.append(slot)

    def emit(self, *args):
        """Emit signal to all connected slots."""
        for slot in self._slots:
            try:
                slot(*args)
            except Exception:
                pass

    def disconnect_all(self):
        """Disconnect all slots."""
        self._slots.clear()
