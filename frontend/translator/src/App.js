import React, { useState } from 'react';
import './App.css';

function App() {
  const [textToTranslate, setTextToTranslate] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [translationStatus, setTranslationStatus] = useState('');
  const [error, setError] = useState(null);

  const handleInputChange = (event) => {
    setTextToTranslate(event.target.value);
  };

  const handleTranslate = async () => {
    try {
      setTranslationStatus('Translating...');

      const response = await fetch('http://localhost:5000/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: textToTranslate }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const result = await response.json();

      if (result.status === 'queued') {
        setTranslatedText('');
        setTranslationStatus('Translation is in the queue. Please wait.');
      } else if (result.translated_text) {
        setTranslatedText(result.translated_text);
        setTranslationStatus('Translation successful.');
      } else {
        setTranslatedText('');
        setTranslationStatus('Translation failed.');
      }

      setError(null);
    } catch (error) {
      console.error('There was a problem with the fetch operation:', error.message);
      setTranslatedText('');
      setTranslationStatus('Translation failed. Please try again.');
      setError('Error fetching translation. Please try again.');
    }
  };

  return (
    <div className="App">
      <h1>Modern Translation App</h1>
      <textarea
        placeholder="Enter text to translate"
        value={textToTranslate}
        onChange={handleInputChange}
      />
      <button onClick={handleTranslate}>Translate</button>
      {error && <div className="error-message">{error}</div>}
      <div className="translation-status">{translationStatus}</div>
      <div className="translated-text">
        <strong>Translated Text:</strong>
        <p>{translatedText}</p>
      </div>
    </div>
  );
}

export default App;