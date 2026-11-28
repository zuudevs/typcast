"""The root document of the document IR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Sequence

from typcast.canonical import assert_encodable
from typcast.diagnostics import CODE_REQUIRED_FIELD, Diagnostic, raise_validation
from typcast.models.base import Block, require_instance, require_tuple
from typcast.models.metadata import Metadata
from typcast.models.module import Module
from typcast.models.page import Page
from typcast.version import SCHEMA_VERSION, check_schema_version

if TYPE_CHECKING:
    from typcast.validations.config import TypcastConfig

__all__ = ["Document"]


@dataclass(frozen=True)
class Document:
    """The immutable root of a Typcast document."""

    metadata: Metadata
    page: Page
    contents: Sequence[Block]
    modules: Sequence[Module] = ()
    schema_version: str = SCHEMA_VERSION

    type: ClassVar[str] = "document"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadata",
            require_instance(self.metadata, Metadata, "/metadata"),
        )
        object.__setattr__(self, "page", require_instance(self.page, Page, "/page"))
        object.__setattr__(
            self,
            "contents",
            require_tuple(self.contents, Block, "/contents", allow_empty=False),
        )
        object.__setattr__(
            self,
            "modules",
            require_tuple(self.modules, Module, "/modules"),
        )
        check_schema_version(self.schema_version)

    def to_dict(self) -> dict[str, Any]:
        """Returns the JSON value of the document."""
        value = {
            "schemaVersion": self.schema_version,
            "metadata": self.metadata.to_dict(),
            "page": self.page.to_dict(),
            "contents": [block.to_dict() for block in self.contents],
            "modules": [module.to_dict() for module in self.modules],
        }
        # The canonical text of the document is UTF-8, so a document that
        # holds a character that UTF-8 cannot encode has no JSON value.
        assert_encodable(value, "")
        return value

    def to_json(self) -> str:
        """Returns the canonical JSON text of the document."""
        from typcast.serialization import document_to_json

        return document_to_json(self)

    def validate(self, config: "TypcastConfig | None" = None) -> tuple[Diagnostic, ...]:
        """Returns the diagnostics of the semantic rules of the document.

        The method reports every problem it finds and raises no error for a
        semantic problem, so that a caller can show all of them at once. An
        invalid configuration raises a configuration error.
        """
        from typcast.validations.engine import validate_document

        return validate_document(self, config)

    def validate_schema(self) -> tuple[Diagnostic, ...]:
        """Returns the diagnostics of the JSON Schema contract of the document.

        The method checks the JSON value of the document against the schema
        contract that the SDK carries. It reports every rule that the value
        breaks and raises no error, so that a caller can show all of the
        problems at once. The check is a layer of its own: the semantic rules
        of the document stay in `validate`.
        """
        from typcast.schema import validate_schema

        return validate_schema(self.to_dict())

    @classmethod
    def from_dict(cls, value: Any) -> "Document":
        """Builds a document from a JSON value."""
        from typcast.serialization import document_from_dict

        return document_from_dict(value)

    @classmethod
    def from_json(cls, source: str) -> "Document":
        """Builds a document from JSON text."""
        from typcast.serialization import document_from_json

        return document_from_json(source)
