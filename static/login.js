document.addEventListener('DOMContentLoaded', function() {
    // 🔐 LOGIN FORM
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    
    // LOGIN HANDLER - UPDATED ✅
    if (loginForm) {
        const errorMsg = document.getElementById('errorMessage');
        const loginBtn = document.getElementById('loginBtn');
        const btnText = document.getElementById('btnText');
        const loadingSpinner = document.getElementById('loadingSpinner');

        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            loginBtn.disabled = true;
            btnText.textContent = 'Signing In...';
            loadingSpinner.style.display = 'inline-block';
            errorMsg.style.display = 'none';

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ username: email, password })
                });

                const data = await response.json();
                console.log('🔥 FULL LOGIN RESPONSE:', data);
                
                if (response.ok && data.access_token) {
                    localStorage.setItem('token', data.access_token);
                    
                    // 🔥 SMART REDIRECT - Let backend / route handle everything
                    window.location.href = '/';  // Backend decides based on role!
                }
            } catch (error) {
                console.error('Login error:', error);
                errorMsg.textContent = error.message || 'Invalid credentials';
                errorMsg.style.display = 'flex';
            } finally {
                loginBtn.disabled = false;
                btnText.textContent = 'Sign In';
                loadingSpinner.style.display = 'none';
            }
        });
    }

    // 📝 SIGNUP HANDLER - UPDATED ✅
    if (signupForm) {
        const signupErrorMsg = document.getElementById('signupErrorMessage');
        const signupBtn = document.getElementById('signupBtn');
        const signupBtnText = document.getElementById('signupBtnText');
        const signupSpinner = document.getElementById('signupLoadingSpinner');

        signupForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            signupBtn.disabled = true;
            signupBtnText.textContent = 'Creating...';
            signupSpinner.style.display = 'inline-block';
            signupErrorMsg.style.display = 'none';

            try {
                const formData = new FormData(signupForm);
                const response = await fetch('/api/signup', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                console.log('📝 SIGNUP RESPONSE:', data);

                if (response.ok && data.access_token) {
                    localStorage.setItem('token', data.access_token);
                    
                    // 🔥 SMART REDIRECT - Backend / route handles ALL roles
                    window.location.href = '/';  // Backend decides!
                    return;
                }
                
                throw new Error(data.detail || 'Signup failed');
                
            } catch (error) {
                console.error('Signup error:', error);
                signupErrorMsg.textContent = error.message;
                signupErrorMsg.style.display = 'flex';
            } finally {
                signupBtn.disabled = false;
                signupBtnText.textContent = 'Sign Up';
                signupSpinner.style.display = 'none';
            }
        });
    }
});
