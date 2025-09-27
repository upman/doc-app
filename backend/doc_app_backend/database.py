"""
Database models and connection handling for SQLite
"""
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json

from .settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and operations"""

    def __init__(self):
        self._db_path = self._get_db_path()

    def _get_db_path(self) -> Path:
        """Get the database file path from settings"""
        if settings.database_url:
            # Extract path from sqlite:///./path format
            if settings.database_url.startswith("sqlite:///"):
                db_path = settings.database_url[len("sqlite:///"):]
                if db_path.startswith("./"):
                    # Relative path - make it relative to backend directory
                    return Path(__file__).parent.parent / db_path[2:]
                else:
                    return Path(db_path)

        # Fallback to default path
        return Path(__file__).parent.parent / settings.database_name

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration"""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return conn

    def execute_migration(self, migration_sql: str) -> None:
        """Execute a migration SQL script"""
        with self.get_connection() as conn:
            conn.executescript(migration_sql)
            conn.commit()

    def create_extraction(self, file_path: str, filename: str, file_size: int, questions: List[str]) -> int:
        """Create a new extraction record and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO extractions (file_path, filename, file_size, questions, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """,
                (file_path, filename, file_size, json.dumps(questions), datetime.utcnow(), datetime.utcnow())
            )
            extraction_id = cursor.lastrowid
            if extraction_id is None:
                raise RuntimeError("Failed to create extraction: no ID returned")
            return extraction_id

    def update_extraction_status(self, extraction_id: int, status: str, markdown_content: Optional[str] = None) -> None:
        """Update extraction status and optionally markdown content"""
        with self.get_connection() as conn:
            if markdown_content:
                conn.execute(
                    """
                    UPDATE extractions
                    SET status = ?, markdown_content = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, markdown_content, datetime.utcnow(), extraction_id)
                )
            else:
                conn.execute(
                    """
                    UPDATE extractions
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, datetime.utcnow(), extraction_id)
                )
            conn.commit()

    def create_question_result(self, extraction_id: int, question: str, answer: str, confidence: Optional[float] = None) -> int:
        """Create a question result record and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO question_results (extraction_id, question, answer, confidence, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (extraction_id, question, answer, confidence, datetime.utcnow())
            )
            result_id = cursor.lastrowid
            if result_id is None:
                raise RuntimeError("Failed to create question result: no ID returned")
            return result_id

    def get_all_extractions(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get all extractions with their question results, with pagination"""
        with self.get_connection() as conn:
            # Calculate offset
            offset = (page - 1) * page_size

            # Get total count
            count_cursor = conn.execute("SELECT COUNT(*) as total FROM extractions")
            total_count = count_cursor.fetchone()["total"]

            # Get extractions with pagination
            extractions_cursor = conn.execute(
                """
                SELECT id, file_path, filename, file_size, questions, status, markdown_content, created_at, updated_at
                FROM extractions
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, offset)
            )
            extractions = []

            for row in extractions_cursor:
                # Extract just the filename from the path
                filename = Path(row["filename"]).name if row["filename"] else "Unknown"

                extraction = {
                    "id": row["id"],
                    "filename": filename,  # Show just the filename, not the full path
                    "file_size": row["file_size"],
                    "questions": json.loads(row["questions"]) if row["questions"] else [],
                    "status": row["status"],
                    "markdown_content": row["markdown_content"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "results": []
                }

                # Get question results for this extraction
                results_cursor = conn.execute(
                    """
                    SELECT question, answer, confidence, created_at
                    FROM question_results
                    WHERE extraction_id = ?
                    ORDER BY created_at ASC
                    """,
                    (row["id"],)
                )

                for result_row in results_cursor:
                    extraction["results"].append({
                        "question": result_row["question"],
                        "answer": result_row["answer"],
                        "confidence": result_row["confidence"],
                        "created_at": result_row["created_at"]
                    })

                extractions.append(extraction)

            # Calculate pagination info
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1

            return {
                "extractions": extractions,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }

    def get_extraction_by_id(self, extraction_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific extraction by ID"""
        with self.get_connection() as conn:
            # Get the specific extraction
            extraction_cursor = conn.execute(
                """
                SELECT id, file_path, filename, file_size, questions, status, markdown_content, created_at, updated_at
                FROM extractions
                WHERE id = ?
                """,
                (extraction_id,)
            )
            row = extraction_cursor.fetchone()

            if not row:
                return None

            # Extract just the filename from the path
            filename = Path(row["filename"]).name if row["filename"] else "Unknown"

            extraction = {
                "id": row["id"],
                "filename": filename,  # Show just the filename, not the full path
                "file_size": row["file_size"],
                "questions": json.loads(row["questions"]) if row["questions"] else [],
                "status": row["status"],
                "markdown_content": row["markdown_content"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "results": []
            }

            # Get question results for this extraction
            results_cursor = conn.execute(
                """
                SELECT question, answer, confidence, created_at
                FROM question_results
                WHERE extraction_id = ?
                ORDER BY created_at ASC
                """,
                (extraction_id,)
            )

            for result_row in results_cursor:
                extraction["results"].append({
                    "question": result_row["question"],
                    "answer": result_row["answer"],
                    "confidence": result_row["confidence"],
                    "created_at": result_row["created_at"]
                })

            return extraction


# Global database manager instance
db_manager = DatabaseManager()