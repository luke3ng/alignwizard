document.addEventListener("DOMContentLoaded", function() {
    const urlParams = new URLSearchParams(window.location.search);
    const patient = urlParams.get('data');
    const dataElement = document.getElementById('patientData');
    const data = JSON.parse(dataElement.textContent);

    if (patient) {
        document.getElementById('patientName').textContent = patient;
        document.getElementById('patientInfo').textContent = patient;
    }

    // Process the data here
    // Loop through the data and set the content for each corresponding element
    data.forEach((item, index) => {
        const frontImg = document.getElementById(`front_img_${index}`);
        const backImg = document.getElementById(`back_img_${index}`);
        const leftImg = document.getElementById(`left_img_${index}`);
        const rightImg = document.getElementById(`right_img_${index}`);

        frontImg.src = item.frontImage;
        backImg.src = item.backImage;
        leftImg.src = item.leftImage;
        rightImg.src = item.rightImage;
    });

    $('input[type=checkbox]').on('change', function (e) {
        // No limit on number of checkboxes
    });
});

function deleteImages() {
    const dates = [...document.querySelectorAll('.inp:checked')].map(e => e.value);
    if (dates.length === 0) {
        alert("Please select at least one date.");
        return;
    }

    const patient = document.getElementById('patientName').textContent;

    // Send selected dates and patient info via fetch
    fetch('/removeImages', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ dates: dates })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        // Optionally, reload the page or update the UI
        window.location.reload();
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
