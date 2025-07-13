import time
print("Ak is here")
class ContinuousScript:
    def __init__(self):
        self.running = True
        self.input1 = ""
        self.input2 = ""
        self.input3 = ""

    def update_inputs(self, input1, input2, input3):
        self.input1 = input1
        self.input2 = input2
        self.input3 = input3

    def run(self):
        while self.running:
            if self.input1 and self.input2 and self.input3:
                print(f"Processing: {self.input1}, {self.input2}, {self.input3}")
            time.sleep(5)  # Simulate processing delay

    def stop(self):
        self.running = False

script_instance = ContinuousScript()
