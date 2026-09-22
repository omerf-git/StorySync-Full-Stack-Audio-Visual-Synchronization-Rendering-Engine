import React, { useState } from 'react';
import UploadView from './components/UploadView';
import ReviewView from './components/ReviewView';
import StudioView from './components/StudioView';
import { Film } from 'lucide-react';

function App() {
  const [sessionData, setSessionData] = useState(null);
  const [view, setView] = useState('upload'); // upload | review | studio

  const handleAnalysisComplete = (data) => {
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

  return (
    <div className="container">
      <header className="header">
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Film color="var(--accent-color)" size={28} />
          <span>Google Images to Video</span>
        </h1>
        {sessionData && (
          <span style={{ color: 'var(--text-muted)' }}>Session: {sessionData.session_id.substring(0,8)}</span>
        )}
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
