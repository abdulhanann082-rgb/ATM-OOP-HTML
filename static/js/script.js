// Client-side helpers ONLY — every rule here is re-validated on the
// server, because frontend validation can always be bypassed.

document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss flash messages after a few seconds.
    document.querySelectorAll(".flash").forEach((el) => {
        setTimeout(() => {
            el.style.transition = "opacity 0.4s";
            el.style.opacity = "0";
            setTimeout(() => el.remove(), 400);
        }, 5000);
    });

    // PIN fields: only digits allowed.
    document.querySelectorAll('input[name$="pin"]').forEach((input) => {
        input.addEventListener("input", () => {
            input.value = input.value.replace(/\D/g, "").slice(0, 4);
        });
    });

    // New PIN / confirm PIN live-match hint.
    const newPin = document.getElementById("new_pin");
    const confirmPin = document.getElementById("confirm_pin");
    if (newPin && confirmPin) {
        const check = () => {
            confirmPin.setCustomValidity(
                confirmPin.value && confirmPin.value !== newPin.value ? "PINs do not match" : ""
            );
        };
        newPin.addEventListener("input", check);
        confirmPin.addEventListener("input", check);
    }

    // Amount fields: block negative/zero entry client-side.
    document.querySelectorAll('input[name="amount"]').forEach((input) => {
        input.addEventListener("input", () => {
            if (input.value && Number(input.value) < 0) {
                input.value = "";
            }
        });
    });
});
