const authForm = document.querySelector("form");
const passwordInput = document.getElementById("password");
const confirmPasswordInput = document.getElementById("confirmPassword");
const passwordMessage = document.getElementById("password-message");
const errorElement = document.getElementById("passwordError");

    // SHOW SECTION LOGIC
    function showSection(section) {
    document.getElementById("formAction").value = section;
    const sections = ["register", "login", "forgot"];
    
    sections.forEach(s => {
        const div = document.getElementById(s + "Section");
        const isCurrent = (s === section);
        div.style.display = isCurrent ? "block" : "none";

        // IMPORTANT FIX: Disable inputs in hidden sections 
        // This prevents the browser from sending 3 different "email" values
        const inputs = div.querySelectorAll("input");
        inputs.forEach(input => {
            if (isCurrent) {
                input.removeAttribute("disabled");
                input.setAttribute("required", "required");
            } else {
                input.setAttribute("disabled", "disabled"); // Browser will ignore these
                input.removeAttribute("required");
            }
        });
    });

    // Toggle nav link visibility
    document.getElementById("btnGoLogin").style.display = (section === 'register') ? "block" : "none";
    document.getElementById("btnGoRegister").style.display = (section !== 'register') ? "block" : "none";
}

    // PASSWORD STRENGTH VALIDATION
    passwordInput.addEventListener("focus", () => passwordMessage.style.display = "block");
    passwordInput.addEventListener("keyup", () => {
        const val = passwordInput.value;
        const check = (id, regex) => {
            const el = document.getElementById(id);
            regex.test(val) ? el.classList.add("valid") : el.classList.remove("valid");
        };
        check("low", /[a-z]/);
        check("upp", /[A-Z]/);
        check("num", /[0-9]/);
        check("spec", /[@$!%*?&_#]/);
        check("len", /.{8,}/);

        validatePasswords(); // check confirm password live
    });

    // CONFIRM PASSWORD MATCH CHECK
    function validatePasswords() {
        const passwordVal = passwordInput.value;
        const confirmVal = confirmPasswordInput.value;

        if (confirmVal === "") {
            errorElement.textContent = "";
            return;
        }

        if (passwordVal !== confirmVal) {
            errorElement.textContent = "❌ Passwords do not match";
            errorElement.classList.add("error");
            errorElement.classList.remove("success");
        } else {
            errorElement.textContent = "✔ Passwords match";
            errorElement.classList.remove("error");
            errorElement.classList.add("success");
        }
    }
    authForm.addEventListener("submit", function(e) {
    if (document.getElementById("password").value !== document.getElementById("confirmPassword").value &&
        document.getElementById("formAction").value === "register") {
        e.preventDefault();
        document.getElementById("passwordError").textContent = "Passwords do not match";
        document.getElementById("passwordError").classList.add("error");
    }
});

    confirmPasswordInput.addEventListener("keyup", validatePasswords);

    // TOGGLE PASSWORD VISIBILITY
    document.getElementById("togglePassword").addEventListener("click", function() {
        const type = passwordInput.type === "password" ? "text" : "password";
        passwordInput.type = type;
        this.textContent = type === "password" ? "👁️" : "🔒";
    });

    // INITIALIZE SECTION
window.onload = () => {
    const initialSection = authForm.dataset.initialSection || "register";
    showSection(initialSection);
};
