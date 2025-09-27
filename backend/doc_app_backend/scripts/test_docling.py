#!/usr/bin/env python3
"""
Test script for Docling integration
"""
import asyncio
from pathlib import Path
import sys
import os

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from doc_app_backend.document_service import document_processing_service
from doc_app_backend.anthropic_service import anthropic_files_service


async def test_docling_conversion():
    """Test converting the PDF document to markdown using Docling"""

    # Path to the test PDF - corrected path
    pdf_path = Path(__file__).parent.parent.parent / "data" / "Bewerbungsbedingungen.pdf"

    if not pdf_path.exists():
        print(f"PDF file not found at: {pdf_path}")
        return

    print(f"Testing Docling conversion with: {pdf_path.name}")
    print("-" * 50)

    # Test questions about the document
    test_questions = [
        "What is this document about?",
        "What are the main requirements mentioned?",
        "Are there any specific deadlines or dates mentioned?"
    ]

    try:
        # Process the document
        result = await document_processing_service.process_document(
            file_path=pdf_path,
            questions=test_questions
        )

        # Display results
        print("✅ Document processing completed!")
        print(f"Markdown length: {result.get('markdown_length', 0)} characters")

        if result.get('markdown_content'):
            print("\n📄 Markdown Preview (first 500 chars):")
            print("-" * 50)
            print(result['markdown_content'][:500] + "..." if len(result['markdown_content']) > 500 else result['markdown_content'])

        if result.get('answers'):
            print("\n❓ Question Answers:")
            print("-" * 50)
            answers_data = result['answers']
            if 'answers' in answers_data:
                for answer in answers_data['answers']:
                    print(f"Q: {answer.get('question', 'N/A')}")
                    print(f"A: {answer.get('answer', 'N/A')}")
                    print(f"Confidence: {answer.get('confidence', 'N/A')}")
                    print("-" * 30)
            else:
                print(f"Error in answers: {answers_data.get('error', 'Unknown error')}")

        if result.get('error'):
            print(f"❌ Error: {result['error']}")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_markdown_only():
    """Test just the markdown conversion without questions"""

    pdf_path = Path(__file__).parent.parent.parent / "data" / "Bewerbungsbedingungen.pdf"

    if not pdf_path.exists():
        print(f"PDF file not found at: {pdf_path}")
        return

    print(f"\nTesting markdown-only conversion with: {pdf_path.name}")
    print("-" * 50)

    try:
        # Read file content
        with open(pdf_path, 'rb') as f:
            file_content = f.read()

        # Convert to markdown
        markdown_content = await document_processing_service.convert_to_markdown(
            file_content=file_content,
            filename=pdf_path.name
        )

        if markdown_content:
            print("✅ Markdown conversion successful!")
            print(f"Length: {len(markdown_content)} characters")
            print(f"First 300 chars:\n{markdown_content[:300]}...")
        else:
            print("❌ Markdown conversion returned None")

    except Exception as e:
        print(f"❌ Markdown conversion failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 Testing Docling Integration")
    print("=" * 50)

    # Check if Anthropic API is configured
    if anthropic_files_service.is_enabled():
        print("✅ Anthropic API is configured - testing full workflow")
        asyncio.run(test_docling_conversion())
    else:
        print("⚠️  Anthropic API not configured - testing markdown conversion only")
        asyncio.run(test_markdown_only())

    print("\n🏁 Test completed!")