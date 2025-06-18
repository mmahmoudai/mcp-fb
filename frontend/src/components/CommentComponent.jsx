import React, { useState } from 'react';

function CommentComponent() {
    const [postUrl, setPostUrl] = useState('');
    const [commentText, setCommentText] = useState('');
    const [status, setStatus] = useState('');

    const handleSubmitComment = async () => {
        setStatus(`Submitting comment to ${postUrl}...`);
        try {
            const response = await fetch('http://localhost:8000/api/comment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ post_url: postUrl, comment_text: commentText }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }
            setStatus(data.message || 'Comment submitted successfully!');
        } catch (error) {
            console.error('Comment submission error:', error);
            setStatus(`Comment submission failed: ${error.message}`);
        }
    };

    return (
        <div>
            <h2>Comment on Post</h2>
            <div>
                <label htmlFor="postUrl">Post URL:</label><br />
                <input
                    type="text"
                    id="postUrl"
                    value={postUrl}
                    onChange={(e) => setPostUrl(e.target.value)}
                    placeholder="Enter post URL"
                    style={{ width: '80%', marginBottom: '10px' }}
                />
            </div>
            <div>
                <label htmlFor="commentText">Comment:</label><br />
                <textarea
                    id="commentText"
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder="Enter your comment"
                    rows="4"
                    style={{ width: '80%', marginBottom: '10px' }}
                />
            </div>
            <button onClick={handleSubmitComment}>Submit Comment</button>

            {status && <p>Status: {status}</p>}
        </div>
    );
}

export default CommentComponent;
