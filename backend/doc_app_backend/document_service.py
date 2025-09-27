"""
Service module for document processing using Docling
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import tempfile
import os

from docling.document_converter import DocumentConverter

from .settings import settings

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Service for processing documents using Docling"""

    def __init__(self):
        self._converter: Optional[DocumentConverter] = None

    @property
    def converter(self) -> DocumentConverter:
        """Get or create Docling DocumentConverter"""
        if self._converter is None:
            self._converter = DocumentConverter()
        return self._converter

    async def convert_to_markdown(self, file_content: bytes, filename: str) -> Optional[str]:
        """
        Convert a document to markdown using Docling

        Args:
            file_content: The file content as bytes
            filename: Name of the file (used for determining file type)

        Returns:
            Markdown content as string if successful, None if conversion fails
        """
        try:
            logger.info(f"Converting document '{filename}' to markdown using Docling")

            # Create a temporary file to work with Docling
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            try:
                # Convert using Docling
                result = self.converter.convert(temp_file_path)
                markdown_content = result.document.export_to_markdown()

                logger.info(f"Successfully converted '{filename}' to markdown ({len(markdown_content)} characters)")
                return markdown_content

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Failed to convert document '{filename}' to markdown: {str(e)}")
            raise

    async def process_document(self, file_path: Path, questions: list[str]) -> Dict[str, Any]:
        """
        Process a document by converting it to markdown and answering questions

        Args:
            file_path: Path to the document file
            questions: List of questions to answer about the document

        Returns:
            Dictionary containing markdown content and answers
        """
        try:
            # Read the file content
            with open(file_path, 'rb') as f:
                file_content = f.read()

            filename = file_path.name

            # Check if the format is supported
            if not self.is_supported_format(filename):
                logger.warning(f"File format not supported by Docling: {filename}")
                return {
                    "markdown_content": None,
                    "answers": None,
                    "error": f"File format not supported: {Path(filename).suffix}"
                }

            # Convert to markdown
            markdown_content = await self.convert_to_markdown(file_content, filename)

            result = {
                "markdown_content": markdown_content,
                "markdown_length": len(markdown_content) if markdown_content else 0,
                "answers": None
            }

            # If questions are provided and we have markdown content, get answers
            if questions and markdown_content:
                from .anthropic_service import anthropic_files_service

                try:
                    answers = await anthropic_files_service.answer_questions(
                        markdown_content=markdown_content,
                        questions=questions
                    )
                    result["answers"] = answers
                    logger.info(f"Successfully answered {len(questions)} questions about '{filename}'")
                except Exception as e:
                    logger.error(f"Failed to get answers for '{filename}': {str(e)}")
                    result["answers"] = {
                        "error": str(e),
                        "questions": questions
                    }
            elif questions and not markdown_content:
                result["answers"] = {
                    "error": "Cannot answer questions without markdown content",
                    "questions": questions
                }

            return result

        except Exception as e:
            logger.error(f"Failed to process document '{file_path}': {str(e)}")
            return {
                "markdown_content": None,
                "answers": None,
                "error": str(e)
            }

    def is_supported_format(self, filename: str) -> bool:
        """
        Check if the file format is supported by Docling

        Args:
            filename: Name of the file

        Returns:
            True if the format is supported, False otherwise
        """
        file_extension = Path(filename).suffix.lower()
        # Docling typically supports PDF, Word, PowerPoint, and other common document formats
        supported_extensions = {'.pdf', '.docx', '.doc', '.pptx', '.ppt', '.txt', '.md', '.html'}
        return file_extension in supported_extensions


# Global service instance
document_processing_service = DocumentProcessingService()