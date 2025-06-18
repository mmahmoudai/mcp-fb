import React from 'react';
import SearchComponent from './components/SearchComponent';
import CommentComponent from './components/CommentComponent';
import './App.css'; // Ensure App.css exists or remove this line if not used

function App() {
    return (
        <>
            <h1>Facebook Automation Frontend</h1>
            <SearchComponent />
            <hr style={{ margin: '20px 0' }} />
            <CommentComponent />
        </>
    );
}
export default App;
