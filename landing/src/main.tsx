import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import App from './App';
import { DocsPage } from './docs/components/DocsPage';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/docs" element={<Navigate to="/docs/introduction" replace />} />
        <Route path="/docs/:slug" element={<DocsPage />} />
        <Route path="*" element={<DocsPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
