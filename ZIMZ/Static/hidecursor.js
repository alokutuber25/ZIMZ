document.addEventListener("DOMContentLoaded", () => {
    // Create a glowing cursor element
    const cursor = document.createElement("div");
    cursor.classList.add("glowing-cursor");
    document.body.appendChild(cursor);

    // Update cursor position based on mouse movement
    document.addEventListener("mousemove", (e) => {
        cursor.style.left = `${e.clientX}px`;
        cursor.style.top = `${e.clientY}px`;
    });

    // Add a subtle effect when clicking
    document.addEventListener("click", () => {
        cursor.style.transform = "scale(1.5)";
        setTimeout(() => {
            cursor.style.transform = "scale(1)";
        }, 100);
    });
});
