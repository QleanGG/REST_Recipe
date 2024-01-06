// Check if the user has a token (authenticated)
const token = localStorage.getItem('access_token');
const userSection = document.getElementById('user-section');
const authSection = document.getElementById('auth-section');

if (token) {
    console.log('Token Found!');
    // User is authenticated, show user section and hide auth section
    userSection.style.display = 'block';
    authSection.style.display = 'none';

    // Add user name if available
    const userName = document.getElementById('user-name');
} else {
    // User is not authenticated, show auth section and hide user section
    userSection.style.display = 'none';
    authSection.style.display = 'block';
}

// Add a click event listener to the "Log Out" link to clear the token
const logOutLink = document.getElementById('logout-link');
logOutLink.addEventListener('click', () => {
    localStorage.removeItem('access_token'); // Remove the token from local storage
    window.location.href = './login.html'; // Redirect to the login page
});

