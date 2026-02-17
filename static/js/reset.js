const passwordInput = document.getElementById("password");
const confirmPasswordInput = document.getElementById("confirmPassword");
const passwordMessage = document.getElementById("password-message");
const errorElement = document.getElementById("passwordError");

// Show password rules
passwordInput.addEventListener("focus", () => passwordMessage.style.display = "block");

// Check password strength dynamically
passwordInput.addEventListener("keyup", () => {
    const val = passwordInput.value;
    const check = (id, regex) => {
        const el = document.getElementById(id);
        if (regex.test(val)) el.classList.add("valid");
        else el.classList.remove("valid");
    };
    check("low", /[a-z]/);
    check("upp", /[A-Z]/);
    check("num", /[0-9]/);
    check("spec", /[@$!%*?&_#]/);
    check("len", /.{8,}/);

    validateMatch();
});

// Confirm password match
confirmPasswordInput.addEventListener("input", validateMatch);

function validateMatch() {
    const p1 = passwordInput.value;
    const p2 = confirmPasswordInput.value;

    if (p2 === "") { errorElement.textContent = ""; return; }
    if (p1 === p2) { 
        errorElement.textContent = "✔ Passwords match"; 
        errorElement.className = "success"; 
    } else { 
        errorElement.textContent = "✖ Passwords do not match"; 
        errorElement.className = "error"; 
    }
}

// Toggle password visibility
function setupToggle(btnId, fieldId) {
    const btn = document.getElementById(btnId);
    const field = document.getElementById(fieldId);
    btn.addEventListener("click", () => {
        const isPass = field.type === "password";
        field.type = isPass ? "text" : "password";
        btn.textContent = isPass ? "🔒" : "👁️";
    });
}

setupToggle("togglePassword", "password");
setupToggle("toggleConfirmPassword", "confirmPassword");