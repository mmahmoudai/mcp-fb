import React, { useState } from 'react';

function SearchComponent() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [status, setStatus] = useState('');

    const handleSearch = async () => {
        setStatus(`Searching for: ${query}...`);
        setResults([]);
        try {
            const response = await fetch('http://localhost:8000/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }
            // Assuming backend returns { "search_results": [...] }
            setResults(data.search_results || (Array.isArray(data) ? data : []));
            setStatus('Search successful!');
        } catch (error) {
            console.error('Search error:', error);
            setResults([]);
            setStatus(`Search failed: ${error.message}`);
        }
    };

    return (
        <div>
            <h2>Search Posts</h2>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter search query"
            />
            <button onClick={handleSearch}>Search</button>

            {status && <p>Status: {status}</p>}

            <h3>Results:</h3>
            {results.length > 0 ? (
                <ul>
                    {results.map((result, index) => (
                        // Assuming results are strings for now. If they are objects, adjust accordingly.
                        <li key={index}>{typeof result === 'object' ? JSON.stringify(result) : result}</li>
                    ))}
                </ul>
            ) : (
                <p>No results yet.</p>
            )}
        </div>
    );
}

export default SearchComponent;
