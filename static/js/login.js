document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("sign-in").addEventListener("click", function(event) {
        event.preventDefault(); // Prevent default form submission behavior

        const email = document.getElementById('un').value;
        const password = document.getElementById('pw').value;

        fetch("/getUser", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email: email, password: password })
        })
        .then(response => {
            if (response.ok) {
                window.location.href = "/"; // Redirect to home page on success
            } else {
                return response.json().then(data => {
                    throw new Error(data.error);
                });
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Login failed: " + error.message); // Show error message
        });
    });
});