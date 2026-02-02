/**
 * Config Page
 * Configuration viewer and editor
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getConfig, updateConfig } from '../services/api';
import './Config.css';

function ConfigItem({ path, value, depth = 0 }) {
    const isObject = typeof value === 'object' && value !== null && !Array.isArray(value);
    const isArray = Array.isArray(value);

    if (isObject) {
        return (
            <div className="config-group" style={{ marginLeft: depth * 16 }}>
                <div className="config-group-header">{path}</div>
                {Object.entries(value).map(([key, val]) => (
                    <ConfigItem key={key} path={key} value={val} depth={depth + 1} />
                ))}
            </div>
        );
    }

    return (
        <div className="config-item" style={{ marginLeft: depth * 16 }}>
            <span className="config-key">{path}</span>
            <span className="config-value">
                {isArray ? JSON.stringify(value) : String(value)}
            </span>
        </div>
    );
}

function Config() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [rawView, setRawView] = useState(false);

    useEffect(() => {
        const fetchConfig = async () => {
            try {
                const data = await getConfig();
                setConfig(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchConfig();
    }, []);

    if (loading) {
        return <div className="loading">Loading configuration...</div>;
    }

    if (error) {
        return (
            <div className="config-page">
                <div className="page-header">
                    <Link to="/" className="back-link">← Dashboard</Link>
                    <h1>Configuration</h1>
                </div>
                <div className="error-banner">Error loading config: {error}</div>
            </div>
        );
    }

    return (
        <div className="config-page">
            <div className="page-header">
                <div>
                    <Link to="/" className="back-link">← Dashboard</Link>
                    <h1>Configuration</h1>
                </div>
                <div className="view-toggle">
                    <button
                        className={!rawView ? 'active' : ''}
                        onClick={() => setRawView(false)}
                    >
                        Structured
                    </button>
                    <button
                        className={rawView ? 'active' : ''}
                        onClick={() => setRawView(true)}
                    >
                        Raw YAML
                    </button>
                </div>
            </div>

            <div className="config-info">
                <span className="info-icon">ℹ️</span>
                Configuration is loaded from <code>config/default.yaml</code>
            </div>

            <div className="panel">
                {rawView ? (
                    <pre className="raw-config">
                        {JSON.stringify(config, null, 2)}
                    </pre>
                ) : (
                    <div className="config-tree">
                        {Object.entries(config).map(([key, value]) => (
                            <ConfigItem key={key} path={key} value={value} />
                        ))}
                    </div>
                )}
            </div>

            <div className="config-sections">
                <div className="config-section">
                    <h3>🎯 Budgets</h3>
                    <div className="section-items">
                        <div className="section-item">
                            <span>Max Tokens</span>
                            <code>{config?.budget?.max_tokens_per_task || 'N/A'}</code>
                        </div>
                        <div className="section-item">
                            <span>Max Cost</span>
                            <code>${config?.budget?.max_cost_per_task || 'N/A'}</code>
                        </div>
                        <div className="section-item">
                            <span>Max Retries</span>
                            <code>{config?.agent?.max_retries || 'N/A'}</code>
                        </div>
                    </div>
                </div>

                <div className="config-section">
                    <h3>⏱️ Timeouts</h3>
                    <div className="section-items">
                        <div className="section-item">
                            <span>Command</span>
                            <code>{config?.sandbox?.command_timeout_seconds || 'N/A'}s</code>
                        </div>
                        <div className="section-item">
                            <span>State</span>
                            <code>{config?.timeouts?.state_timeout_seconds || 'N/A'}s</code>
                        </div>
                    </div>
                </div>

                <div className="config-section">
                    <h3>🌐 Languages</h3>
                    <div className="section-items">
                        {(config?.languages?.supported || ['Python', 'JavaScript', 'TypeScript']).map((lang) => (
                            <div key={lang} className="section-item">
                                <span>{lang}</span>
                                <span className="check">✓</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Config;
