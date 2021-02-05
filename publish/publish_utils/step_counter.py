class StepCounter:
    def __init__(self):
        self.step_counter = 0

    def next_step(self) -> int:
        self.step_counter += 1
        return self.step_counter
