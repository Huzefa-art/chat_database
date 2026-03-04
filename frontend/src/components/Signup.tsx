import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { signup } from '../services/api';
import './Login.css'; // Reusing Login styles for consistency

const Signup: React.FC = () => {
    const [userData, setUserData] = useState({ username: '', password: '', email: '' });
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setUserData({ ...userData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            await signup(userData);
            navigate('/login');
        } catch (err) {
            setError('Signup failed. Username might be taken.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h2>Create Account</h2>
                <p className="auth-subtitle">Join the ERP Analytics Platform</p>
                <form onSubmit={handleSubmit}>
                    {error && <div className="auth-error">{error}</div>}
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            name="username"
                            value={userData.username}
                            onChange={handleChange}
                            required
                            placeholder="Choose a username"
                            autoComplete="username"
                        />
                    </div>
                    <div className="form-group">
                        <label>Email (Optional)</label>
                        <input
                            type="email"
                            name="email"
                            value={userData.email}
                            onChange={handleChange}
                            placeholder="Enter your email"
                            autoComplete="email"
                        />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            name="password"
                            value={userData.password}
                            onChange={handleChange}
                            required
                            placeholder="Create a password"
                            autoComplete="new-password"
                        />
                    </div>
                    <button type="submit" className="auth-button" disabled={isLoading}>
                        {isLoading ? 'Creating account...' : 'Sign Up'}
                    </button>
                </form>
                <p className="auth-footer">
                    Already have an account? <Link to="/login">Login</Link>
                </p>
            </div>
        </div>
    );
};

export default Signup;
