'use client';

import { useState, useEffect } from 'react';
import { getApiUrl } from '../../lib/env';
import styles from './documents.module.css';

interface Document {
  id: string;
  filename?: string | null;
  upload_date?: string | null;
  file_size?: number | null;
  // Backend actually returns these fields:
  size?: number | null;
  modified?: number | null;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null); // Clear previous errors
      const response = await fetch(getApiUrl('/documents'));

      if (response.ok) {
        const data = await response.json();

        // Handle null, undefined, or non-array responses
        if (data === null || data === undefined) {
          console.warn('API returned null/undefined data');
          setDocuments([]);
        } else if (Array.isArray(data)) {
          // Filter out any null/undefined items in the array
          const validDocuments = data.filter((doc: any) => doc !== null && doc !== undefined);
          setDocuments(validDocuments);
        } else if (typeof data === 'object' && data.documents && Array.isArray(data.documents)) {
          // Handle case where documents are nested in a wrapper object
          const validDocuments = data.documents
            .filter((doc: any) => doc !== null && doc !== undefined)
            .map((doc: any, index: number) => ({
              // Generate a unique ID since backend doesn't provide one
              id: doc.filename || `doc-${index}`,
              filename: doc.filename,
              // Map backend fields to frontend expectations
              file_size: doc.size,
              upload_date: doc.modified ? new Date(doc.modified * 1000).toISOString() : null,
              // Keep original fields as backup
              size: doc.size,
              modified: doc.modified
            }));
          setDocuments(validDocuments);
        } else {
          console.warn('API returned unexpected data format:', data);
          setDocuments([]);
        }
      } else {
        throw new Error(`Failed to fetch documents: ${response.status} ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to load documents. Please check your connection and try again.');
      setDocuments([]); // Ensure documents is always an empty array on error
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number | null | undefined) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Unknown date';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.warn('Invalid date format:', dateString);
      return 'Invalid date';
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <h1>Documents</h1>
        <div className={styles.loading}>Loading documents...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <h1>Documents</h1>
        <div className={styles.error}>
          {error}
          <button onClick={fetchDocuments} className={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Documents</h1>
        <button onClick={fetchDocuments} className={styles.refreshButton}>
          🔄 Refresh
        </button>
      </div>

      {documents.length === 0 ? (
        <div className={styles.empty}>
          <p>No documents uploaded yet.</p>
          <p>Go to the upload page to add your first document.</p>
        </div>
      ) : (
        <div className={styles.documentsGrid}>
          {documents.map((doc) => {
            // Ensure doc is not null and has required properties
            if (!doc || !doc.id) {
              console.warn('Invalid document found:', doc);
              return null;
            }

            return (
              <div key={doc.id} className={styles.documentCard}>
                <div className={styles.documentIcon}>📄</div>
                <div className={styles.documentInfo}>
                  <h3 className={styles.documentName}>
                    {doc.filename || 'Unnamed Document'}
                  </h3>
                  <p className={styles.documentMeta}>
                    Size: {formatFileSize(doc.file_size)}
                  </p>
                  <p className={styles.documentMeta}>
                    Uploaded: {formatDate(doc.upload_date)}
                  </p>
                </div>
              </div>
            );
          }).filter(Boolean)} {/* Remove any null items from rendering */}
        </div>
      )}
    </div>
  );
}