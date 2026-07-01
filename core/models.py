class RawNote:
    """Represents a raw note"""
    def __init__(self, content, title=None, deadline=None, note_type="misc"):
        self.content = content
        self.title = title
        self.deadline = deadline
        self.note_type = note_type

class PrintJob:
    """Represents a formatted print job containing ESC/POS raw bytes."""
    def __init__(self, data):
        self.data = data
