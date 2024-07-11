document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("savePatient").addEventListener("click", function(event) {
        event.preventDefault(); // Prevent default form submission behavior

        const patient = document.getElementById('patient').value;


        fetch("/createPatient", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ patient:patient})
        })
        .then(response => {
            if (response.ok) {
                window.location.href = "/findPatient"; // Redirect to home page on success
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