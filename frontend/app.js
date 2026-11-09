console.log("🔥 ERB APP.JS LOADED");


// ============================================================
// API
// ============================================================

const API_URL = String(window.UPRINT_API_URL || "").replace(/\/$/, "");


// ============================================================
// ELEMENTS
// ============================================================

const pdfFile = document.getElementById("pdfFile");

const uploadZone = document.getElementById("uploadZone");

const uploadProgress =
    document.getElementById("uploadProgress");

const uploadProgressBar =
    document.getElementById("uploadProgressBar");

const uploadProgressText =
    document.getElementById("uploadProgressText");

const fileInfo = document.getElementById("fileInfo");

const fileInfoDetails =
    document.getElementById("fileInfoDetails");

const removeFileBtn =
    document.getElementById("removeFileBtn");

const optionsCard =
    document.getElementById("optionsCard");

const orderCard =
    document.getElementById("orderCard");

const errorMessage =
    document.getElementById("errorMessage");

const copiesDisplay =
    document.getElementById("copies");

const minusBtn =
    document.getElementById("minusBtn");

const plusBtn =
    document.getElementById("plusBtn");

const totalPrice =
    document.getElementById("totalPrice");

const pricePages =
    document.getElementById("pricePages");

const priceCopies =
    document.getElementById("priceCopies");

const priceRate =
    document.getElementById("priceRate");

const orderBtn =
    document.getElementById("orderBtn");

const orderId =
    document.getElementById("orderId");

const orderPages =
    document.getElementById("orderPages");

const orderType =
    document.getElementById("orderType");

const orderPaperSize =
    document.getElementById("orderPaperSize");

const orderSides =
    document.getElementById("orderSides");

const orderOrientation =
    document.getElementById("orderOrientation");

const orderAmount =
    document.getElementById("orderAmount");

const printStatus =
    document.getElementById("printStatus");

const orderMessage =
    document.getElementById("orderMessage");

const printAnotherBtn =
    document.getElementById("printAnotherBtn");


// Navigation
const navHamburger =
    document.getElementById("navHamburger");

const navLinks =
    document.getElementById("navLinks");


// Order tracking
const trackInput =
    document.getElementById("trackInput");

const trackBtn =
    document.getElementById("trackBtn");

const trackResult =
    document.getElementById("trackResult");

const trackError =
    document.getElementById("trackError");

const trackOrderId =
    document.getElementById("trackOrderId");

const trackPages =
    document.getElementById("trackPages");

const trackCopies =
    document.getElementById("trackCopies");

const trackType =
    document.getElementById("trackType");

const trackPaperSize =
    document.getElementById("trackPaperSize");

const trackSides =
    document.getElementById("trackSides");

const trackOrientation =
    document.getElementById("trackOrientation");

const trackAmount =
    document.getElementById("trackAmount");

const trackPayment =
    document.getElementById("trackPayment");

const trackStatus =
    document.getElementById("trackStatus");

const workflowSteps = document.querySelectorAll("[data-workflow-step]");
const workflowConnectors = document.querySelectorAll(".step-connector");


// ============================================================
// VARIABLES
// ============================================================

let uploadedFileId = null;

let pageCount = 0;

let copies = 1;

let workflowTimer = null;


// ============================================================
// PAGE READY
// ============================================================

console.log("🟢 ERB FRONTEND READY");


// ============================================================
// MOBILE NAVIGATION
// ============================================================

// This explanatory animation does not represent a real order. When a real
// backend order is tracked, syncWorkflowWithOrderStatus replaces its state.
function setWorkflowStep(stepName) {

    const stepOrder = ["upload", "print", "collect"];
    const activeIndex = stepOrder.indexOf(stepName);

    workflowSteps.forEach(function (step, index) {
        step.classList.toggle("is-active", index === activeIndex);
        step.classList.toggle("is-complete", activeIndex > index);
    });

    workflowConnectors.forEach(function (connector, index) {
        connector.classList.toggle("is-complete", activeIndex > index);
    });

}

function startWorkflowDemo() {

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        setWorkflowStep("upload");
        return;
    }

    const steps = ["upload", "print", "collect"];
    let current = 0;

    setWorkflowStep(steps[current]);

    workflowTimer = setInterval(function () {
        current = (current + 1) % steps.length;
        setWorkflowStep(steps[current]);
    }, 2600);

}

function syncWorkflowWithOrderStatus(status) {

    const normalizedStatus = String(status || "").toLowerCase();

    if (normalizedStatus === "completed") {
        setWorkflowStep("collect");
    } else if (normalizedStatus === "printing") {
        setWorkflowStep("print");
    } else if (normalizedStatus === "queued" || normalizedStatus === "pending") {
        setWorkflowStep("upload");
    }

}

startWorkflowDemo();

if (navHamburger) {

    navHamburger.addEventListener("click", function () {

        navHamburger.classList.toggle("open");

        navLinks.classList.toggle("open");

    });

}

// Close mobile nav on link click
document.querySelectorAll(".nav-link").forEach(function (link) {

    link.addEventListener("click", function () {

        navHamburger.classList.remove("open");

        navLinks.classList.remove("open");

    });

});

// Active nav link on scroll
const sections = document.querySelectorAll("[id]");
const navLinksAll = document.querySelectorAll(".nav-link");

window.addEventListener("scroll", function () {

    let current = "";

    sections.forEach(function (section) {

        const top = section.offsetTop - 120;

        if (window.scrollY >= top) {

            current = section.getAttribute("id");

        }

    });

    navLinksAll.forEach(function (link) {

        link.classList.remove("active");

        if (link.getAttribute("href") === "#" + current) {

            link.classList.add("active");

        }

    });

});


// ============================================================
// ERROR DISPLAY
// ============================================================

let errorTimeout = null;

function showError(message) {

    console.error("❌ ERROR:", message);

    errorMessage.textContent = message;

    errorMessage.classList.remove("hidden");

    // Auto-dismiss after 5 seconds
    if (errorTimeout) {
        clearTimeout(errorTimeout);
    }

    errorTimeout = setTimeout(function () {
        hideError();
    }, 5000);

}


function hideError() {

    errorMessage.textContent = "";

    errorMessage.classList.add("hidden");

}


// ============================================================
// DRAG & DROP
// ============================================================

if (uploadZone) {

    ["dragenter", "dragover"].forEach(function (event) {

        uploadZone.addEventListener(event, function (e) {

            e.preventDefault();

            e.stopPropagation();

            uploadZone.classList.add("drag-over");

        });

    });

    ["dragleave", "drop"].forEach(function (event) {

        uploadZone.addEventListener(event, function (e) {

            e.preventDefault();

            e.stopPropagation();

            uploadZone.classList.remove("drag-over");

        });

    });

    uploadZone.addEventListener("drop", function (e) {

        const files = e.dataTransfer.files;

        if (files.length > 0) {

            // Assign the dropped file to the input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(files[0]);
            pdfFile.files = dataTransfer.files;

            // Trigger the upload
            pdfFile.dispatchEvent(
                new Event("change", { bubbles: true })
            );

        }

    });

}


// ============================================================
// PDF UPLOAD
// ============================================================

pdfFile.addEventListener("change", async function () {

    console.log("📄 FILE SELECTED");

    hideError();

    const file = pdfFile.files[0];


    if (!file) {

        console.log("No file selected");

        return;

    }


    console.log(
        "📤 Uploading:",
        file.name
    );


    // Make sure selected file is PDF

    if (
        file.type !== "application/pdf" &&
        !file.name.toLowerCase().endsWith(".pdf")
    ) {

        showError(
            "Please select a PDF file."
        );

        return;

    }

    // Check file size (50 MB)
    if (file.size > 50 * 1024 * 1024) {

        showError(
            "File too large. Maximum size is 50 MB."
        );

        return;

    }


    const formData = new FormData();

    formData.append(
        "file",
        file
    );


    // Show progress
    uploadProgress.classList.remove("hidden");
    uploadProgressBar.style.width = "0%";
    uploadProgressText.textContent = "Uploading...";
    uploadZone.style.display = "none";
    fileInfo.classList.add("hidden");


    try {

        console.log(
            "🌐 Sending request to:",
            `${API_URL}/upload-pdf`
        );

        // Animate progress bar
        simulateProgress();


        const response = await fetch(
            `${API_URL}/upload-pdf`,
            {
                method: "POST",
                body: formData
            }
        );


        console.log(
            "📡 Upload response:",
            response.status
        );


        const data =
            await response.json();


        console.log(
            "📦 Backend response:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "PDF upload failed"
            );

        }


        // ====================================================
        // COMPLETE PROGRESS
        // ====================================================

        uploadProgressBar.style.width = "100%";
        uploadProgressText.textContent = "Upload complete!";

        await delay(500);

        uploadProgress.classList.add("hidden");


        // ====================================================
        // SAVE BACKEND DATA
        // ====================================================

        uploadedFileId =
            data.file_id;

        pageCount =
            data.pages;

        setWorkflowStep("print");


        console.log(
            "🆔 File ID:",
            uploadedFileId
        );

        console.log(
            "📄 Pages:",
            pageCount
        );


        // ====================================================
        // SHOW FILE INFORMATION
        // ====================================================

        fileInfo.classList.remove("hidden");


        const sizeKB =
            data.file_size_bytes
                ? (
                    data.file_size_bytes / 1024
                ).toFixed(1)
                : "Unknown";


        fileInfoDetails.innerHTML = `
            <strong>
                ${escapeHtml(
                    data.filename || file.name
                )}
            </strong>
            <span>
                ${pageCount} page${pageCount !== 1 ? "s" : ""}
                • ${sizeKB} KB
            </span>
        `;


        // ====================================================
        // SHOW PRINT OPTIONS
        // ====================================================

        optionsCard.classList.remove("hidden");


        console.log(
            "🟢 PRINT OPTIONS DISPLAYED"
        );


        // ====================================================
        // UPDATE PRICE
        // ====================================================

        updatePrice();


        // Scroll smoothly to options

        setTimeout(function () {

            optionsCard.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        }, 100);


    } catch (error) {

        console.error(
            "❌ UPLOAD ERROR:",
            error
        );

        uploadProgress.classList.add("hidden");
        uploadZone.style.display = "";

        showError(
            error.message ||
            "Could not upload PDF."
        );

    }

});


// ============================================================
// UPLOAD PROGRESS SIMULATION
// ============================================================

let progressInterval = null;

function simulateProgress() {

    let width = 0;

    if (progressInterval) {
        clearInterval(progressInterval);
    }

    progressInterval = setInterval(function () {

        width += Math.random() * 15;

        if (width >= 85) {
            width = 85;
            clearInterval(progressInterval);
        }

        uploadProgressBar.style.width = width + "%";

    }, 200);

}


// ============================================================
// REMOVE / REPLACE FILE
// ============================================================

if (removeFileBtn) {

    removeFileBtn.addEventListener("click", function () {

        resetUpload();

    });

}

function resetUpload() {

    uploadedFileId = null;
    pageCount = 0;
    copies = 1;

    pdfFile.value = "";
    copiesDisplay.textContent = "1";

    fileInfo.classList.add("hidden");
    optionsCard.classList.add("hidden");
    orderCard.classList.add("hidden");
    uploadProgress.classList.add("hidden");
    uploadZone.style.display = "";

    updatePrice();

}


// ============================================================
// COPY MINUS
// ============================================================

minusBtn.addEventListener(
    "click",
    function () {

        if (copies > 1) {

            copies--;

            copiesDisplay.textContent =
                copies;

            updatePrice();

        }

    }
);


// ============================================================
// COPY PLUS
// ============================================================

plusBtn.addEventListener(
    "click",
    function () {

        if (copies < 50) {

            copies++;

            copiesDisplay.textContent =
                copies;

            updatePrice();

        }

    }
);


// ============================================================
// PRINT TYPE
// ============================================================

document
    .querySelectorAll(
        'input[name="printType"], input[name="paperSize"], input[name="sides"], input[name="orientation"]'
    )
    .forEach(function (radio) {

        radio.addEventListener(
            "change",
            function () {

                // Update active classes for visual feedback
                const name = radio.name;
                document.querySelectorAll(`input[name="${name}"]`).forEach(function(r) {
                    const card = r.closest('.toggle-card');
                    if (card) {
                        if (r.checked) {
                            card.classList.add('toggle-card--active');
                        } else {
                            card.classList.remove('toggle-card--active');
                        }
                    }
                });

                console.log(
                    `🖨️ ${name}:`,
                    radio.value
                );

                updatePrice();

            }
        );

    });


// ============================================================
// PRICE CALCULATION
// ============================================================

function updatePrice() {

    const selectedRadio =
        document.querySelector(
            'input[name="printType"]:checked'
        );
    const printType =
        selectedRadio ? selectedRadio.value : "bw";

    const selectedPaper =
        document.querySelector(
            'input[name="paperSize"]:checked'
        );
    const paperSize =
        selectedPaper ? selectedPaper.value : "a4";

    let pricePerPage =
        printType === "color"
            ? 10
            : 2;
            
    // Double the price for A3
    if (paperSize === "a3") {
        pricePerPage *= 2;
    }


    // Update breakdown
    if (pricePages) {
        pricePages.textContent = pageCount;
    }

    if (priceCopies) {
        priceCopies.textContent = copies;
    }

    if (priceRate) {
        priceRate.textContent =
            `₹${pricePerPage} / page`;
    }


    // Total
    const total =
        pageCount *
        copies *
        pricePerPage;


    if (totalPrice) {
        totalPrice.textContent =
            `₹${total}`;
    }


    console.log(
        "💰 Price:",
        total
    );

}


// ============================================================
// PLACE ORDER
// ============================================================

orderBtn.addEventListener(
    "click",
    async function () {

        console.log(
            "🛒 PLACE ORDER CLICKED"
        );


        hideError();


        // ----------------------------------------------------
        // CHECK FILE
        // ----------------------------------------------------

        if (!uploadedFileId) {

            showError(
                "Please upload a PDF first."
            );

            return;

        }


        // ----------------------------------------------------
        // GET PRINT TYPE
        // ----------------------------------------------------

        const selectedRadio =
            document.querySelector(
                'input[name="printType"]:checked'
            );
        const printType =
            selectedRadio ? selectedRadio.value : "bw";

        const selectedPaper =
            document.querySelector(
                'input[name="paperSize"]:checked'
            );
        const paperSize =
            selectedPaper ? selectedPaper.value : "a4";

        const selectedSides =
            document.querySelector(
                'input[name="sides"]:checked'
            );
        const sides =
            selectedSides ? selectedSides.value : "single";

        const selectedOrientation =
            document.querySelector(
                'input[name="orientation"]:checked'
            );
        const orientation =
            selectedOrientation ? selectedOrientation.value : "portrait";

        // ... existing logs ...
        console.log("🖨️ Print type:", printType);
        console.log("📄 File ID:", uploadedFileId);
        console.log("📑 Pages:", pageCount);
        console.log("📚 Copies:", copies);

        // ----------------------------------------------------
        // DISABLE BUTTON
        // ----------------------------------------------------

        orderBtn.disabled = true;

        const btnText =
            orderBtn.querySelector(".order-btn-text");

        if (btnText) {
            btnText.textContent =
                "Creating order...";
        }


        try {

            // =================================================
            // CREATE ORDER
            // =================================================

            const url =
                `${API_URL}/create-order` +
                `?file_id=${encodeURIComponent(
                    uploadedFileId
                )}` +
                `&copies=${copies}` +
                `&print_type=${encodeURIComponent(
                    printType
                )}` +
                `&paper_size=${encodeURIComponent(
                    paperSize
                )}` +
                `&sides=${encodeURIComponent(
                    sides
                )}` +
                `&orientation=${encodeURIComponent(
                    orientation
                )}`;


            console.log(
                "🌐 CREATE ORDER URL:",
                url
            );


            const response =
                await fetch(
                    url,
                    {
                        method: "POST",
                        headers: {
                            "accept":
                                "application/json"
                        }
                    }
                );


            console.log(
                "📡 Order response:",
                response.status
            );


            const data =
                await response.json();


            console.log(
                "📦 Order backend response:",
                data
            );


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Order creation failed"
                );

            }


            // =================================================
            // SHOW ORDER RESULT
            // =================================================

            orderId.textContent =
                data.order_id || "N/A";


            orderPages.textContent =
                data.pages || pageCount;


            orderType.textContent =
                (data.print_type || printType) === "color"
                    ? "Color"
                    : "B&W";
                    
            if (orderPaperSize) {
                orderPaperSize.textContent = (data.paper_size || paperSize).toUpperCase();
            }
            if (orderSides) {
                orderSides.textContent = (data.sides || sides) === "double" ? "Double-sided" : "Single-sided";
            }
            if (orderOrientation) {
                const o = data.orientation || orientation;
                orderOrientation.textContent = o.charAt(0).toUpperCase() + o.slice(1);
            }


            orderAmount.textContent =
                `₹${data.amount || 0}`;


            printStatus.textContent =
                data.print_status || "Pending";

            syncWorkflowWithOrderStatus(data.print_status);


            orderMessage.textContent =
                data.message ||
                "Your order has been created successfully.";


            // Show order card

            orderCard.classList.remove(
                "hidden"
            );


            // =================================================
            // HIDE OPTIONS
            // =================================================

            optionsCard.classList.add(
                "hidden"
            );

            // Also hide upload section details
            fileInfo.classList.add("hidden");
            uploadZone.style.display = "none";


            console.log(
                "✅ ORDER CREATED:",
                data.order_id
            );


            // Scroll to result

            setTimeout(function () {

                orderCard.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }, 100);


        } catch (error) {

            console.error(
                "❌ ORDER ERROR:",
                error
            );


            showError(
                error.message ||
                "Could not create order."
            );


        } finally {

            orderBtn.disabled = false;

            if (btnText) {
                btnText.textContent =
                    "Place Order";
            }

        }

    }
);


// ============================================================
// PRINT ANOTHER
// ============================================================

if (printAnotherBtn) {

    printAnotherBtn.addEventListener("click", function () {

        // Reset everything
        resetUpload();

        // Hide order card
        orderCard.classList.add("hidden");

        // Scroll to upload section
        const uploadSection =
            document.getElementById("uploadSection");

        if (uploadSection) {

            setTimeout(function () {

                uploadSection.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }, 100);

        }

    });

}


// ============================================================
// ORDER TRACKING
// ============================================================


if (trackBtn) {

    trackBtn.addEventListener("click", async function () {

        const trackId = trackInput.value.trim();

        if (!trackId) {
            trackError.textContent = "Please enter an order ID.";
            trackError.classList.remove("hidden");
            trackResult.classList.add("hidden");
            return;
        }

        trackError.classList.add("hidden");
        trackResult.classList.add("hidden");

        trackBtn.textContent = "Tracking...";
        trackBtn.disabled = true;

        try {

            const response = await fetch(
                `${API_URL}/order/${encodeURIComponent(trackId)}`,
                {
                    method: "GET",
                    headers: {
                        "ngrok-skip-browser-warning": "true"
                    }
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Could not find this order."
                );
            }

            // Fill in tracking results
            trackOrderId.textContent = data.order_id || trackId;
            trackPages.textContent = data.pages || "—";
            trackCopies.textContent = data.copies || "—";

            trackType.textContent =
                (data.print_type || "bw") === "color"
                    ? "Color"
                    : "B&W";

            if (trackPaperSize) {
                trackPaperSize.textContent =
                    (data.paper_size || "a4").toUpperCase();
            }

            if (trackSides) {
                trackSides.textContent =
                    (data.sides || "single") === "double"
                        ? "Double-sided"
                        : "Single-sided";
            }

            if (trackOrientation) {
                const o = data.orientation || "portrait";
                trackOrientation.textContent =
                    o.charAt(0).toUpperCase() + o.slice(1);
            }

            trackAmount.textContent = `₹${data.amount || 0}`;
            trackPayment.textContent = data.payment_status || "—";
            trackStatus.textContent = data.print_status || "—";

            syncWorkflowWithOrderStatus(data.print_status);

            trackResult.classList.remove("hidden");

        } catch (error) {

            trackError.textContent =
                error.message || "Could not find this order.";

            trackError.classList.remove("hidden");

        } finally {

            trackBtn.textContent = "Track";
            trackBtn.disabled = false;

        }

    });

}


// Track on Enter key
if (trackInput) {

    trackInput.addEventListener("keydown", function (e) {

        if (e.key === "Enter") {

            trackBtn.click();

        }

    });

}


// ============================================================
// UTILITY: DELAY
// ============================================================

function delay(ms) {

    return new Promise(function (resolve) {
        setTimeout(resolve, ms);
    });

}


// ============================================================
// UTILITY: HTML ESCAPE
// ============================================================

function escapeHtml(value) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        value;

    return div.innerHTML;

}
