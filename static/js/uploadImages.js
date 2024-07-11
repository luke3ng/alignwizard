document.addEventListener("DOMContentLoaded", function() {
   let modes = {
       Front: false,
       Back: false,
       Left: false,
       Right: false
   };


   function toggleMode(side) {
       modes[side] = !modes[side];
       if (modes[side]) {
           $("#imageSrc" + side).addClass("clickable");
       } else {
           $("#imageSrc" + side).removeClass("clickable");
       }
   }


   function handleFileSelect(event, imgElementId, side) {
       const file = event.target.files[0];
       if (file) {
           const fileType = file.type;
           if (/^image\//.test(fileType)) {
               const imgElement = document.getElementById(imgElementId);
               imgElement.src = URL.createObjectURL(file);


               const img = new Image();
               img.src = imgElement.src;
               img.onload = function() {
                   const displayWidth = imgElement.offsetWidth;
                   const displayHeight = imgElement.offsetHeight;


                   console.log(side + " image display dimensions: ", displayWidth, displayHeight);


                   imgElement.addEventListener("click", function(event) {
                       if (modes[side]) {
                           const rect = imgElement.getBoundingClientRect();
                           const x = event.clientX - rect.left; // Coordinates relative to the image
                           const y = event.clientY - rect.top;  // Coordinates relative to the image
                           console.log("Client-side coordinates:", x, y, "Image dimensions:", rect.width, rect.height);
                           $.ajax({
                               type: "POST",
                               url: "/get_coordinates" + side,
                               data: JSON.stringify({ ["x" + side]: x, ["y" + side]: y, width: rect.width, height: rect.height }),
                               contentType: "application/json",
                               success: function(response) {
                                   console.log(response);
                                   if (response.image) {
                                       $("#imageSrc" + side).attr("src", "data:image/png;base64," + response.image);
                                   }
                               },
                               error: function(error) {
                                   console.error("Error:", error);
                               }
                           });
                       }
                   });
               };
           } else {
               console.error("Unsupported file type. Only images are supported.");
           }
       } else {
           console.error("No file selected or file input is not supported.");
       }


       const reader = new FileReader();
       reader.onload = function(event) {
           const imgData = event.target.result;
           $.ajax({
               type: "POST",
               url: "/upload" + side,
               data: JSON.stringify({ ["img" + side]: imgData }),
               contentType: "application/json",
               success: function(response) {
                   console.log(response);
               },
               error: function(error) {
                   console.error("Error:", error);
               }
           });
       };
       reader.readAsDataURL(file);
   }


   ["Front", "Back", "Left", "Right"].forEach(function(side) {
       $("#addLines" + side).click(function() {
           toggleMode(side);
       });


       $("#fileInput" + side).on("change", function(event) {
           handleFileSelect(event, "imageSrc" + side, side);
       });
   });


   document.getElementById("saveImages").addEventListener("click", function(event) {
       event.preventDefault(); // Prevent default form submission behavior


       const urlParams = new URLSearchParams(window.location.search);
       const patientData = urlParams.get('data');


       fetch("/saveImages", {
           method: "POST",
           headers: {
               "Content-Type": "application/json"
           },
           body: JSON.stringify({ patientData: patientData })
       })
       .then(response => {
           if (response.ok) {
               window.location.href = `/patientHome?data=${patientData}`;
           } else {
               return response.json().then(data => {
                   throw new Error(data.error);
               });
           }
       })
       .catch(error => {
           console.error("Error:", error);
           alert("Save failed: " + error.message); // Show error message
       });
   });
});

