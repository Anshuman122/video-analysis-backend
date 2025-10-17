import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import Dashboard from './Dashboard';
import AuthenticationButton from './components/AuthenticationButton';
import './App.css';

function App() {
  const { isAuthenticated, isLoading } = useAuth0();

  // Show a loading message while Auth0 is initializing
  if (isLoading) {
    return <div className="loading-container"><h1>Loading Application...</h1></div>;
  }

  return (
    <div className="App">
      <header className="app-header">
        <h1>Video Analysis</h1>
        <AuthenticationButton />
      </header>
      <main>
        {isAuthenticated ? (
          <Dashboard />
        ) : (
          <div className="login-prompt">
            <h2>Welcome!</h2>
            <p>Please log in to access your personal dashboard and analyze videos.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

