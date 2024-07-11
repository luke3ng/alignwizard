    function redirect() {
        // Get the value from the dropdown
        var dropdown = document.getElementById("patientList");
        var selectedValue = dropdown.options[dropdown.selectedIndex].value;

        // Redirect to another page with the selected value as a query parameter
        window.location.href = "/patientHome?data=" + selectedValue;
    }