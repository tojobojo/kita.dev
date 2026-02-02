/**
 * Tasks Page
 * Full task history with filtering and detail view
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getTasks, formatDate, getStateColor } from '../services/api';
import './Tasks.css';

function Tasks() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all'); // all, completed, stopped, running
    const [selectedTask, setSelectedTask] = useState(null);

    useEffect(() => {
        const fetchTasks = async () => {
            try {
                const data = await getTasks(100);
                setTasks(data);
            } catch (err) {
                console.error('Failed to fetch tasks:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchTasks();
        const interval = setInterval(fetchTasks, 5000);
        return () => clearInterval(interval);
    }, []);

    const filteredTasks = tasks.filter((task) => {
        if (filter === 'all') return true;
        if (filter === 'completed') return task.final_state === 'COMPLETED';
        if (filter === 'stopped') return ['STOPPED_SAFE', 'STOPPED_ERROR'].includes(task.final_state);
        if (filter === 'running') return !task.final_state;
        return true;
    });

    if (loading) {
        return <div className="loading">Loading tasks...</div>;
    }

    return (
        <div className="tasks-page">
            <div className="page-header">
                <div>
                    <Link to="/" className="back-link">← Dashboard</Link>
                    <h1>Task History</h1>
                </div>
                <Link to="/run" className="action-button primary">+ New Task</Link>
            </div>

            <div className="filters">
                {['all', 'completed', 'stopped', 'running'].map((f) => (
                    <button
                        key={f}
                        className={`filter-btn ${filter === f ? 'active' : ''}`}
                        onClick={() => setFilter(f)}
                    >
                        {f.charAt(0).toUpperCase() + f.slice(1)}
                    </button>
                ))}
            </div>

            <div className="tasks-container">
                <div className="tasks-list">
                    {filteredTasks.length === 0 ? (
                        <div className="empty-state">No tasks match the filter</div>
                    ) : (
                        filteredTasks.map((task) => (
                            <div
                                key={task.id}
                                className={`task-item ${selectedTask?.id === task.id ? 'selected' : ''}`}
                                onClick={() => setSelectedTask(task)}
                            >
                                <div className="task-item-header">
                                    <span
                                        className="status-dot"
                                        style={{ backgroundColor: getStateColor(task.final_state) }}
                                    />
                                    <span className="task-id">{task.id?.substring(0, 8)}</span>
                                </div>
                                <div className="task-description">{task.task}</div>
                                <div className="task-meta">
                                    <span>{task.repo}</span>
                                    <span>{formatDate(task.started_at)}</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {selectedTask && (
                    <div className="task-detail panel">
                        <h2>Task Details</h2>

                        <div className="detail-grid">
                            <div className="detail-item">
                                <label>Task ID</label>
                                <code>{selectedTask.id}</code>
                            </div>
                            <div className="detail-item">
                                <label>Status</label>
                                <span
                                    className="status-badge"
                                    style={{ backgroundColor: getStateColor(selectedTask.final_state) }}
                                >
                                    {selectedTask.final_state || 'Running'}
                                </span>
                            </div>
                            <div className="detail-item">
                                <label>Repository</label>
                                <code>{selectedTask.repo}</code>
                            </div>
                            <div className="detail-item">
                                <label>Started</label>
                                <span>{formatDate(selectedTask.started_at)}</span>
                            </div>
                            <div className="detail-item">
                                <label>Completed</label>
                                <span>{formatDate(selectedTask.completed_at)}</span>
                            </div>
                            <div className="detail-item">
                                <label>Tokens Used</label>
                                <span>{selectedTask.token_usage || '-'}</span>
                            </div>
                            <div className="detail-item">
                                <label>Confidence</label>
                                <span>{selectedTask.confidence_score?.toFixed(2) || '-'}</span>
                            </div>
                        </div>

                        <div className="detail-item full-width">
                            <label>Task Description</label>
                            <div className="task-full-description">{selectedTask.task}</div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default Tasks;
