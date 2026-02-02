/**
 * Dashboard Page
 * Main metrics and overview dashboard
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getHealth, getMetrics, getTasks, formatDate, getStateColor } from '../services/api';
import './Dashboard.css';

function MetricCard({ title, value, subtitle, color }) {
    return (
        <div className="metric-card">
            <div className="metric-value" style={{ color: color || 'var(--accent-color)' }}>
                {value}
            </div>
            <div className="metric-title">{title}</div>
            {subtitle && <div className="metric-subtitle">{subtitle}</div>}
        </div>
    );
}

function Dashboard() {
    const [metrics, setMetrics] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        try {
            const [metricsData, tasksData, healthData] = await Promise.all([
                getMetrics(),
                getTasks(10),
                getHealth(),
            ]);
            setMetrics(metricsData);
            setTasks(tasksData);
            setHealth(healthData);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return <div className="loading">Loading dashboard...</div>;
    }

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <h1>Dashboard</h1>
                <div className="health-badge" data-status={health?.status || 'unknown'}>
                    {health?.status === 'healthy' ? '● Healthy' : '● Offline'}
                </div>
            </div>

            {error && <div className="error-banner">Error: {error}</div>}

            <div className="metrics-grid">
                <MetricCard
                    title="Total Tasks"
                    value={metrics?.total_tasks || 0}
                />
                <MetricCard
                    title="Completed"
                    value={metrics?.completed || 0}
                    color="var(--success-color)"
                />
                <MetricCard
                    title="Success Rate"
                    value={`${((metrics?.success_rate || 0) * 100).toFixed(1)}%`}
                    color="var(--success-color)"
                />
                <MetricCard
                    title="Stop Rate"
                    value={`${((metrics?.stop_rate || 0) * 100).toFixed(1)}%`}
                    color="var(--warning-color)"
                />
            </div>

            <div className="panel">
                <div className="panel-header">
                    <h2>Recent Tasks</h2>
                    <Link to="/tasks" className="link-button">View All →</Link>
                </div>

                {tasks.length === 0 ? (
                    <div className="empty-state">No tasks yet. Submit your first task!</div>
                ) : (
                    <table className="tasks-table">
                        <thead>
                            <tr>
                                <th>Task</th>
                                <th>Repository</th>
                                <th>Status</th>
                                <th>Started</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tasks.slice(0, 5).map((task) => (
                                <tr key={task.id}>
                                    <td className="task-cell">{task.task?.substring(0, 40)}...</td>
                                    <td className="repo-cell">{task.repo}</td>
                                    <td>
                                        <span
                                            className="status-badge"
                                            style={{ backgroundColor: getStateColor(task.final_state) }}
                                        >
                                            {task.final_state || 'Running'}
                                        </span>
                                    </td>
                                    <td>{formatDate(task.started_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            <div className="quick-actions">
                <Link to="/run" className="action-button primary">+ New Task</Link>
                <Link to="/config" className="action-button">⚙️ Configuration</Link>
            </div>
        </div>
    );
}

export default Dashboard;
