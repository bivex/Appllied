"""
OCR System - Composition Root

Dependency injection configuration and service container.
Entry point for creating the application with all dependencies.
"""

from __future__ import annotations

import asyncio
from typing import Optional
from pathlib import Path

from ocr_system.domain import DocumentType, Language, OCRPath
from ocr_system.application import (
    ProcessDocumentUseCase,
    GetDocumentUseCase,
    SearchDocumentsUseCase,
    OCREngine,
    DocumentRepository,
    ImageSource,
    PathSelectionStrategy,
    ExtractStructureUseCase,
)
from ocr_system.infrastructure import (
    VisionOCRAdapter,
    CustomModelOCRAdapter,
    LocalFileImageSource,
    HttpImageSource,
    InMemoryDocumentRepository,
    OCRConfig,
)


class OCRContainer:
    """Simple dependency injection container."""

    def __init__(
        self,
        config: Optional[OCRConfig] = None,
        use_vision: bool = True,
        use_custom_model: bool = False,
        model_path: Optional[str] = None,
    ):
        self.config = config or OCRConfig.from_env()
        self.use_vision = use_vision
        self.use_custom_model = use_custom_model
        self.model_path = model_path

        self._ocr_engine: Optional[OCREngine] = None
        self._image_source: Optional[ImageSource] = None
        self._document_repository: Optional[DocumentRepository] = None
        self._path_selector: Optional[PathSelectionStrategy] = None

    def get_ocr_engine(self) -> OCREngine:
        if self._ocr_engine is None:
            if self.use_custom_model and self.model_path:
                self._ocr_engine = CustomModelOCRAdapter(
                    model_path=self.model_path, use_ane=True
                )
            else:
                self._ocr_engine = VisionOCRAdapter(
                    use_accurate=True,
                    use_language_correction=self.config.use_language_correction,
                    recognition_level="accurate",
                )
        return self._ocr_engine

    def get_image_source(self, source_type: str = "local") -> ImageSource:
        if self._image_source is None:
            if source_type == "http":
                self._image_source = HttpImageSource()
            else:
                self._image_source = LocalFileImageSource(
                    base_path=str(self.config.temp_directory)
                )
        return self._image_source

    def get_document_repository(self) -> DocumentRepository:
        if self._document_repository is None:
            self._document_repository = InMemoryDocumentRepository()
        return self._document_repository

    def get_path_selector(self) -> PathSelectionStrategy:
        if self._path_selector is None:
            self._path_selector = SimplePathSelector()
        return self._path_selector

    def create_process_document_use_case(self) -> ProcessDocumentUseCase:
        return ProcessDocumentUseCase(
            image_source=self.get_image_source(),
            ocr_engine=self.get_ocr_engine(),
            document_repository=self.get_document_repository(),
            path_selector=self.get_path_selector(),
        )

    def create_get_document_use_case(self) -> GetDocumentUseCase:
        return GetDocumentUseCase(self.get_document_repository())

    def create_search_documents_use_case(self) -> SearchDocumentsUseCase:
        return SearchDocumentsUseCase(self.get_document_repository())

    def create_extract_structure_use_case(self) -> ExtractStructureUseCase:
        return ExtractStructureUseCase(self.get_ocr_engine())


class SimplePathSelector(PathSelectionStrategy):
    """Simple heuristic path selector."""

    def select_path(
        self,
        image_size: tuple[int, int],
        estimated_text_density: float,
        language_hint: Optional["Language"] = None,
    ) -> OCRPath:
        width, height = image_size
        megapixels = (width * height) / 1_000_000
        if megapixels < 2.0 or estimated_text_density > 0.3:
            return OCRPath.FAST
        return OCRPath.ACCURATE


# ===============================
# Entry point
# ===============================


async def main():
    """Example usage of the OCR system."""
    container = OCRContainer()
    process = container.create_process_document_use_case()

    try:
        document = await process.execute(
            image_url="sample.png", document_type=DocumentType.GENERIC
        )
        print(f"Processed document {document.id}")
        print(f"Full text:\n{document.get_full_text()}")
        print(f"Paragraphs: {len(document.paragraphs)}")
        print(f"Tables: {len(document.tables)}")
    except Exception as e:
        print(f"Error processing document: {e}")


if __name__ == "__main__":
    asyncio.run(main())
