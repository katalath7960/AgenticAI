import React, { useState, useEffect } from 'react';

// Sample component with intentional code review issues
const UserDashboard = (props) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredUsers, setFilteredUsers] = useState([]);

  // Issue: Missing dependency array causes infinite loop risk
  useEffect(() => {
    fetchUsers();
  });

  // Issue: No error boundary, no abort controller, no loading state management
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/users');
      const data = await response.json();
      setUsers(data);
      setLoading(false);
    } catch (err) {
      console.log(err); // Issue: Using console.log instead of proper error handling
      setLoading(false);
    }
  };

  // Issue: Derived state stored in separate useState (should be computed)
  useEffect(() => {
    const filtered = users.filter(user =>
      user.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredUsers(filtered);
  }, [searchTerm, users]);

  // Issue: Function recreated on every render, should use useCallback
  const handleDelete = (userId) => {
    fetch(`http://localhost:5000/api/users/${userId}`, {
      method: 'DELETE',
    }).then(() => {
      fetchUsers();
    });
  };

  // Issue: dangerouslySetInnerHTML - XSS vulnerability
  const renderBio = (bio) => {
    return <div dangerouslySetInnerHTML={{ __html: bio }} />;
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {/* Issue: No label for input - accessibility */}
      <input
        type="text"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        placeholder="Search users"
      />

      {/* Issue: Using index as key on dynamic list */}
      {filteredUsers.map((user, index) => (
        <div key={index} style={{ border: '1px solid gray', padding: '10px', margin: '5px' }}>
          <h3>{user.name}</h3>
          <p>{user.email}</p>
          {renderBio(user.bio)}

          {/* Issue: Inline function in onClick */}
          <button onClick={() => handleDelete(user.id)}>
            Delete
          </button>

          {/* Issue: No confirmation before destructive action */}
          <div onClick={() => window.location.href = `/users/${user.id}`}>
            {/* Issue: div with onClick instead of button/link - a11y */}
            View Profile
          </div>
        </div>
      ))}

      {/* Issue: Hardcoded API key in frontend code */}
      <input type="hidden" value="sk-1234567890abcdef" />
    </div>
  );
};

export default UserDashboard;
