import React, { useState } from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

const ReviewView = ({ sessionData, onConfirm, language = 'en' }) => {
  const [editedTranscript, setEditedTranscript] = useState([...sessionData.transcript_words]);
  
  // Only list those with errors (match_status 2 or 3)
  const segmentsWithErrors = sessionData.json_data.filter(item => item.match_status >= 2);

  const getStatusColorClass = (status) => {
    if (status === 1) return 'status-1'; // Green
    if (status === 2) return 'status-2'; // Yellow
    if (status === 3) return 'status-3'; // Red
    return '';
  };

  const handleWordEdit = (index, newWord) => {
    const updated = [...editedTranscript];
    updated[index] = { ...updated[index], word: newWord };
    setEditedTranscript(updated);
  };

  const handleConfirm = () => {
    onConfirm(sessionData.session_id, sessionData.json_data, editedTranscript);
  };

  return (
    <div className="card">
      <h2 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <AlertCircle size={24} color="var(--warning-color)" /> {language === 'tr' ? 'İnceleme Gerekli' : 'Review Required'}
      </h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        {language === 'tr' 
          ? 'Whisper bazı kelimeleri yanlış anlamış olabilir. Özellikle kırmızıyla işaretli (Kritik Hata) alanlarda, orijinal metin ile çıkarılan kelimeler uyuşmuyor. Lütfen aşağıdaki çıktıları orijinal metninizle eşleşecek şekilde inceleyin ve düzeltin.' 
          : 'Whisper might have misunderstood some words. Especially in the areas marked in red (Critical Error), the original text and the extracted words do not match. Please review and adjust the outputs below to match your original script.'}
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginBottom: '2rem' }}>
        {sessionData.json_data.map((item, idx) => (
          <div key={idx} className={`card ${getStatusColorClass(item.match_status)}`} style={{ padding: '1.5rem', backgroundColor: 'rgba(255,255,255,0.02)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <strong>{language === 'tr' ? 'Parça' : 'Segment'} {item.sample_num}</strong>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                {item.match_ratio ? `%${(item.match_ratio * 100).toFixed(1)} ${language === 'tr' ? 'Eşleşme' : 'Match'}` : (language === 'tr' ? 'Eşleşme Bulunamadı' : 'No Match Found')}
              </span>
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{language === 'tr' ? 'Orijinal Metin:' : 'Original Text:'}</div>
              <p>
                {/* Highlight mismatched words in the original text */}
                {item.sample_text.split(' ').map((word, wIdx) => {
                  const isMismatch = item.mismatched_words && item.mismatched_words.includes(word.toLowerCase().replace(/[^\w\s]/gi, ''));
                  return (
                    <span key={wIdx} className={isMismatch ? 'mismatch-highlight' : ''} style={{ marginRight: '4px' }}>
                      {word}
                    </span>
                  );
                })}
              </p>
            </div>

            {item.match_status === 3 && (
              <div style={{ backgroundColor: 'rgba(248, 81, 73, 0.1)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--error-color)' }}>
                <div style={{ fontSize: '0.875rem', color: 'var(--error-color)', marginBottom: '0.5rem', fontWeight: 600 }}>
                  {language === 'tr' ? 'Kritik Hata: Eşleşme %60\'ın altında. İşleme devam etmek için Whisper çıktısını düzenlemelisiniz.' : 'Critical Error: Match is below 60%. You must edit the Whisper output to continue the process.'}
                </div>
                
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
                  {/* Provide a very basic way to edit transcript. In a real app, finding the exact timestamp span is better, but here we can show the whole transcript or just a section */}
                  <textarea 
                    style={{ width: '100%', minHeight: '100px' }}
                    value={editedTranscript.map(t => t.word).join('')}
                    onChange={(e) => {
                      // Note: Complex to edit word by word while maintaining timestamps.
                      // For a simple UX, we might just warn the user.
                      alert(language === 'tr' ? "Gelişmiş düzenleme arayüzü eklenecektir." : "Advanced editing interface will be added.");
                    }}
                    placeholder={language === 'tr' ? "Whisper çıktısı düzenleme alanı" : "Whisper output editing area"}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button onClick={handleConfirm} style={{ backgroundColor: 'var(--success-color)', color: '#fff' }}>
          <CheckCircle2 size={20} /> {language === 'tr' ? 'Değişiklikleri Onayla' : 'Confirm Edits'}
        </button>
      </div>
    </div>
  );
};

export default ReviewView;
