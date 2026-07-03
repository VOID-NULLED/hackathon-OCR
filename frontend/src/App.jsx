import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = '/api'

function App() {
  const [health, setHealth] = useState(null)
  const [status, setStatus] = useState(null)
  const [documents, setDocuments] = useState([])
  const [selectedDocument, setSelectedDocument] = useState(null)
  const [results, setResults] = useState([])
  const [codeBlocks, setCodeBlocks] = useState([])
  const [uploadError, setUploadError] = useState(null)
  const [uploadSuccess, setUploadSuccess] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [file, setFile] = useState(null)
  const [language, setLanguage] = useState('eng')

  useEffect(() => {
    fetchStatus()
    fetchHealth()
    fetchDocuments()
  }, [])

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/status/`)
      const data = await response.json()
      setStatus(data)
    } catch (error) {
      setStatus({ error: 'Unable to connect to backend' })
    }
  }

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health/`)
      const data = await response.json()
      setHealth(data)
    } catch (error) {
      setHealth({ error: 'Unable to connect to backend' })
    }
  }

  const fetchDocuments = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/documents/?order_by=-uploaded_at`)
      const data = await response.json()
      setDocuments(data.results || data)
    } catch (error) {
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchDocumentDetails = async (document) => {
    setSelectedDocument(document)
    setResults([])
    setCodeBlocks([])

    try {
      const [resultsResponse, codeResponse] = await Promise.all([
        fetch(`${API_BASE}/documents/${document.id}/results/`),
        fetch(`${API_BASE}/documents/${document.id}/code_blocks/`),
      ])

      const resultsData = await resultsResponse.json()
      const codeData = await codeResponse.json()

      setResults(resultsData)
      setCodeBlocks(codeData)
    } catch (error) {
      console.error(error)
    }
  }

  const handleUpload = async (event) => {
    event.preventDefault()
    setUploadError(null)
    setUploadSuccess(null)

    if (!file) {
      setUploadError('Select a file to upload.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)
    formData.append('language', language)

    try {
      const response = await fetch(`${API_BASE}/documents/upload/`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        setUploadError(data.error || 'Upload failed')
        return
      }

      setUploadSuccess('Upload started successfully. Refreshing document list...')
      setFile(null)
      fetchDocuments()
    } catch (error) {
      setUploadError('Upload failed. Check backend connection.')
    }
  }

  const refreshSelectedDocument = () => {
    if (selectedDocument) fetchDocumentDetails(selectedDocument)
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>OCR Dashboard</h1>
        <p>Upload documents, monitor OCR status, and review extracted text.</p>
      </header>

      <section className="status-panel">
        <div className="status-card">
          <h2>Backend Status</h2>
          <pre>{status ? JSON.stringify(status, null, 2) : 'Loading...'}</pre>
        </div>
        <div className="status-card">
          <h2>Health Check</h2>
          <pre>{health ? JSON.stringify(health, null, 2) : 'Loading...'}</pre>
        </div>
      </section>

      <section className="upload-panel">
        <div>
          <h2>Upload Document</h2>
          <form onSubmit={handleUpload} className="upload-form">
            <label>
              File
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.gif,.bmp,.tiff,.pdf"
                onChange={(event) => setFile(event.target.files[0] || null)}
              />
            </label>
            <label>
              Language
              <input
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
                placeholder="eng"
              />
            </label>
            <button type="submit" className="button">
              Start OCR
            </button>
          </form>
          {uploadError && <div className="message error">{uploadError}</div>}
          {uploadSuccess && <div className="message success">{uploadSuccess}</div>}
        </div>
      </section>

      <section className="documents-panel">
        <div className="documents-list">
          <div className="section-header">
            <h2>Documents</h2>
            <button className="small-button" onClick={fetchDocuments}>
              Refresh
            </button>
          </div>
          {isLoading ? (
            <p>Loading documents…</p>
          ) : documents.length === 0 ? (
            <p>No documents found.</p>
          ) : (
            <div className="document-items">
              {documents.map((doc) => (
                <button
                  key={doc.id}
                  onClick={() => fetchDocumentDetails(doc)}
                  className={`document-item ${selectedDocument?.id === doc.id ? 'active' : ''}`}
                >
                  <strong>{doc.filename}</strong>
                  <span>{doc.status}</span>
                  <small>{new Date(doc.uploaded_at).toLocaleString()}</small>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="document-details">
          {selectedDocument ? (
            <>
              <div className="section-header">
                <div>
                  <h2>Document Details</h2>
                  <p>{selectedDocument.filename}</p>
                </div>
                <button className="small-button" onClick={refreshSelectedDocument}>
                  Refresh
                </button>
              </div>

              <div className="details-grid">
                <div>
                  <strong>Status</strong>
                  <p>{selectedDocument.status}</p>
                </div>
                <div>
                  <strong>Size</strong>
                  <p>{selectedDocument.file_size} bytes</p>
                </div>
                <div>
                  <strong>Processed</strong>
                  <p>{selectedDocument.processed_at || 'Pending'}</p>
                </div>
              </div>

              <div className="result-section">
                <h3>OCR Results</h3>
                {results.length === 0 ? (
                  <p>No results available yet.</p>
                ) : (
                  results.map((result) => (
                    <div key={result.id} className="result-card">
                      <div className="result-meta">
                        <span>{result.content_type}</span>
                        <span>Lang: {result.language}</span>
                        <span>Confidence: {result.confidence}</span>
                        <span>Page: {result.page_number}</span>
                      </div>
                      <pre>{result.extracted_text || 'No extracted text.'}</pre>
                    </div>
                  ))
                )}
              </div>

              <div className="result-section">
                <h3>Code Blocks</h3>
                {codeBlocks.length === 0 ? (
                  <p>No code blocks detected.</p>
                ) : (
                  codeBlocks.map((block) => (
                    <div key={block.id} className="result-card">
                      <div className="result-meta">
                        <span>{block.detected_language}</span>
                        <span>Lines {block.line_start}-{block.line_end}</span>
                      </div>
                      <pre>{block.code_content}</pre>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>Select a document to see OCR results and code blocks.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

export default App
