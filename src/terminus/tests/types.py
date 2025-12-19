from dataclasses import dataclass

from terminus.types import ContentType


@dataclass(frozen=True)
class BodyDTO:
    content: bytes = b""
    content_type: ContentType = ContentType.TEXT_PLAIN
    
    @property
    def content_length(self):
        return len(self.content)