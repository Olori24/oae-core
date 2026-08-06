class EngineeringStateManager:
    """
    Central state registry for the engineering organization.
    """

    def __init__(self):
        self._state = {
            "active_missions": 0,
            "completed_missions": 0,
            "registered_engineers": 0,
            "busy_engineers": 0,
            "idle_engineers": 0,
        }

    def set(self, key, value):
        self._state[key] = value

    def get(self, key):
        return self._state.get(key)

    def increment(self, key, amount=1):
        self._state[key] = self._state.get(key, 0) + amount

    def snapshot(self):
        return dict(self._state)