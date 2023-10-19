class Controller:
    def __init__(self, page):
        self.page = page
        self.setup_controls()
        self.setup_events()

    def setup_controls(self):
        """Method for setting up controls"""

        raise NotImplementedError

    def setup_events(self):
        """Method for setting up events"""

        raise NotImplementedError
