export default function StatusBadge({ state }) {
    const getStateColor = (s) => {
        if (!s) return 'var(--text-secondary)';
        if (s.includes('STOPPED_ERROR') || s.includes('FAILED')) return 'var(--error-color)';
        if (s.includes('COMPLETED') || s.includes('PASSED')) return 'var(--success-color)';
        if (s === 'IDLE') return 'var(--text-secondary)';
        return 'var(--accent-color)'; // Active states
    };

    return (
        <span
            style={{
                backgroundColor: getStateColor(state),
                color: 'white',
                padding: '0.25rem 0.75rem',
                borderRadius: '12px',
                fontSize: '0.85rem',
                fontWeight: 'bold',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
            }}
        >
            {state || 'OFFLINE'}
        </span>
    );
}
