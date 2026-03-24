class TelemetryEntry:
    def __init__(self, identifier: str, message: str):
        self.identifier = identifier
        self.message = message

    def get_string(self):
        return f"[{self.identifier}] -> {self.message}"

    def print(self):
        print(self.get_string())


class Telemetry:
    def __init__(self, persistent_path='/telemetry/log.txt'):
        self.entries = []
        self.persistent_path = ""

    def add(self, entry: TelemetryEntry):
        self.entries.append(entry)

    def dump(self):
        with open(self.persistent_path, 'w') as file:
            file.write('\n'.join([k.get_string() for k in self.entries]))