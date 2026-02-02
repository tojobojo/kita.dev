import { useState } from 'react';

export default function TaskInput({ onSubmit, isLoading }) {
    const [task, setTask] = useState('');
    const [repo, setRepo] = useState('./project'); // Default relative path

    const handleSubmit = (e) => {
        e.preventDefault();
        if (task.trim()) {
            onSubmit(task, repo);
        }
    };

    return (
        <div className="panel">
            <h2>🚀 Start New Mission</h2>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                        Target Repository Path
                    </label>
                    <input
                        type="text"
                        value={repo}
                        onChange={(e) => setRepo(e.target.value)}
                        placeholder="/absolute/path/to/repo"
                        disabled={isLoading}
                    />
                </div>
                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                        Task Description
                    </label>
                    <input
                        type="text"
                        value={task}
                        onChange={(e) => setTask(e.target.value)}
                        placeholder="e.g. Refactor the authentication module..."
                        disabled={isLoading}
                    />
                </div>
                <div style={{ textAlign: 'right' }}>
                    <button type="submit" disabled={isLoading || !task.trim()}>
                        {isLoading ? 'Agent Running...' : 'Deploy Agent'}
                    </button>
                </div>
            </form>
        </div>
    );
}
