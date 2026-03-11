import React, { useState } from 'react';

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Issue: Storing JWT in localStorage - security risk
  const handleLogin = async (e) => {
    e.preventDefault();

    const response = await fetch('http://localhost:5000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    // Issue: No error handling for failed requests
    // Issue: Token stored in localStorage instead of HttpOnly cookie
    localStorage.setItem('token', data.token);
    localStorage.setItem('refreshToken', data.refreshToken);

    // Issue: No input sanitization
    // Issue: Password visible in network tab via JSON body (should use HTTPS)
    window.location.href = '/dashboard';
  };

  return (
    // Issue: Using form but no CSRF protection
    <form onSubmit={handleLogin}>
      <h2>Login</h2>

      {/* Issue: autocomplete not set for email/password fields */}
      <div>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
        />
      </div>
      <div>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
        />
      </div>

      {/* Issue: No disabled state while submitting */}
      <button type="submit">Login</button>

      {/* Issue: No error message display */}
      {/* Issue: No loading indicator */}
    </form>
  );
};

export default LoginForm;
