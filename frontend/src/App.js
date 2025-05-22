import React, { useState, useRef } from 'react';
import axios from 'axios';
import './App.css';
import '@fortawesome/fontawesome-free/css/all.min.css';

const App = () => {
  const [pdfFile, setPdfFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [archiveUrl, setArchiveUrl] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null); // Для отображения ошибок
  const pdfInputRef = useRef(null);
  const videoInputRef = useRef(null);

  // Базовый URL бэкенда (замени на актуальный)
  const API_BASE_URL = 'https://service-lessons.onrender.com';

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (type === 'pdf') {
      setPdfFile(file);
    } else {
      setVideoFile(file);
    }
    setErrorMessage(null); // Сбрасываем ошибку при выборе нового файла
  };

  const handleDrop = (e, type) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (type === 'pdf' && file.type === 'application/pdf') {
      setPdfFile(file);
    } else if (type === 'video' && file.type.startsWith('video/')) {
      setVideoFile(file);
    } else {
      setErrorMessage(`Неверный формат файла для ${type === 'pdf' ? 'PDF' : 'видео/аудио'}`);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!pdfFile) {
      setErrorMessage('Пожалуйста, выберите PDF файл');
      return;
    }

    setUploading(true);
    setProgress(0);
    setArchiveUrl(null);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append('file', pdfFile); // Убедимся, что имя поля совпадает с ожиданием бэкенда
    if (videoFile) {
      formData.append('video_file', videoFile);
    }

    try {
      // Отправляем файл на бэкенд
      const uploadResponse = await axios.post(`${API_BASE_URL}/api/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percent);
        },
      });

      // Предполагаем, что бэкенд возвращает archive_url напрямую после обработки
      if (uploadResponse.data.archive_url) {
        setArchiveUrl(`${API_BASE_URL}${uploadResponse.data.archive_url}`);
      } else {
        setErrorMessage('Архив не был сгенерирован. Проверьте бэкенд.');
      }

      setUploading(false);
      setProgress(0);
    } catch (error) {
      setErrorMessage(
        'Ошибка при обработке: ' + (error.response?.data?.error || error.message)
      );
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="upload-container">
      <h1>Сгенерируйте видеоуроки!</h1>
      <form onSubmit={handleSubmit}>
        <div
          className="drop-zone"
          onDrop={(e) => handleDrop(e, 'pdf')}
          onDragOver={handleDragOver}
          onClick={() => pdfInputRef.current.click()}
        >
          <i className="fas fa-cloud-upload-alt"></i>
          <p>{pdfFile ? pdfFile.name : 'Перетащите PDF или кликните для выбора'}</p>
          <input
            type="file"
            accept="application/pdf"
            ref={pdfInputRef}
            style={{ display: 'none' }}
            onChange={(e) => handleFileChange(e, 'pdf')}
          />
        </div>

        <div
          className="drop-zone"
          onDrop={(e) => handleDrop(e, 'video')}
          onDragOver={handleDragOver}
          onClick={() => videoInputRef.current.click()}
        >
          <i className="fas fa-video"></i>
          <p>
            {videoFile ? videoFile.name : 'Перетащите видео/аудио или кликните для выбора (опционально)'}
          </p>
          <input
            type="file"
            accept="video/*,audio/*"
            ref={videoInputRef}
            style={{ display: 'none' }}
            onChange={(e) => handleFileChange(e, 'video')}
          />
        </div>

        <button type="submit" disabled={uploading}>
          {uploading ? 'Обработка...' : 'Создать видеоуроки'}
        </button>

        {uploading && (
          <div className="progress-bar">
            <div style={{ width: `${progress}%` }}>{progress}%</div>
          </div>
        )}
      </form>

      {errorMessage && (
        <div className="error-message" style={{ color: 'red', marginTop: '10px' }}>
          {errorMessage}
        </div>
      )}

      {archiveUrl && (
        <div>
          <h2>Видеоуроки готовы!</h2>
          <p>Скачайте архив с вашими видеоуроками:</p>
          <a href={archiveUrl} download>
            <button style={{ marginTop: '20px' }}>Скачать архив</button>
          </a>
        </div>
      )}
    </div>
  );
};

export default App;