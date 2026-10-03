import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { DocumentsPage } from './pages/DocumentsPage';
import { QueryWorkspacePage } from './pages/QueryWorkspacePage';
import { ReviewsPage } from './pages/ReviewsPage';

// Placeholder Pages
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="rl-card p-8 flex flex-col items-center justify-center min-h-[400px] text-center">
      <h2 className="text-xl font-semibold text-rl-neutral-800 mb-2">{title}</h2>
      <p className="text-rl-neutral-500 max-w-md">
        This screen is currently being built. The mock data and layout structure are ready.
      </p>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/queries" replace />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="queries" element={<QueryWorkspacePage />} />
          <Route path="reviews" element={<ReviewsPage />} />
          <Route path="audit" element={<PlaceholderPage title="Audit Log" />} />
          <Route path="settings" element={<PlaceholderPage title="System Settings" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
