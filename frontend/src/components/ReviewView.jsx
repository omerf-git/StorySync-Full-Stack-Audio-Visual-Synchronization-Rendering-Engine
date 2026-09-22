import React, { useState } from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

const ReviewView = ({ sessionData, onConfirm }) => {
  const [editedTranscript, setEditedTranscript] = useState([...sessionData.transcript_words]);
  
  // Sadece hatalı olanları listelemek için (match_status 2 veya 3 olanlar)
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
        <AlertCircle size={24} color="var(--warning-color)" /> İnceleme Gerekli
      </h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Whisper bazı kelimeleri yanlış anlamış olabilir. Özellikle kırmızı (Ciddi Hata) ile işaretlenen alanlarda, asıl metin ile sesten çıkarılan kelimeler eşleşmiyor. Lütfen aşağıdaki çıktıları orijinal metninize uygun şekilde düzenleyin.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginBottom: '2rem' }}>
        {sessionData.json_data.map((item, idx) => (
          <div key={idx} className={`card ${getStatusColorClass(item.match_status)}`} style={{ padding: '1.5rem', backgroundColor: 'rgba(255,255,255,0.02)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <strong>Parça {item.sample_num}</strong>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                {item.match_ratio ? `%${(item.match_ratio * 100).toFixed(1)} Eşleşme` : 'Eşleşme Bulunamadı'}
              </span>
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Orijinal Metin:</div>
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
                <div style={{ fontSize: '0.875rem', color: 'var(--error-color)', marginBottom: '0.5rem', fontWeight: 600 }}>Ciddi Hata: Eşleşme %60'ın altında. Sürecin devam etmesi için Whisper çıktısını düzenlemelisiniz.</div>
                
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
                  {/* Provide a very basic way to edit transcript. In a real app, finding the exact timestamp span is better, but here we can show the whole transcript or just a section */}
                  <textarea 
                    style={{ width: '100%', minHeight: '100px' }}
                    value={editedTranscript.map(t => t.word).join('')}
                    onChange={(e) => {
                      // Note: Complex to edit word by word while maintaining timestamps.
                      // For a simple UX, we might just warn the user.
                      alert("Gelişmiş düzenleme arayüzü eklenecektir.");
                    }}
                    placeholder="Whisper çıktısı düzenleme alanı"
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button onClick={handleConfirm} style={{ backgroundColor: 'var(--success-color)', color: '#fff' }}>
          <CheckCircle2 size={20} /> Düzenlemeleri Onayla
        </button>
      </div>
    </div>
  );
};

export default ReviewView;
