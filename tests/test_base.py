from rating.base import Base

class Concrete(Base):
    def __init__(self, player=None, content=None):
        self.player = player
        self.content = content

    def get_url(self):
        return "http://example.com"

    def parse_content(self, content):
        return self.content

def test_run():
    obj = Concrete()
    obj.run()  # Should not raise any AttributeError
    obj = Concrete(content="Hello")
    obj.run()
