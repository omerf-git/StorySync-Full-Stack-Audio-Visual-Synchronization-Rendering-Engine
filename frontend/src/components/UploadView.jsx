import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, Loader2 } from 'lucide-react';

const UploadView = ({ onComplete, language = 'en' }) => {
  const [audioFile, setAudioFile] = useState(null);
  const [inputType, setInputType] = useState('text'); // text | file
  const [textContent, setTextContent] = useState('');
  const [textFile, setTextFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!audioFile) {
      setError(language === 'tr' ? 'Lütfen bir ses dosyası yükleyin.' : 'Please upload an audio file.');
      return;
    }

    let finalScript = '';
    if (inputType === 'text') {
      if (!textContent.trim()) {
        setError(language === 'tr' ? 'Lütfen metni girin.' : 'Please enter the text.');
        return;
      }
      finalScript = textContent;
    } else {
      if (!textFile) {
        setError(language === 'tr' ? 'Lütfen bir metin dosyası yükleyin.' : 'Please upload a text file.');
        return;
      }
      finalScript = await textFile.text();
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('audio', audioFile);
      formData.append('text', finalScript);

      const res = await axios.post('/api/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      onComplete(res.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || (language === 'tr' ? 'Analiz sırasında bir hata oluştu.' : 'An error occurred during analysis.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Upload size={24} /> {language === 'tr' ? 'Proje Başlat' : 'Start Project'}
      </h2>
      
      {error && <div style={{ color: 'var(--error-color)', marginBottom: '1rem' }}>{error}</div>}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>{language === 'tr' ? '1. Ses Dosyası (MP3/WAV)' : '1. Audio File (MP3/WAV)'}</label>
          <input 
            type="file" 
            accept="audio/*" 
            onChange={(e) => setAudioFile(e.target.files[0])} 
            disabled={loading}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>{language === 'tr' ? '2. Metin İçeriği' : '2. Text Content'}</label>
          
          <div className="tabs">
            <div className={`tab ${inputType === 'text' ? 'active' : ''}`} onClick={() => setInputType('text')}>
              {language === 'tr' ? 'Kopyala / Yapıştır' : 'Copy / Paste'}
            </div>
            <div className={`tab ${inputType === 'file' ? 'active' : ''}`} onClick={() => setInputType('file')}>
              {language === 'tr' ? '.txt Dosyası Yükle' : 'Upload .txt File'}
            </div>
          </div>

          {inputType === 'text' ? (
            <textarea 
              rows="6" 
              placeholder={language === 'tr' ? "Hikaye veya belgesel metninizi buraya yapıştırın..." : "Paste your story or documentary script here..."}
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              disabled={loading}
            />
          ) : (
            <input 
              type="file" 
              accept=".txt" 
              onChange={(e) => setTextFile(e.target.files[0])}
              disabled={loading}
            />
          )}
        </div>

        <button type="submit" disabled={loading} style={{ marginTop: '1rem', width: '100%' }}>
          {loading ? (
            <><Loader2 className="spinner" /> {language === 'tr' ? 'Analiz Ediliyor...' : 'Analyzing...'}</>
          ) : (
            language === 'tr' ? 'Analizi Başlat' : 'Start Analysis'
          )}
        </button>
      </form>
    </div>
  );
};

export default UploadView;
