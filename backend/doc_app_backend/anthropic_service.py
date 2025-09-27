"""
Service module for integrating with Anthropic Files API
"""
import logging
from typing import Optional, BinaryIO, Dict, Any
import anthropic

from .settings import settings

logger = logging.getLogger(__name__)


class AnthropicFilesService:
    """Service for managing files through Anthropic Files API"""

    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        """Get or create Anthropic client"""
        if self._client is None:
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY must be set to use Files API")
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def is_enabled(self) -> bool:
        """Check if Anthropic Files API is enabled"""
        return settings.anthropic_api_key is not None

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a file to Anthropic Files API

        Args:
            file_content: The file content as bytes
            filename: Name of the file
            content_type: MIME type of the file

        Returns:
            Dictionary with file information if successful, None if API not enabled

        Raises:
            Exception: If upload fails
        """
        if not self.is_enabled():
            logger.info("Anthropic API not configured, skipping file upload")
            return None

        try:
            logger.info(f"Uploading file '{filename}' to Anthropic Files API")

            # Create a file-like object from bytes
            from io import BytesIO
            file_obj = BytesIO(file_content)

            # Upload to Anthropic Files API
            uploaded_file = self.client.beta.files.upload(
                file=(filename, file_obj, content_type)
            )

            logger.info(f"Successfully uploaded file '{filename}' with ID: {uploaded_file.id}")

            return {
                "file_id": uploaded_file.id,
                "filename": uploaded_file.filename,
                "size": len(file_content),  # Use the original file content length
                "type": uploaded_file.type,
                "created_at": uploaded_file.created_at.isoformat() if uploaded_file.created_at else None
            }

        except Exception as e:
            logger.error(f"Failed to upload file '{filename}' to Anthropic API: {str(e)}")
            raise

    async def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a file from Anthropic Files API

        Args:
            file_id: The file ID from Anthropic

        Returns:
            Dictionary with file metadata if successful, None if API not enabled
        """
        if not self.is_enabled():
            logger.info("Anthropic API not configured, skipping file metadata retrieval")
            return None

        try:
            file_metadata = self.client.beta.files.retrieve_metadata(file_id)

            return {
                "file_id": file_metadata.id,
                "filename": file_metadata.filename,
                "type": file_metadata.type,
                "created_at": file_metadata.created_at.isoformat() if file_metadata.created_at else None
            }

        except Exception as e:
            logger.error(f"Failed to get file metadata for ID '{file_id}': {str(e)}")
            raise

    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Anthropic Files API

        Args:
            file_id: The file ID from Anthropic

        Returns:
            True if successful, False if API not enabled
        """
        if not self.is_enabled():
            logger.info("Anthropic API not configured, skipping file deletion")
            return False

        try:
            self.client.beta.files.delete(file_id)
            logger.info(f"Successfully deleted file with ID: {file_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file with ID '{file_id}': {str(e)}")
            raise

    async def list_files(self) -> Optional[list[Dict[str, Any]]]:
        """
        List all files from Anthropic Files API

        Returns:
            List of file dictionaries if successful, None if API not enabled
        """
        if not self.is_enabled():
            logger.info("Anthropic API not configured, skipping file listing")
            return None

        try:
            files = self.client.beta.files.list()

            return [
                {
                    "file_id": file.id,
                    "filename": file.filename,
                    "type": file.type,
                    "created_at": file.created_at.isoformat() if file.created_at else None
                }
                for file in files.data
            ]

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise

    async def answer_questions(
        self,
        markdown_content: str,
        questions: list[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Answer questions about a document using Anthropic's Claude

        Args:
            markdown_content: The document content in markdown format
            questions: List of questions to answer

        Returns:
            Dictionary with answers in JSON format if successful, None if API not enabled
        """
        if not self.is_enabled():
            logger.info("Anthropic API not configured, skipping question answering")
            return None

        try:
            logger.info(f"Sending {len(questions)} questions to Anthropic for answering")

            # Create the prompt with markdown content and questions
            prompt = f"""You are a helpful assistant that answers questions about documents.
I will provide you with a document in markdown format and a list of questions.

Please analyze the document and answer each question based on the content.
Your response must be in valid JSON format with the following structure:

{{
  "answers": [
    {{
      "question": "The original question text",
      "answer": "Your detailed answer based on the document content",
      "confidence": "high|medium|low",
      "source_section": "Brief description of where in the document the answer was found (optional)"
    }}
  ]
}}

Document content:
{markdown_content}

Questions to answer:
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(questions)])}

Please provide your response in the exact JSON format specified above. Make sure your response is valid JSON that can be parsed."""

            # Send to Claude
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_content = message.content[0].text
            logger.info("Received response from Anthropic")

            # Try to parse as JSON
            import json
            try:
                parsed_response = json.loads(response_content)
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Anthropic response as JSON: {e}")
                # Return a fallback structure
                return {
                    "answers": [
                        {
                            "question": q,
                            "answer": "Error: Could not parse response from AI service",
                            "confidence": "low",
                            "error": str(e)
                        }
                        for q in questions
                    ],
                    "raw_response": response_content
                }

        except Exception as e:
            logger.error(f"Failed to get answers from Anthropic: {str(e)}")
            raise


# Global service instance
anthropic_files_service = AnthropicFilesService()