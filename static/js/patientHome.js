document.addEventListener("DOMContentLoaded", function() {
    const urlParams = new URLSearchParams(window.location.search);
    const patient = urlParams.get('data');

    if (patient) {
        document.getElementById('patientName').textContent = patient;
        document.getElementById('patientInfo').textContent = patient;
    }

    // Embed the data directly into the script
    const data = JSON.parse(document.getElementById('patientData').textContent);
    console.log("Patient data:", data);

    // Process the data here
    // Loop through the data and set the content for each corresponding element
    data.forEach((item, index) => {
        const frontImg = document.getElementById(`front_img_${index}`);
        const backImg = document.getElementById(`back_img_${index}`);
        const leftImg = document.getElementById(`left_img_${index}`);
        const rightImg = document.getElementById(`right_img_${index}`);

        frontImg.src = 'data:image/jpeg;base64,' + item.frontImage;
        backImg.src = 'data:image/jpeg;base64,' + item.backImage;
        leftImg.src = 'data:image/jpeg;base64,' + item.leftImage;
        rightImg.src = 'data:image/jpeg;base64,' + item.rightImage;
    });

    $('input[type=checkbox]').on('change', function (e) {
        if ($('input[type=checkbox]:checked').length > 2) {
            $(this).prop('checked', false);
            alert("allowed only 2");
        }
    });
});

function redirect() {
    const dates = [...document.querySelectorAll('.inp:checked')].map(e => e.value);
    if (dates.length < 2) {
        alert("Please select exactly two dates.");
        return;
    }

    const patient = document.getElementById('patientName').textContent;

    // Redirect to another page with the selected value as a query parameter
    window.location.href = `/compareImages?date1=${encodeURIComponent(dates[0])}&date2=${encodeURIComponent(dates[1])}&patient=${encodeURIComponent(patient)}`;
}
