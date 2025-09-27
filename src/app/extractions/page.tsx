'use client';

import { useState, useEffect } from 'react';
import { getApiUrl } from '../../lib/env';
import styles from './extractions.module.css';

interface QuestionResult {
  question: string;
  answer: string;
  confidence: string | number | null;  // Updated to handle both string and number
  created_at: string;
}

interface Extraction {
  id: number;
  filename: string;
  file_size: number;
  questions: string[];
  status: string;
  created_at: string;
  updated_at: string;
  results: QuestionResult[];
}

interface PaginationInfo {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

interface ExtractionsResponse {
  message: string;
  extractions: Extraction[];
  pagination: PaginationInfo;
}

export default function ExtractionsPage() {
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    fetchExtractions(currentPage, pageSize);
  }, [currentPage, pageSize]);

  const fetchExtractions = async (page: number, size: number) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(getApiUrl(`/extractions?page=${page}&page_size=${size}`));

      if (response.ok) {
        const data: ExtractionsResponse = await response.json();
        setExtractions(data.extractions || []);
        setPagination(data.pagination);
      } else {
        throw new Error(`Failed to fetch extractions: ${response.status} ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error fetching extractions:', err);
      setError('Failed to load extractions. Please check your connection and try again.');
      setExtractions([]);
      setPagination(null);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1); // Reset to first page when changing page size
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Invalid date';
    }
  };

  const formatConfidence = (confidence: string | number | null | undefined): string => {
    if (confidence === null || confidence === undefined) {
      return 'N/A';
    }

    // If confidence is a string (like "high", "medium", "low"), return it as-is with proper capitalization
    if (typeof confidence === 'string') {
      return confidence.charAt(0).toUpperCase() + confidence.slice(1).toLowerCase();
    }

    // Handle confidence as a decimal (0-1) or percentage (0-100) for numeric values
    if (typeof confidence === 'number' && !isNaN(confidence)) {
      let confidenceValue = confidence;
      if (confidence <= 1) {
        // Assume it's a decimal, convert to percentage
        confidenceValue = confidence * 100;
      }
      return `${confidenceValue.toFixed(1)}%`;
    }

    return 'N/A';
  };

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      pending: styles.statusPending,
      processing: styles.statusProcessing,
      completed: styles.statusCompleted,
      failed: styles.statusFailed
    };

    return (
      <span className={`${styles.statusBadge} ${statusClasses[status as keyof typeof statusClasses] || ''}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  const renderPagination = () => {
    if (!pagination) return null;

    const pages = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, pagination.page - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(pagination.total_pages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`${styles.pageButton} ${i === pagination.page ? styles.activePage : ''}`}
          disabled={loading}
        >
          {i}
        </button>
      );
    }

    return (
      <div className={styles.pagination}>
        <button
          onClick={() => handlePageChange(pagination.page - 1)}
          disabled={!pagination.has_prev || loading}
          className={styles.pageButton}
        >
          ← Previous
        </button>
        {pages}
        <button
          onClick={() => handlePageChange(pagination.page + 1)}
          disabled={!pagination.has_next || loading}
          className={styles.pageButton}
        >
          Next →
        </button>
      </div>
    );
  };

  if (loading && extractions.length === 0) {
    return (
      <div className={styles.container}>
        <h1>Document Extractions</h1>
        <div className={styles.loading}>Loading extractions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <h1>Document Extractions</h1>
        <div className={styles.error}>
          {error}
          <button onClick={() => fetchExtractions(currentPage, pageSize)} className={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Document Extractions</h1>
        <div className={styles.controls}>
          <label className={styles.pageSizeLabel}>
            Items per page:
            <select
              value={pageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              className={styles.pageSizeSelect}
              disabled={loading}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </label>
          <button onClick={() => fetchExtractions(currentPage, pageSize)} className={styles.refreshButton} disabled={loading}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {pagination && (
        <div className={styles.paginationInfo}>
          Showing {((pagination.page - 1) * pagination.page_size) + 1} to{' '}
          {Math.min(pagination.page * pagination.page_size, pagination.total_count)} of{' '}
          {pagination.total_count} extractions
        </div>
      )}

      {extractions.length === 0 ? (
        <div className={styles.empty}>
          <p>No extractions found.</p>
          <p>Upload a document with questions to see extractions here.</p>
        </div>
      ) : (
        <>
          <div className={styles.extractionsGrid}>
            {extractions.map((extraction) => (
              <div key={extraction.id} className={styles.extractionCard}>
                <div className={styles.extractionHeader}>
                  <div className={styles.extractionTitle}>
                    <h3>{extraction.filename}</h3>
                    {getStatusBadge(extraction.status)}
                  </div>
                  <div className={styles.extractionMeta}>
                    <span>Size: {formatFileSize(extraction.file_size)}</span>
                    <span>Created: {formatDate(extraction.created_at)}</span>
                    {extraction.updated_at !== extraction.created_at && (
                      <span>Updated: {formatDate(extraction.updated_at)}</span>
                    )}
                  </div>
                </div>

                {extraction.questions.length > 0 && (
                  <div className={styles.questionsSection}>
                    <h4>Questions Asked ({extraction.questions.length})</h4>
                    <ul className={styles.questionsList}>
                      {extraction.questions.map((question, index) => (
                        <li key={index} className={styles.questionItem}>
                          {question}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {extraction.results.length > 0 && (
                  <div className={styles.resultsSection}>
                    <h4>Results ({extraction.results.length})</h4>
                    <div className={styles.resultsList}>
                      {extraction.results.map((result, index) => (
                        <div key={index} className={styles.resultItem}>
                          <div className={styles.questionText}>
                            <strong>Q:</strong> {result.question}
                          </div>
                          <div className={styles.answerText}>
                            <strong>A:</strong> {result.answer}
                          </div>
                          {result.confidence !== null && (
                            <div className={styles.confidenceScore}>
                              <strong>Confidence:</strong> {formatConfidence(result.confidence)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {extraction.status === 'completed' && extraction.results.length === 0 && (
                  <div className={styles.noResults}>
                    <p>Processing completed but no question results available.</p>
                  </div>
                )}

                {extraction.status === 'failed' && (
                  <div className={styles.failedStatus}>
                    <p>Processing failed. Please try uploading the document again.</p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {renderPagination()}
        </>
      )}
    </div>
  );
}