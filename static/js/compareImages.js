document.addEventListener("DOMContentLoaded", function() {
    const urlParams = new URLSearchParams(window.location.search);
    const patient = urlParams.get('patient');
    const dataElement = document.getElementById('patientData');
    const data = JSON.parse(dataElement.textContent);

    console.log("Patient data:", data);

    if (patient) {
        document.getElementById('patientName').textContent = patient;
    }

    if (data.length >= 2) {
        // Process the first set of images
        const item1 = data.find(item => item.id == urlParams.get('date1'));
        if (item1) {
            document.getElementById('front_img_1').src = 'data:image/jpeg;base64,' + item1.frontImage;
            document.getElementById('left_img_1').src = 'data:image/jpeg;base64,' + item1.leftImage;
            document.getElementById('back_img_1').src = 'data:image/jpeg;base64,' + item1.backImage;
            document.getElementById('right_img_1').src = 'data:image/jpeg;base64,' + item1.rightImage;
        }

        // Process the second set of images
        const item2 = data.find(item => item.id == urlParams.get('date2'));
        if (item2) {
            document.getElementById('front_img_2').src = 'data:image/jpeg;base64,' + item2.frontImage;
            document.getElementById('left_img_2').src = 'data:image/jpeg;base64,' + item2.leftImage;
            document.getElementById('back_img_2').src = 'data:image/jpeg;base64,' + item2.backImage;
            document.getElementById('right_img_2').src = 'data:image/jpeg;base64,' + item2.rightImage;
        }
    }
});
