document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed");

    const sign_in_btn = document.querySelector("#sign-in-btn");
    const sign_up_btn = document.querySelector("#sign-up-btn");
    const container = document.querySelector(".container");

    if (sign_up_btn && sign_in_btn) {
        sign_up_btn.addEventListener("click", () => {
            console.log("Sign-up button clicked");
            container.classList.add("sign-up-mode");
            document.querySelector(".sign-in-form").style.display = "none";
            document.querySelector(".sign-up-form").style.display = "flex";
        });

        sign_in_btn.addEventListener("click", () => {
            console.log("Sign-in button clicked");
            container.classList.remove("sign-up-mode");
            document.querySelector(".sign-up-form").style.display = "none";
            document.querySelector(".sign-in-form").style.display = "flex";
        });
    }

    // Ensure Lucide is fully loaded before initializing
    const checkLucide = setInterval(() => {
        if (typeof lucide !== "undefined") {
            clearInterval(checkLucide);
            lucide.createIcons();
            console.log("Lucide icons initialized");
        }
    }, 100); // Check every 100ms
});
