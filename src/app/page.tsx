'use client';

import Image from "next/image";
import styles from "./page.module.css";
import { useState } from "react";
import { getApiUrl, env } from "../lib/env";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState<string>('');
  const [questions, setQuestions] = useState<string[]>(['']);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadStatus('idle');
      setUploadMessage('');
    }
  };

  const handleQuestionChange = (index: number, value: string) => {
    const updatedQuestions = [...questions];
    updatedQuestions[index] = value;
    setQuestions(updatedQuestions);
  };

  const addQuestion = () => {
    setQuestions([...questions, '']);
  };

  const removeQuestion = (index: number) => {
    if (questions.length > 1) {
      const updatedQuestions = questions.filter((_, i) => i !== index);
      setQuestions(updatedQuestions);
    }
  };

  const hasValidQuestions = () => {
    return questions.some(question => question.trim() !== '');
  };

  const handleUpload = async () => {
    if (!file || !hasValidQuestions()) return;

    setUploadStatus('uploading');
    setUploadMessage('Uploading...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Add questions to the form data
      const validQuestions = questions.filter(q => q.trim() !== '');
      formData.append('questions', JSON.stringify(validQuestions));

      const response = await fetch(getApiUrl('/documents/upload'), {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setUploadStatus('success');
        setUploadMessage('Upload succeeded!');
        console.log('Upload successful:', result);
      } else {
        throw new Error(`Upload failed with status: ${response.status}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      setUploadMessage('Upload failed!');
    }
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>

        {/* File Upload Form */}
        <div style={{ margin: '2rem 0', padding: '1rem', border: '1px solid #ccc', borderRadius: '8px', background: '#f9f9f9' }}>
          <h2 style={{ marginBottom: '1rem', color: "black" }}>Upload Document</h2>

          <div style={{ marginBottom: '1rem' }}>
            <input
              type="file"
              onChange={handleFileChange}
              style={{ marginBottom: '1rem', padding: '0.5rem' }}
            />
          </div>

          {/* Questions Section */}
          <div style={{ marginBottom: '1rem' }}>
            <h3 style={{ marginBottom: '0.5rem', color: "black" }}>Questions (at least 1 required)</h3>
            {questions.map((question, index) => (
              <div key={index} style={{ display: 'flex', marginBottom: '0.5rem', alignItems: 'center' }}>
                <input
                  type="text"
                  value={question}
                  onChange={(e) => handleQuestionChange(index, e.target.value)}
                  placeholder={`Question ${index + 1}`}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #ccc',
                    marginRight: '0.5rem'
                  }}
                />
                {questions.length > 1 && (
                  <button
                    onClick={() => removeQuestion(index)}
                    style={{
                      padding: '0.5rem',
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={addQuestion}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                marginTop: '0.5rem'
              }}
            >
              Add Question
            </button>
          </div>

          <button
            onClick={handleUpload}
            disabled={!file || uploadStatus === 'uploading' || !hasValidQuestions()}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: file && uploadStatus !== 'uploading' && hasValidQuestions() ? '#0070f3' : '#ccc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: file && uploadStatus !== 'uploading' && hasValidQuestions() ? 'pointer' : 'not-allowed'
            }}
          >
            {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload File'}
          </button>

          {!hasValidQuestions() && (
            <div style={{
              marginTop: '0.5rem',
              color: '#dc3545',
              fontSize: '0.9rem'
            }}>
              Please add at least one question before uploading.
            </div>
          )}

          {uploadMessage && (
            <div style={{
              marginTop: '1rem',
              padding: '0.5rem',
              borderRadius: '4px',
              backgroundColor: uploadStatus === 'success' ? '#d4edda' : uploadStatus === 'error' ? '#f8d7da' : '#fff3cd',
              color: uploadStatus === 'success' ? '#155724' : uploadStatus === 'error' ? '#721c24' : '#856404',
              border: `1px solid ${uploadStatus === 'success' ? '#c3e6cb' : uploadStatus === 'error' ? '#f5c6cb' : '#ffeaa7'}`
            }}>
              {uploadMessage}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
