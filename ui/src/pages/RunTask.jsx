/**
 * Run Task Page
 * Submit new tasks to the agent
 */
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { submitTask } from '../services/api';
import './RunTask.css';

function RunTask() {
    const navigate = useNavigate();
    const [task, setTask] = useState('');
    const [repoPath, setRepoPath] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!task.trim() || !repoPath.trim()) {
            setError('Both fields are required');
            return;
        }

        if (task.split(' ').length < 3) {
            setError('Task description should be at least 3 words');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const result = await submitTask(task, repoPath);
            // Navigate to tasks page with the new job ID
            navigate(`/tasks?highlight=${result.job_id}`);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="run-page">
            <div className="page-header">
                <div>
                    <Link to="/" className="back-link">← Dashboard</Link>
                    <h1>New Task</h1>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="task-form panel">
                {error && (
                    <div className="form-error">
                        <span>⚠️</span> {error}
                    </div>
                )}

                <div className="form-group">
                    <label htmlFor="task">Task Description</label>
                    <textarea
                        id="task"
                        value={task}
                        onChange={(e) => setTask(e.target.value)}
                        placeholder="Describe what you want the agent to do..."
                        rows={4}
                        disabled={loading}
                    />
                    <span className="form-hint">
                        Be specific. Example: "Add unit tests for the authentication module in auth.py"
                    </span>
                </div>

                <div className="form-group">
                    <label htmlFor="repo">Repository Path</label>
                    <input
                        type="text"
                        id="repo"
                        value={repoPath}
                        onChange={(e) => setRepoPath(e.target.value)}
                        placeholder="/path/to/repository"
                        disabled={loading}
                    />
                    <span className="form-hint">
                        Absolute path to the repository on the server
                    </span>
                </div>

                <div className="form-actions">
                    <button type="submit" className="submit-btn" disabled={loading}>
                        {loading ? (
                            <>
                                <span className="spinner" />
                                Submitting...
                            </>
                        ) : (
                            '🚀 Submit Task'
                        )}
                    </button>
                </div>
            </form>

            <div className="tips-section">
                <h3>💡 Tips for Good Tasks</h3>
                <ul>
                    <li>Be specific about what files or modules to modify</li>
                    <li>Mention the expected outcome (e.g., "tests should pass")</li>
                    <li>Keep scope reasonable - one feature or fix at a time</li>
                    <li>Include relevant context if needed</li>
                </ul>
            </div>
        </div>
    );
}

export default RunTask;
