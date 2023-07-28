const emailInput = document.querySelector("#id_email");
  //  const emailError = document.querySelector('#id_email_error');
  const firstNameInput = document.querySelector("#id_first_name");
  const lastNameInput = document.querySelector("#id_last_name");
  const companyInput = document.querySelector("#id_company");
  const password1Input = document.querySelector("#id_password1");
  const password2Input = document.querySelector("#id_password2");
  const registerButton = document.querySelector("#register-btn");
  const error = document.querySelector("#client-error");
  const emailCrossMarker = document.querySelector(".email-cross-marker");
  const fnameCrossMarker = document.querySelector(".fname-cross-marker");
  const lnameCrossMarker = document.querySelector(".lname-cross-marker");
  const companyCrossMarker = document.querySelector(".company-cross-marker");
  const password1CrossMarker = document.querySelector(
    ".password1-cross-marker"
  );
  const password2CrossMarker = document.querySelector(
    ".password2-cross-marker"
  );
  window.onload = function() {
 
    emailInput.value=""
    emailInput.blur()
    password1Input.value=""
    password1Input.focus()
    password1Input.blur()
   // $("#register-form").reset()
   
    $(".fa-times").hide()
    $(".fa-check").hide()
    
}

  emailInput.addEventListener("input", () => {
    checkServerError();
    emailCrossMarker.style.display = "inline";
    if (emailInput.value.trim() !== "") {
      if (emailInput.validity.typeMismatch) {
        error.textContent = "Please enter a valid email address.";
        emailInput.setCustomValidity("Please enter a valid email address.");
        emailCrossMarker.classList.replace("fa-check", "fa-times");
      } else {
        error.textContent = "";
        emailCrossMarker.classList.replace("fa-times", "fa-check");
        emailInput.setCustomValidity("");
      }
    } else {
      error.textContent = "Please enter a valid email address.";
      emailInput.setCustomValidity("Please enter a valid email address.");
      emailCrossMarker.classList.replace("fa-check", "fa-times");
    }
    checkInputs();
  });
  firstNameInput.addEventListener("input", () => {
    checkServerError();
    fnameCrossMarker.style.display = "inline";
    const firstName = firstNameInput.value.trim();

    if (firstName === "") {
      error.textContent = "First name is required.";
      firstNameInput.setCustomValidity("First name is required.");
      fnameCrossMarker.classList.replace("fa-check", "fa-times");
    } else {
      error.textContent = "";
      firstNameInput.setCustomValidity("");
      fnameCrossMarker.classList.replace("fa-times", "fa-check");
    }
    checkInputs();
  });
  lastNameInput.addEventListener("input", () => {
    checkServerError();
    const lastName = lastNameInput.value.trim();
    lnameCrossMarker.style.display = "inline";
    if (lastName === "") {
      error.textContent = "Last name is required.";
      lastNameInput.setCustomValidity("Last name is required.");

      lnameCrossMarker.classList.replace("fa-check", "fa-times");
    } else {
      error.textContent = "";
      lastNameInput.setCustomValidity("");
      lnameCrossMarker.classList.replace("fa-times", "fa-check");
    }
    checkInputs();
  });
  companyInput.addEventListener("input", () => {
    checkServerError();
    const company = companyInput.value.trim();
    companyCrossMarker.style.display = "inline";
    if (company === "") {
      error.textContent = "Company name is required.";
      companyInput.setCustomValidity("Comapny name is required.");

      companyCrossMarker.classList.replace("fa-check", "fa-times");
    } else {
      error.textContent = "";
      companyInput.setCustomValidity("");
      companyCrossMarker.classList.replace("fa-times", "fa-check");
    }
    checkInputs();
  });
  password1Input.addEventListener("input", () => {
    checkServerError();
    
    password1CrossMarker.style.display = "inline";
    error.textContent = "";
    let password = password1Input.value;
    let isValid = true;
    checkConfirmPassword();
    if (error.textContent.trim() !== "") {
      password2CrossMarker.classList.replace("fa-check", "fa-times");
    }
    if (password.length < 8 || password.length > 24) {
      error.innerHTML = "Password must be between 8 to 24 characters long.";
      password1Input.setCustomValidity(
        "Password must be between 8 to 24 characters long."
      );
      isValid = false;
    }
    if (!/[A-Z]/.test(password)) {
    
      error.innerHTML +=
        "<br> Password must contain at least one uppercase letter.";
      password1Input.setCustomValidity(
        "Password must contain at least one uppercase letter."
      );
      isValid = false;
    }

    if (!/\d/.test(password)) {
      error.innerHTML += "<br> Password must contain at least one digit.";
      password1Input.setCustomValidity(
        "Password must contain at least one digit."
      );
      isValid = false;
    }
    if (!/\W/.test(password)) {
       error.innerHTML +=
        "<br> Password must contain at least one special character.";
      password1Input.setCustomValidity(
        "Password must contain at least one special character."
      );
      isValid = false;
    }

    if (isValid) {
      error.textContent = "";
      password1Input.setCustomValidity("");
      password1CrossMarker.classList.replace("fa-times", "fa-check");
    } else password1CrossMarker.classList.replace("fa-check", "fa-times");
    checkInputs();
  });

  password2Input.addEventListener("input", () => {
    checkConfirmPassword();
  });
  function checkInputs() {
    if (
      emailInput.value &&
      firstNameInput.value &&
      lastNameInput.value &&
      password1Input.value &&
      password2Input.value &&
      companyInput.value &&
      document.querySelector(".fa-times") === null
    ) {
      registerButton.disabled = false;
    } else registerButton.disabled = true;
  }
  function checkServerError() {
    if (document.getElementById("server-error") !== null) {
      document.getElementById("server-error").style.display = "none";
    }
  }
  function checkConfirmPassword() {
    checkServerError();
    password2CrossMarker.style.display = "inline";

    const confirmPassword = password2Input.value;
    const password = password1Input.value;

    if (confirmPassword.trim() === "" || confirmPassword !== password) {
      error.innerHTML = "Passwords do not match. <br>";
      password2Input.setCustomValidity("Passwords do not match.");
      password2CrossMarker.classList.replace("fa-check", "fa-times");
    } else {
      error.innerHTML = "";
      password2Input.setCustomValidity("");
      password2CrossMarker.classList.replace("fa-times", "fa-check");
    }
    checkInputs();
  }
  setTimeout(function () {
    if( document.getElementById("flash-message") !== null)
    document.getElementById("flash-message").style.display = "none";
  }, 3000);