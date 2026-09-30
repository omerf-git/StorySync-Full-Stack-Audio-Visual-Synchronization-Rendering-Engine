import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronRight, ChevronLeft, Video, Loader2, Download, Home } from 'lucide-react';

const StudioView = ({ sessionId, language = 'en', onGoHome }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const fetchImages = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`/api/session/${sessionId}/images`);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error loading images.');
    } finally {
      setLoading(false);
    }
  };

  const handleMoreImages = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`/api/session/${sessionId}/images?more=true`);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error loading images.');
    } finally {
      setLoading(false);
    }
  };

  const handleNextKeyword = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`/api/session/${sessionId}/next_keyword`);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search with a different keyword.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, [sessionId]);

  const handleNext = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`/api/session/${sessionId}/next`);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to skip to next segment.');
    } finally {
      setLoading(false);
    }
  };

  const handlePrev = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`/api/session/${sessionId}/prev`);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to go to previous segment.');
    } finally {
      setLoading(false);
    }
  };

  const generateVideo = async (imageUrl) => {
    if (generating) return;
    setGenerating(true);
    setError('');

    try {
      // Create an invisible anchor to download the file directly from the response blob
      const res = await axios.post(`/api/session/${sessionId}/generate_video`, {
        image_url: imageUrl,
        ken_burns: true,
        zoom_direction: "in"
      }, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `segment_${data.index + 1}.mp4`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);

      // Successfully generated, load next segment automatically
      fetchImages();
    } catch (err) {
      console.error(err);
      let errorMsg = 'An error occurred while generating video.';
      if (err.response?.data instanceof Blob) {
        try {
          const text = await err.response.data.text();
          const json = JSON.parse(text);
          errorMsg = json.detail || errorMsg;
        } catch (e) {
          // Ignore parse errors
        }
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      setError(errorMsg);
    } finally {
      setGenerating(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="card" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <Loader2 className="spinner" size={32} color="var(--accent-color)" />
      </div>
    );
  }

  if (data?.status === 'completed') {
    return (
      <div className="card fade-enter" style={{ textAlign: 'center', padding: '4rem 2rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <h2 style={{ color: 'var(--success-color)', fontSize: '2.5rem', marginBottom: '1rem' }}>{language === 'tr' ? 'Tebrikler!' : 'Congratulations!'}</h2>
        <p style={{ fontSize: '1.2rem', color: 'var(--text-color)', marginBottom: '1rem' }}>{data.message}</p>
        <p style={{ color: 'var(--text-muted)', marginBottom: '3rem', maxWidth: '600px' }}>
          {language === 'tr' 
            ? 'İndirilen MP4 dosyalarını video düzenleyicinizde birleştirerek belgeselinizi tamamlayabilirsiniz.' 
            : 'You can combine the downloaded MP4 files in your video editor to complete your documentary.'}
        </p>
        
        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <button 
            className="secondary" 
            onClick={handlePrev} 
            style={{ padding: '1rem 2rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <ChevronLeft size={24} /> {language === 'tr' ? 'Önceki Görsel Aramaya Dön' : 'Return to Previous Search'}
          </button>
          
          <button 
            className="primary" 
            onClick={onGoHome} 
            style={{ padding: '1rem 2rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'var(--error-color)', color: 'white' }}
          >
            <Home size={24} /> {language === 'tr' ? 'Ana Sayfaya Dön' : 'Return to Homepage'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
          <Video size={24} color="var(--accent-color)" /> Stüdyo
          <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 400 }}>| {language === 'tr' ? 'Parça' : 'Segment'} {data?.index + 1}</span>
        </h2>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="secondary" onClick={handlePrev} disabled={loading || generating || data?.index === 0}>
            <ChevronLeft size={20} /> {language === 'tr' ? 'Önceki' : 'Previous'}
          </button>
          <button className="secondary" onClick={handleNext} disabled={loading || generating}>
            {language === 'tr' ? 'Sonraki' : 'Next'} <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {error && <div style={{ color: 'var(--error-color)', marginBottom: '1rem' }}>{error}</div>}

      {generating && (
        <div style={{ backgroundColor: 'rgba(201, 154, 76, 0.1)', border: '1px solid var(--accent-color)', padding: '1rem', borderRadius: '8px', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Loader2 className="spinner" color="var(--accent-color)" />
          <span>{language === 'tr' ? 'Video arka planda oluşturuluyor, lütfen bekleyin... Tamamlandığında otomatik olarak indirilecektir.' : 'Video is being generated in the background, please wait... It will download automatically when complete.'}</span>
        </div>
      )}

      {data && (
        <>
          <div style={{ backgroundColor: 'var(--bg-color)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{language === 'tr' ? 'Çeviri:' : 'Translation:'}</div>
            <p style={{ fontSize: '1.15rem', fontWeight: 600, lineHeight: 1.4, marginBottom: '0.5rem', color: 'var(--text-color)' }}>
              {language === 'tr' 
                ? (data.turkish_translation || data.turkish_sum || "Çeviri bulunamadı") 
                : (data.english_translation || data.english_sum || "No translation found")}
            </p>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.5rem', opacity: 0.7 }}>
              <span>{language === 'tr' ? 'Arama Anahtar Kelimesi:' : 'Search Keyword:'}</span>
              <span style={{ fontStyle: 'italic' }}>{data.keyword_used}</span>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h3 style={{ color: 'var(--text-muted)' }}>{language === 'tr' ? 'Bu parça için bir arka plan seçin:' : 'Select a background for this segment:'}</h3>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                className="secondary"
                onClick={handleNextKeyword}
                disabled={loading || generating}
                style={{ padding: '0.5rem', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                title={language === 'tr' ? 'Oluşturulan farklı bir anahtar kelime ile ara' : 'Search with a different generated keyword'}
              >
                🔑
              </button>
              {data.total_cached > 5 && (
                <button
                  className="secondary"
                  onClick={handleMoreImages}
                  disabled={loading || generating}
                  style={{ padding: '0.5rem', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  title={language === 'tr' ? 'Aynı anahtar kelimeyle daha fazla görsel getir' : 'Fetch more images with the same keyword'}
                >
                  🔄
                </button>
              )}
            </div>
          </div>

          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 0' }}>
              <Loader2 className="spinner" size={32} color="var(--accent-color)" />
            </div>
          ) : (
            <div className="image-grid">
              {data.images.map((img, idx) => (
                <div key={idx} className="image-card" onClick={() => generateVideo(img.imageUrl)}>
                  <img src={img.imageUrl} alt={img.title || 'Option'} loading="lazy" />
                  <div className="overlay">
                    <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{img.source || 'Unknown Source'}</div>
                    <div style={{ color: '#ccc' }}>{img.imageWidth} x {img.imageHeight}</div>
                  </div>
                </div>
              ))}
              {data.images.length === 0 && (
                <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  {language === 'tr' ? 'Görsel bulunamadı. Lütfen anahtar kelimeyi kontrol edin.' : 'No image found. Please check the keyword.'}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default StudioView;
