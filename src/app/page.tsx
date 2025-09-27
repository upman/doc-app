'use client';

import Image from "next/image";
import styles from "./page.module.css";
import { useState } from "react";
import { getApiUrl, env } from "../lib/env";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadStatus('idle');
      setUploadMessage('');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploadStatus('uploading');
    setUploadMessage('Uploading...');

    try {
      const formData = new FormData();
      formData.append('file', file);

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
        <Image
          className={styles.logo}
          src="/next.svg"
          alt="Next.js logo"
          width={180}
          height={38}
          priority
        />

        {/* File Upload Form */}
        <div style={{ margin: '2rem 0', padding: '1rem', border: '1px solid #ccc', borderRadius: '8px', background: '#f9f9f9' }}>
          <h2 style={{ marginBottom: '1rem', color: "black" }}>Upload Document: {env.LOCAL_ONLY}</h2>
          <div style={{ marginBottom: '1rem' }}>
            <input
              type="file"
              onChange={handleFileChange}
              style={{ marginBottom: '1rem', padding: '0.5rem' }}
            />
          </div>
          <button
            onClick={handleUpload}
            disabled={!file || uploadStatus === 'uploading'}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: file && uploadStatus !== 'uploading' ? '#0070f3' : '#ccc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: file && uploadStatus !== 'uploading' ? 'pointer' : 'not-allowed'
            }}
          >
            {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload File'}
          </button>

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

        <ol>
          <li>
            Get started by editing <code>src/app/page.tsx</code>.
          </li>
          <li>Save and see your changes instantly.</li>
        </ol>

        <div className={styles.ctas}>
          <a
            className={styles.primary}
            href="https://vercel.com/new?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Image
              className={styles.logo}
              src="/vercel.svg"
              alt="Vercel logomark"
              width={20}
              height={20}
            />
            Deploy now
          </a>
          <a
            href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.secondary}
          >
            Read our docs
          </a>
        </div>
      </main>
      <footer className={styles.footer}>
        <a
          href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/file.svg"
            alt="File icon"
            width={16}
            height={16}
          />
          Learn
        </a>
        <a
          href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/window.svg"
            alt="Window icon"
            width={16}
            height={16}
          />
          Examples
        </a>
        <a
          href="https://nextjs.org?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/globe.svg"
            alt="Globe icon"
            width={16}
            height={16}
          />
          Go to nextjs.org →
        </a>
      </footer>
    </div>
  );
}
