import React, { useState, useEffect } from 'react';
import UploadView from './components/UploadView';
import ReviewView from './components/ReviewView';
import StudioView from './components/StudioView';
import { Film, Home } from 'lucide-react';

function App() {
  const [sessionData, setSessionData] = useState(null);
  const [view, setView] = useState('upload'); // upload | review | studio

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
          setView(data.confirmed ? 'studio' : 'review');
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
    const hasCriticalError = data.json_data.some(item => item.match_status === 3);
    const hasMinorError = data.json_data.some(item => item.match_status === 2);
    
    if (hasCriticalError || hasMinorError) {
      setView('review');
    } else {
      // Auto confirm if perfect
      confirmSession(data.session_id, data.json_data, data.transcript_words);
    }
  };

  const confirmSession = async (sessionId, jsonData, transcriptWords) => {
    try {
      // Update local state first
      setSessionData(prev => ({
        ...prev,
        json_data: jsonData,
        transcript_words: transcriptWords
      }));

      const res = await fetch(`/api/session/${sessionId}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          json_data: jsonData,
          transcript_words: transcriptWords
        })
      });
      const data = await res.json();
      
      if (data.status === 'success') {
        setView('studio');
      } else {
        // Still review needed
        setSessionData(prev => ({
          ...prev,
          json_data: data.json_data,
          transcript_words: data.transcript_words
        }));
      }
    } catch (error) {
      console.error("Error confirming session:", error);
      alert("Error confirming session");
    }
  };

  const goHome = () => {
    localStorage.removeItem('sessionId');
    setSessionData(null);
    setView('upload');
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
            <span style={{ color: 'var(--text-muted)' }}>Session: {sessionData.session_id.substring(0,8)}</span>
          )}
          {view !== 'upload' && (
            <button className="secondary" onClick={goHome} title="Ana Sayfaya Dön" style={{ padding: '0.5rem', display: 'flex', alignItems: 'center' }}>
              <Home size={18} />
            </button>
          )}
        </div>
      </header>

      <main className="fade-enter">
        {view === 'upload' && <UploadView onComplete={handleAnalysisComplete} />}
        {view === 'review' && <ReviewView sessionData={sessionData} onConfirm={confirmSession} />}
        {view === 'studio' && <StudioView sessionId={sessionData.session_id} />}
      </main>
    </div>
  );
}

export default App;
