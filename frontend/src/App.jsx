import React, { useState, useEffect } from 'react';
import UploadView from './components/UploadView';
import StudioView from './components/StudioView';
import { Film, Home } from 'lucide-react';

function App() {
  const [sessionData, setSessionData] = useState(null);
  const [view, setView] = useState('upload'); // upload | review | studio
  const [language, setLanguage] = useState(() => localStorage.getItem('language') || 'en'); // 'en' | 'tr'

  useEffect(() => {
    localStorage.setItem('language', language);
  }, [language]);

  useEffect(() => {
    const savedSessionId = localStorage.getItem('sessionId');
    if (savedSessionId) {
      fetch(`/api/session/${savedSessionId}`)
        .then(res => {
          if (!res.ok) throw new Error("Session not found");
          return res.json();
        })
        .then(data => {
          setSessionData(data);
          setView('studio');
        })
        .catch(err => {
          console.error("Failed to restore session:", err);
          localStorage.removeItem('sessionId');
        });
    }
  }, []);

  const handleAnalysisComplete = (data) => {
    localStorage.setItem('sessionId', data.session_id);
    setSessionData(data);
    setView('studio');
  };

  const goHome = async () => {
    const confirmMsg = language === 'tr' 
      ? "Ana sayfaya dönmek istediğinizden emin misiniz? Tüm ilerlemeleriniz tamamen silinecek!" 
      : "Are you sure you want to return to the homepage? All progress will be lost!";
      
    if (window.confirm(confirmMsg)) {
      const savedSessionId = localStorage.getItem('sessionId');
      if (savedSessionId) {
        try {
          await fetch(`/api/session/${savedSessionId}`, { method: 'DELETE' });
        } catch (e) {
          console.error("Failed to delete session on backend", e);
        }
      }
      localStorage.removeItem('sessionId');
      setSessionData(null);
      setView('upload');
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.5rem', margin: 0 }}>
          <Film color="var(--accent-color)" size={24} />
          <span>Google Images to Video</span>
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {sessionData && (
            <span style={{ color: 'var(--text-muted)' }}>{language === 'tr' ? 'Oturum' : 'Session'}: {sessionData.session_id.substring(0,8)}</span>
          )}
          <button 
            className="secondary" 
            onClick={() => setLanguage(language === 'en' ? 'tr' : 'en')}
            style={{ padding: '0.25rem 0.5rem', display: 'flex', alignItems: 'center', fontSize: '0.875rem' }}
            title={language === 'tr' ? 'Switch to English' : 'Türkçe diline geç'}
          >
            {language === 'en' ? 'TR' : 'EN'}
          </button>
          {view !== 'upload' && (
            <button className="secondary" onClick={goHome} title={language === 'tr' ? 'Ana Sayfaya Dön' : 'Return to Home'} style={{ padding: '0.5rem', display: 'flex', alignItems: 'center' }}>
              <Home size={18} />
            </button>
          )}
        </div>
      </header>

      <main className="fade-enter">
        {view === 'upload' && <UploadView onComplete={handleAnalysisComplete} language={language} />}
        {view === 'studio' && <StudioView sessionId={sessionData.session_id} language={language} onGoHome={goHome} />}
      </main>
    </div>
  );
}

export default App;
