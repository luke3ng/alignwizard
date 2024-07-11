    $(document).ready(function() {
        $("#sign-in").on("click", function(event) {
            event.preventDefault(); // Prevent default button behavior
            const name = document.getElementById('un').value;
            const password = document.getElementById('pw').value;
            const email = document.getElementById('email').value;

            // Client-side validation
            if (password.length < 8) {
                document.getElementById('userTaken').innerText = 'Password must be at least 8 characters long';
                return;
            }

            const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
            if (!emailPattern.test(email)) {
                document.getElementById('userTaken').innerText = 'Please enter a valid email address';
                return;
            }

            $.ajax({
                type: "POST",
                url: "/createUser",
                data: JSON.stringify({ name: name, password: password, email: email }),
                contentType: "application/json",
                success: function(response) {
                    console.log(response);
                    window.location.href = "/login";
                },
                error: function(error) {
                    console.error("Error:", error);
                    document.getElementById('userTaken').innerText = 'Username taken';
                }
            });
        });
    });