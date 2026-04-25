"""
OCR System - Composition Root

Dependency injection configuration and service container.
Entry point for creating the application with all dependencies.
"""

from __future__ import annotations

from typing import Optional

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
from ocr_system.infrastructure.constants import (
    PATH_SELECTION_MEGAPIXEL_THRESHOLD,
    PATH_SELECTION_TEXT_DENSITY_THRESHOLD,
    PIXELS_PER_MEGAPIXEL,
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
        self._local_image_source: Optional[ImageSource] = None
        self._http_image_source: Optional[ImageSource] = None
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
        if source_type == "http":
            if self._http_image_source is None:
                self._http_image_source = HttpImageSource()
            return self._http_image_source
        if self._local_image_source is None:
            self._local_image_source = LocalFileImageSource(
                base_path=str(self.config.temp_directory)
            )
        return self._local_image_source

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
        megapixels = (width * height) / PIXELS_PER_MEGAPIXEL
        if megapixels < PATH_SELECTION_MEGAPIXEL_THRESHOLD or estimated_text_density > PATH_SELECTION_TEXT_DENSITY_THRESHOLD:
            return OCRPath.FAST
        return OCRPath.ACCURATE
