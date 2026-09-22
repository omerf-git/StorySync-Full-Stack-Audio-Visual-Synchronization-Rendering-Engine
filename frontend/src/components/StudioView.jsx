import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronRight, ChevronLeft, Video, Loader2, Download } from 'lucide-react';

const StudioView = ({ sessionId }) => {
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
      setError(err.response?.data?.detail || 'Görseller yüklenirken hata oluştu.');
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
      setError(err.response?.data?.detail || 'Görseller yüklenirken hata oluştu.');
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
      setError(err.response?.data?.detail || 'Farklı kelime ile arama yapılamadı.');
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
      setError(err.response?.data?.detail || 'Sonraki parçaya geçilemedi.');
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
      setError(err.response?.data?.detail || 'Önceki parçaya geçilemedi.');
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
      let errorMsg = 'Video oluşturulurken bir hata oluştu.';
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
      <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <h2 style={{ color: 'var(--success-color)' }}>Tebrikler!</h2>
        <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>{data.message}</p>
        <p style={{ marginTop: '0.5rem' }}>İndirilen MP4 dosyalarını video düzenleyicinizde birleştirerek belgeselinizi tamamlayabilirsiniz.</p>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
          <Video size={24} color="var(--accent-color)" /> Stüdyo
          <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 400 }}>| Parça {data?.index + 1}</span>
        </h2>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="secondary" onClick={handlePrev} disabled={loading || generating || data?.index === 0}>
            <ChevronLeft size={20} /> Önceki
          </button>
          <button className="secondary" onClick={handleNext} disabled={loading || generating}>
            Sonraki <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {error && <div style={{ color: 'var(--error-color)', marginBottom: '1rem' }}>{error}</div>}

      {generating && (
        <div style={{ backgroundColor: 'rgba(201, 154, 76, 0.1)', border: '1px solid var(--accent-color)', padding: '1rem', borderRadius: '8px', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Loader2 className="spinner" color="var(--accent-color)" />
          <span>Video arka planda oluşturuluyor, lütfen bekleyin... Tamamlandığında otomatik indirilecektir.</span>
        </div>
      )}

      {data && (
        <>
          <div style={{ backgroundColor: 'var(--bg-color)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Türkçe Çeviri:</div>
            <p style={{ fontSize: '1.15rem', fontWeight: 600, lineHeight: 1.4, marginBottom: '0.5rem', color: 'var(--text-color)' }}>
              {data.turkish_translation || data.turkish_sum || "Çeviri bulunamadı"}
            </p>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.5rem', opacity: 0.7 }}>
              <span>Arama Terimi:</span>
              <span style={{ fontStyle: 'italic' }}>{data.keyword_used}</span>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h3 style={{ color: 'var(--text-muted)' }}>Bu parça için arka plan seçin:</h3>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                className="secondary"
                onClick={handleNextKeyword}
                disabled={loading || generating}
                style={{ padding: '0.5rem', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                title="Oluşturulan farklı bir anahtar kelime ile arama yap"
              >
                🔑
              </button>
              {data.total_cached > 5 && (
                <button
                  className="secondary"
                  onClick={handleMoreImages}
                  disabled={loading || generating}
                  style={{ padding: '0.5rem', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  title="Aynı anahtar kelime ile farklı görseller getir"
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
                  <img src={img.imageUrl} alt={img.title || 'Seçenek'} loading="lazy" />
                  <div className="overlay">
                    <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{img.source || 'Bilinmeyen Kaynak'}</div>
                    <div style={{ color: '#ccc' }}>{img.imageWidth} x {img.imageHeight}</div>
                  </div>
                </div>
              ))}
              {data.images.length === 0 && (
                <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  Görsel bulunamadı. Lütfen anahtar kelimeyi kontrol edin.
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
