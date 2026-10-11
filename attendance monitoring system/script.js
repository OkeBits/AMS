/* =========================================
   PASSWORD SHOW / HIDE
========================================= */

function togglePassword(inputId, button) {

    const input = document.getElementById(inputId);

    if (input.type === "password") {

        input.type = "text";
        button.textContent = "Hide";

    } else {

        input.type = "password";
        button.textContent = "Show";

    }

}


/* =========================================
   ADMINISTRATOR LOGIN
========================================= */

const loginForm = document.getElementById("loginForm");

if (loginForm) {

    loginForm.addEventListener("submit", async function(event) {

        event.preventDefault();

        const gmail =
            document.getElementById("loginUsername").value.trim();

        const password =
            document.getElementById("loginPassword").value;

        const message =
            document.getElementById("loginMessage");


        /* CHECK GMAIL FORMAT */

        const gmailPattern =
            /^[a-zA-Z0-9._%+-]+@gmail\.com$/;

        if (!gmailPattern.test(gmail)) {

            message.textContent =
                "Please enter a valid Gmail address ending with @gmail.com.";

            message.style.display = "block";

            return;
        }


        /* CHECK PASSWORD FORMAT */

        const passwordPattern =
            /^[0-9]{6}$/;

        if (!passwordPattern.test(password)) {

            message.textContent =
                "Password must contain exactly 6 digits.";

            message.style.display = "block";

            return;
        }


        /* SEND LOGIN TO FLASK */

        try {

            const response = await fetch("/login", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    username: gmail,
                    password: password
                })

            });


            const data = await response.json();


            /* LOGIN SUCCESS */

            if (data.success) {

                window.location.href = "/dashboard";

                return;
            }


            /* LOGIN FAILED */

            message.textContent =
                data.message || "Invalid Gmail or password.";

            message.style.display = "block";


        } catch (error) {

            console.error("Login error:", error);

            message.textContent =
                "Unable to connect to the server.";

            message.style.display = "block";

        }

    });

}


/* =========================================
   TEACHER REGISTRATION
========================================= */

const registerForm = document.getElementById("registerForm");

if (registerForm) {

    registerForm.addEventListener("submit", async function(event) {

        event.preventDefault();

        const gmail =
            document.getElementById("registerUsername").value.trim();

        const password =
            document.getElementById("registerPassword").value;

        const confirmPassword =
            document.getElementById("confirmPassword").value;

        const message =
            document.getElementById("registerMessage");


        /* CHECK GMAIL */

        const gmailPattern =
            /^[a-zA-Z0-9._%+-]+@gmail\.com$/;

        if (!gmailPattern.test(gmail)) {

            message.textContent =
                "Please enter a valid Gmail address ending with @gmail.com.";

            message.style.display = "block";

            return;
        }


        /* CHECK PASSWORD */

        const passwordPattern =
            /^[0-9]{6}$/;

        if (!passwordPattern.test(password)) {

            message.textContent =
                "Password must contain exactly 6 digits.";

            message.style.display = "block";

            return;
        }


        /* CHECK CONFIRM PASSWORD */

        if (password !== confirmPassword) {

            message.textContent =
                "Passwords do not match.";

            message.style.display = "block";

            return;
        }


        /* SEND DATA TO FLASK */

        try {

            const response = await fetch("/register", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    username: gmail,
                    password: password,
                    confirm_password: confirmPassword
                })

            });


            const data = await response.json();


            /* REGISTRATION SUCCESS */

            if (data.success) {

                message.textContent =
                    "Registration successful! Redirecting to login...";

                message.style.display = "block";

                setTimeout(function() {

                    window.location.href = "/login";

                }, 1000);

                return;
            }


            /* REGISTRATION FAILED */

            message.textContent =
                data.message || "Registration failed.";

            message.style.display = "block";


        } catch (error) {

            console.error("Registration error:", error);

            message.textContent =
                "Unable to connect to the server.";

            message.style.display = "block";

        }

    });

}


/* =========================================
   CURRENT DATE
========================================= */

function updateCurrentDate() {

    const dateElement =
        document.getElementById("currentDate");

    if (!dateElement) {
        return;
    }

    const today = new Date();

    const formattedDate =
        today.toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric"
        });

    dateElement.textContent =
        formattedDate;
}

updateCurrentDate();


/* ==========================================
   ADD STRAND BUTTON
========================================== */

document.addEventListener("DOMContentLoaded", function() {

    const editStrandsButton =
        document.getElementById("editStrandsButton");

    if (editStrandsButton) {

        editStrandsButton.addEventListener(
            "click",
            function() {

                showStrandManager();

            }
        );

    }

});


/* ==========================================
   SHOW SECTION
========================================== */

function showSection(sectionId) {
    const selectedSection =
        document.getElementById(sectionId);

    if (!selectedSection || !selectedSection.classList.contains("section")) {
        return;
    }

    const hash = sectionId === "students" &&
        window.location.hash.startsWith("#students/")
        ? window.location.hash
        : `#${sectionId}`;
    window.history.replaceState(null, "", hash);

    const sections =
        document.querySelectorAll(".section");

    sections.forEach(function(section) {

        section.classList.remove("active");

    });


    selectedSection.classList.add("active");


    /* DASHBOARD CARDS */

    const dashboardCards =
        document.querySelector(".cards");

    if (dashboardCards) {

        if (sectionId === "home") {

            dashboardCards.style.display = "grid";

        } else {

            dashboardCards.style.display = "none";

        }

    }


    /* PAGE TITLE */

    const pageTitle =
        document.getElementById("pageTitle");

    if (pageTitle) {

        if (sectionId === "home") {

            pageTitle.textContent =
                "Admin Dashboard";

        } else if (sectionId === "register") {

            pageTitle.textContent =
                "Add Student";

        } else if (sectionId === "students") {

            pageTitle.textContent =
                "Student List";

        } else if (sectionId === "reports") {

            pageTitle.textContent =
                "Attendance Reports";

        } else if (sectionId === "settings") {

            pageTitle.textContent =
                "Settings";
            loadPhilSmsSettings();

        } else if (sectionId === "scanner") {

            pageTitle.textContent =
                "RFID Scanner";

            setTimeout(function() {

                prepareRFIDScanner();

            }, 100);

        } else {

            pageTitle.textContent =
                sectionId.charAt(0).toUpperCase() +
                sectionId.slice(1);

        }

    }

}


/* ==========================================
  SENIOR HIGH SCHOOL
========================================== */

const educationLevel =
    document.getElementById("educationLevel");

const gradeLevel =
    document.getElementById("gradeLevel");

const strand =
    document.getElementById("strand");


if (educationLevel) {

    educationLevel.addEventListener(
        "change",
        function() {

            gradeLevel.innerHTML = "";

            strand.innerHTML = "";


            /* SENIOR HIGH SCHOOL */

            if (
                educationLevel.value ===
                "Senior High School"
            ) {

                gradeLevel.disabled = false;

                gradeLevel.innerHTML = `
                    <option value="" disabled selected>
                        Select grade level
                    </option>

                    <option value="Grade 11">
                        Grade 11
                    </option>

                    <option value="Grade 12">
                        Grade 12
                    </option>
                `;


                strand.disabled = false;

                strand.innerHTML = `
                    <option value="" disabled selected>
                        Select strand
                    </option>

                    <option value="BE">
                        BE
                    </option>

                    <option value="ASSH">
                        ASSH
                    </option>

                    <option value="STEM">
                        STEM
                    </option>

                    <option value="ICT">
                        ICT
                    </option>

                    <option value="IT">
                        IT
                    </option>
                `;

            }

        }
    );

}

/* ==========================================
   ADD STUDENT - SENIOR HIGH SCHOOL
========================================== */

const studentForm = document.getElementById("studentForm");

if (studentForm) {
    studentForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const message = document.getElementById("studentFormMessage");

        const rfidNumber = document.getElementById("rfidNumber").value.trim();
        const fullName = document.getElementById("fullName").value.trim();
        const age = document.getElementById("age").value;
        const birthday = document.getElementById("birthday").value;
        const educationLevel = "Senior High School";
        const gradeLevel = document.getElementById("gradeLevel").value;
        const strand = document.getElementById("strand").value;
        const parentName = document.getElementById("parentName").value.trim();
        const parentPhone = document.getElementById("parentPhone").value.trim();

        const scheduleType = document.getElementById("schedule_type")?.value;
        const classStartTime = document.getElementById("class_start_time")?.value;
        const classEndTime = document.getElementById("class_end_time")?.value;

        if (!scheduleType || !classStartTime || !classEndTime) {
            message.textContent = "Please select the student's schedule and enter the class start and end times.";
            message.style.display = "block";
            message.style.color = "#b44b4b";
            return;
        }

        if (classStartTime >= classEndTime) {
            message.textContent = "Class end time must be later than class start time.";
            message.style.display = "block";
            message.style.color = "#b44b4b";
            return;
        }

        try {
            const response = await fetch("/api/students", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    rfid_number: rfidNumber,
                    full_name: fullName,
                    age: age,
                    birthday: birthday,
                    education_level: educationLevel,
                    grade_level: gradeLevel,
                    strand: strand,
                    parent_name: parentName,
                    parent_phone: parentPhone,
                    schedule_type: scheduleType,
                    class_start_time: classStartTime,
                    class_end_time: classEndTime
                })
            });

            const data = await response.json();

            console.log("Add Student HTTP status:", response.status);
            console.log("Add Student server response:", data);

            if (response.ok && data.success) {
                message.textContent = "Senior High School student successfully saved!";
                message.style.display = "block";
                message.style.color = "#150f4d";

                studentForm.reset();

                // Restore the fixed education level after reset.
                const educationInput = document.getElementById("educationLevel");
                if (educationInput) {
                    educationInput.value = "Senior High School";
                }

                return;
            }

            message.textContent = data.message || "Student could not be saved.";
            message.style.display = "block";
            message.style.color = "#b44b4b";

        } catch (error) {
            console.error("Add student error:", error);

            message.textContent = "Unable to connect to the server.";
            message.style.display = "block";
            message.style.color = "#b44b4b";
        }
    });
}


/* ==========================================
   STUDENT LIST GROUPS
========================================== */

async function showStudentGroup(groupName) {

    const groupView =
        document.getElementById(
            "studentGroupView"
        );


    const groupTitle =
        document.getElementById(
            "selectedStudentGroup"
        );


    const studentTable =
        document.getElementById(
            "selectedStudentTable"
        );


    /* CHANGE TITLE */

    groupTitle.textContent =
        groupName + " Students";
    window.history.replaceState(
        null,
        "",
        `#students/${encodeURIComponent(groupName)}`
    );


    /* SHOW LOADING */

    studentTable.innerHTML = `
        <tr>
            <td colspan="4">
                Loading students...
            </td>
        </tr>
    `;


    /* SHOW GROUP */

    groupView.style.display =
        "block";


    try {

        /* GET STUDENTS */

        const response =
            await fetch(
                "/api/students"
            );


        if (!response.ok) {

            throw new Error(
                "Could not load students."
            );

        }


        const students =
            await response.json();


        /* SEPARATE GROUP NAME */

        let selectedStrand = "";
        let selectedGrade = "";


        /* SENIOR HIGH SCHOOL */

        const seniorHighMatch =
            groupName.match(
                /^(.+)\s(11|12)$/
            );


        if (seniorHighMatch) {

            selectedStrand =
                seniorHighMatch[1];

            selectedGrade =
                "Grade " +
                seniorHighMatch[2];

        }




        /* FILTER STUDENTS */

        const filteredStudents =
            students.filter(
                function(student) {

                    return (
                        student.strand ===
                        selectedStrand &&

                        student.grade_level ===
                        selectedGrade
                    );

                }
            );


        /* NO STUDENTS */

        if (filteredStudents.length === 0) {

            studentTable.innerHTML = `
                <tr class="empty-student-row">
                    <td colspan="4">
                        No students registered in this group.
                    </td>
                </tr>
            `;

        }


        /* DISPLAY STUDENTS */

        else {

            studentTable.innerHTML = "";


            filteredStudents.forEach(
                function(student) {

                    const row =
                        document.createElement("tr");


                    row.innerHTML = `
                        <td>${student.rfid_number}</td>
                        <td>${student.full_name}</td>
                        <td>${student.grade_level}</td>
                        <td>${student.parent_phone || "—"}</td>
                    `;


                    studentTable.appendChild(row);

                }
            );

        }


    } catch (error) {

        console.error(
            "Student list error:",
            error
        );


        studentTable.innerHTML = `
            <tr>
                <td colspan="4">
                    Unable to load students from the database.
                </td>
            </tr>
        `;

    }


    /* SCROLL TO GROUP */

    groupView.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


/* ==========================================
   HIDE STUDENT GROUP
========================================== */

function hideStudentGroup() {

    const groupView =
        document.getElementById(
            "studentGroupView"
        );

    groupView.style.display =
        "none";
    window.history.replaceState(null, "", "#students");

}


/* ==========================================
   ATTENDANCE REPORTS
========================================== */

const reportMonth =
    document.getElementById(
        "reportMonth"
    );


/* SET CURRENT MONTH */

if (reportMonth) {

    const today =
        new Date();

    const year =
        today.getFullYear();

    const month =
        String(
            today.getMonth() + 1
        ).padStart(2, "0");

    reportMonth.value =
        `${year}-${month}`;

}


/* ==========================================
   GENERATE ATTENDANCE REPORT
========================================== */

async function generateAttendanceReport() {

    const monthInput =
        document.getElementById("reportMonth");

    const groupInput =
        document.getElementById("reportGroup");

    const reportTable =
        document.getElementById("attendanceReportTable");

    const selectedMonth =
        monthInput.value;

    const selectedGroup =
        groupInput.value;


    if (!selectedMonth) {
        alert("Please select a month.");
        return;
    }


    reportTable.innerHTML = `
        <tr>
            <td colspan="37">
                Loading attendance report...
            </td>
        </tr>
    `;


    try {

        const url =
            "/api/attendance-report?month="
            + encodeURIComponent(selectedMonth)
            + "&group="
            + encodeURIComponent(selectedGroup);


        const response =
            await fetch(url);


        if (!response.ok) {
            throw new Error(
                "Could not load attendance report."
            );
        }


        const data = await response.json();


        console.log(
            "Attendance Report Data:",
            data
        );


        if (!data.success) {
            throw new Error(
                data.message ||
                "Could not generate report."
            );
        }


       // =========================================
        // UPDATE REPORT TITLE + PRINT HEADER
        // =========================================

        const reportTitle =
            document.getElementById("reportTitle");

        const date =
            new Date(selectedMonth + "-01");

        const monthName =
            date.toLocaleString(
                "en-US",
                {
                    month: "long",
                    year: "numeric"
                }
            );


        /* UPDATE REPORT TITLE */

        if (reportTitle) {

            reportTitle.textContent =
                monthName +
                " Attendance Report";

        }


        /* =========================================
        UPDATE PRINT HEADER
        ========================================= */

        const printMonth =
            document.getElementById("printMonth");

        const printGroup =
            document.getElementById("printGroup");


        if (printMonth) {

            printMonth.textContent =
                monthName;

        }


        if (printGroup) {

            printGroup.textContent =
                selectedGroup ||
                "All Students";

        }

        // =========================================
        // UPDATE GROUP NAME
        // =========================================

        const reportGroup =
            document.getElementById(
                "attendanceReportGroup"
            );


        if (reportGroup) {

            reportGroup.textContent =
                selectedGroup ||
                "All Students";
        }


        // =========================================
        // DETERMINE NUMBER OF DAYS
        // =========================================

        const year =
            parseInt(
                selectedMonth.substring(0, 4)
            );


        const month =
            parseInt(
                selectedMonth.substring(5, 7)
            );


        const daysInMonth =
            new Date(
                year,
                month,
                0
            ).getDate();


        // =========================================
        // NO STUDENTS
        // =========================================

        if (
            !data.students ||
            data.students.length === 0
        ) {

            reportTable.innerHTML = `
                <tr class="empty-report-row">
                    <td colspan="${daysInMonth + 5}">
                        No registered students found
                        for this student group.
                    </td>
                </tr>
            `;


            document.getElementById(
                "reportTotalStudents"
            ).textContent = "0";


            document.getElementById(
                "reportPresent"
            ).textContent = "0";


            document.getElementById(
                "reportLate"
            ).textContent = "0";


            document.getElementById(
                "reportAbsent"
            ).textContent = "0";


            return;
        }


        // =========================================
        // CREATE TABLE HEADER
        // =========================================

        const table =
            reportTable.closest("table");


        const tableHead =
            table.querySelector("thead");


        tableHead.innerHTML = "";


        const headerRow =
            document.createElement("tr");


        // Student information columns

        const rfidHeader =
            document.createElement("th");

        rfidHeader.textContent =
            "RFID Number";

        headerRow.appendChild(
            rfidHeader
        );


        const nameHeader =
            document.createElement("th");

        nameHeader.textContent =
            "Full Name";

        headerRow.appendChild(
            nameHeader
        );


        const groupHeader =
            document.createElement("th");

        groupHeader.textContent =
            "Grade / Section";

        headerRow.appendChild(
            groupHeader
        );


        // =========================================
        // DAY COLUMNS
        // =========================================

        for (
            let day = 1;
            day <= daysInMonth;
            day++
        ) {

            const dayHeader =
                document.createElement("th");

            dayHeader.textContent =
                day;

            headerRow.appendChild(
                dayHeader
            );
        }


        // =========================================
        // TOTAL COLUMNS
        // =========================================

        const presentHeader =
            document.createElement("th");

        presentHeader.textContent =
            "Present";

        headerRow.appendChild(
            presentHeader
        );


        const lateHeader =
            document.createElement("th");

        lateHeader.textContent =
            "Late";

        headerRow.appendChild(
            lateHeader
        );


        const absentHeader =
            document.createElement("th");

        absentHeader.textContent =
            "Absent";

        headerRow.appendChild(
            absentHeader
        );


        tableHead.appendChild(
            headerRow
        );


        // =========================================
        // CLEAR OLD TABLE DATA
        // =========================================

        reportTable.innerHTML = "";


        let totalPresent = 0;
        let totalLate = 0;
        let totalAbsent = 0;


        // =========================================
        // CREATE STUDENT ROWS
        // =========================================

        data.students.forEach(
            function(student) {

                const row =
                    document.createElement("tr");


                // ---------------------------------
                // RFID
                // ---------------------------------

                const rfidCell =
                    document.createElement("td");

                rfidCell.textContent =
                    student.rfid_number || "—";

                row.appendChild(
                    rfidCell
                );


                // ---------------------------------
                // FULL NAME
                // ---------------------------------

                const nameCell =
                    document.createElement("td");

                nameCell.textContent =
                    student.full_name || "—";

                row.appendChild(
                    nameCell
                );


                // ---------------------------------
                // GRADE / SECTION
                // ---------------------------------

                const groupCell =
                    document.createElement("td");

                groupCell.textContent =
                    (
                        student.grade_level ||
                        "—"
                    )
                    + " / " +
                    (
                        student.strand ||
                        "—"
                    );

                row.appendChild(
                    groupCell
                );


                // ---------------------------------
                // ATTENDANCE DATA
                // ---------------------------------

                const attendance =
                    student.attendance || {};


                let present = 0;
                let late = 0;
                let absent = 0;


                // ---------------------------------
                // CREATE DAY CELLS
                // ---------------------------------

                for (
                    let day = 1;
                    day <= daysInMonth;
                    day++
                ) {

                    const dayCell =
                        document.createElement("td");


                    const dayString =
                        String(day)
                        .padStart(2, "0");


                    const dateKey =
                        selectedMonth +
                        "-" +
                        dayString;


                    const record =
                        attendance[dateKey];


                    if (record) {

                        const status =
                            String(
                                record.status ||
                                ""
                            )
                            .trim();


                        if (
                            status ===
                            "Present"
                        ) {

                            dayCell.textContent =
                                "P";

                            present++;

                            totalPresent++;
                        }

                        else if (
                            status ===
                            "Late"
                        ) {

                            dayCell.textContent =
                                "L";

                            late++;

                            totalLate++;
                        }

                        else if (
                            status ===
                            "Absent"
                        ) {

                            dayCell.textContent =
                                "A";

                            absent++;

                            totalAbsent++;
                        }

                        else {

                            dayCell.textContent =
                                "—";
                        }

                    }

                    else {

                        dayCell.textContent =
                            "—";
                    }


                    row.appendChild(
                        dayCell
                    );
                }


                // ---------------------------------
                // PRESENT TOTAL
                // ---------------------------------

                const presentCell =
                    document.createElement("td");

                presentCell.textContent =
                    present;

                row.appendChild(
                    presentCell
                );


                // ---------------------------------
                // LATE TOTAL
                // ---------------------------------

                const lateCell =
                    document.createElement("td");

                lateCell.textContent =
                    late;

                row.appendChild(
                    lateCell
                );


                // ---------------------------------
                // ABSENT TOTAL
                // ---------------------------------

                const absentCell =
                    document.createElement("td");

                absentCell.textContent =
                    absent;

                row.appendChild(
                    absentCell
                );


                reportTable.appendChild(
                    row
                );

            }
        );


        // =========================================
        // UPDATE SUMMARY CARDS
        // =========================================

        document.getElementById(
            "reportTotalStudents"
        ).textContent =
            data.students.length;


        document.getElementById(
            "reportPresent"
        ).textContent =
            totalPresent;


        document.getElementById(
            "reportLate"
        ).textContent =
            totalLate;


        document.getElementById(
            "reportAbsent"
        ).textContent =
            totalAbsent;


    }

    catch (error) {

        console.error(
            "Attendance report error:",
            error
        );


        reportTable.innerHTML = `
            <tr>
                <td colspan="37">
                    Unable to load attendance report.
                </td>
            </tr>
        `;

    }

}

/* ==========================================
   PRINT ATTENDANCE REPORT
========================================== */

function printAttendanceReport() {

    window.print();

}


/* ==========================================
   RFID SCANNER
========================================== */

const rfidScannerInput =
    document.getElementById(
        "rfidScannerInput"
    );


const scannerStatusIndicator =
    document.getElementById(
        "scannerStatusIndicator"
    );


const scannerStatusText =
    document.getElementById(
        "scannerStatusText"
    );


const lastScannedRFID =
    document.getElementById(
        "lastScannedRFID"
    );


const lastScanStatus =
    document.getElementById(
        "lastScanStatus"
    );

const smsSendModal =
    document.getElementById("smsSendModal");
const smsSendDescription =
    document.getElementById("smsSendDescription");
const smsSendResult =
    document.getElementById("smsSendResult");
let smsAutoCloseTimer = null;

function closeSmsSendModal() {
    if (!smsSendModal) {
        return;
    }
    if (smsAutoCloseTimer) {
        clearTimeout(smsAutoCloseTimer);
        smsAutoCloseTimer = null;
    }
    smsSendModal.hidden = true;
    focusRFIDScanner();
}

function showRfidSmsResult(student, eventType, sms) {
    if (!smsSendModal || !smsSendDescription || !smsSendResult) {
        return;
    }
    if (smsAutoCloseTimer) {
        clearTimeout(smsAutoCloseTimer);
        smsAutoCloseTimer = null;
    }

    const parentName = student.parent_name || "Parent/Guardian";
    const isSent = sms && sms.status === "sent";
    const isFailed = sms && ["failed", "disabled"].includes(sms.status);
    const resultMessage = isSent
        ? `Attendance message for ${student.full_name || "the student"} ` +
            `was sent to parent/guardian ${parentName} via PhilSMS. ` +
            "Check PhilSMS logs for delivery status."
        : isFailed
            ? `Message was not sent to ${parentName}. ${
                sms.message || "Check SMS settings."
            }`
            : `Could not confirm whether the message was sent to ${parentName}. ` +
                "Restart the attendance app and check PhilSMS logs before scanning again.";

    smsSendDescription.textContent =
        `${eventType === "time_out" ? "Time Out" : "Time In"} recorded for ` +
        `${student.full_name || "the student"}.`;
    smsSendResult.hidden = false;
    smsSendResult.dataset.state = isSent
        ? "success"
        : isFailed ? "error" : "unknown";
    smsSendResult.textContent = resultMessage;
    smsSendModal.hidden = false;

    smsAutoCloseTimer = setTimeout(function() {
        smsAutoCloseTimer = null;
        closeSmsSendModal();
    }, 6000);
}

if (smsSendModal) {
    smsSendModal.addEventListener("click", function(event) {
        if (event.target === smsSendModal) {
            closeSmsSendModal();
        }
    });
}

document.addEventListener("keydown", function(event) {
    if (event.key === "Escape" && smsSendModal && !smsSendModal.hidden) {
        closeSmsSendModal();
    }
});

const scannedStudentCard =
    document.getElementById(
        "scannedStudentCard"
    );


/* ==========================================
   FOCUS RFID INPUT
========================================== */

function focusRFIDScanner() {

    if (rfidScannerInput) {

        rfidScannerInput.focus();

    }

}


/* ==========================================
   PREPARE RFID SCANNER
========================================== */

function prepareRFIDScanner() {

    if (!rfidScannerInput) {

        return;

    }


    rfidScannerInput.value =
        "";


    scannerStatusText.textContent =
        "Scanner Ready";


    lastScanStatus.textContent =
        "Waiting for scan";


    scannerStatusIndicator.style.background =
        "#4f8064";


    focusRFIDScanner();

}




/* ==========================================
   RFID SCANNER INPUT
========================================== */

let rfidScanTimer = null;
let rfidScanProcessing = false;

if (rfidScannerInput) {

    rfidScannerInput.addEventListener(
        "input",
        function() {

            const rfidNumber =
                rfidScannerInput.value.trim();


            if (!rfidNumber) {

                return;

            }


            /*
             * Wait briefly after the last character.
             * RFID scanners send the characters very quickly.
             */

            clearTimeout(rfidScanTimer);


            rfidScanTimer =
                setTimeout(
                    function() {

                        if (
                            rfidScanProcessing
                        ) {

                            return;

                        }


                        const finalRFID =
                            rfidScannerInput.value.trim();


                        if (!finalRFID) {

                            return;

                        }


                        rfidScanProcessing =
                            true;


                        processRFIDScan(
                            finalRFID
                        ).finally(
                            function() {

                                rfidScanProcessing =
                                    false;

                            }
                        );

                    },
                    200
                );

        }
    );


    /*
     * Keep Enter support as a backup.
     */

    rfidScannerInput.addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {

                event.preventDefault();

                clearTimeout(
                    rfidScanTimer
                );


                const rfidNumber =
                    rfidScannerInput.value.trim();


                if (
                    !rfidNumber ||
                    rfidScanProcessing
                ) {

                    return;

                }


                rfidScanProcessing =
                    true;


                processRFIDScan(
                    rfidNumber
                ).finally(
                    function() {

                        rfidScanProcessing =
                            false;

                    }
                );

            }

        }
    );

}


/* ==========================================
   PROCESS RFID
========================================== */

async function processRFIDScan(
    rfidNumber
) {

    lastScannedRFID.textContent =
        rfidNumber;


    lastScanStatus.textContent =
        "Checking database...";


    scannerStatusText.textContent =
        "Checking RFID...";


    scannerStatusIndicator.style.background =
        "#d4a64a";


    try {

        const response =
            await fetch(
                "/api/scan",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        rfid:
                            rfidNumber
                    })
                }
            );


        const responseText = await response.text();
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (error) {
            if (responseText.trimStart().startsWith("<")) {
                throw new Error(
                    "The attendance server returned an HTML page. " +
                    "Restart the latest main.py with F5 and try again."
                );
            }
            throw new Error("The attendance server returned an invalid response.");
        }


        /* ==========================================
           RFID NOT REGISTERED
        ========================================== */

        if (!data.success) {

            lastScanStatus.textContent =
                data.message ||
                "RFID not registered.";


            scannerStatusText.textContent =
                "RFID Not Registered";


            scannerStatusIndicator.style.background =
                "#b44b4b";


            scannedStudentCard.style.display =
                "block";


            document.getElementById(
                "scannedStudentRFID"
            ).textContent =
                rfidNumber;


            document.getElementById(
                "scannedStudentName"
            ).textContent =
                "Student not registered";


            document.getElementById(
                "scannedStudentGrade"
            ).textContent =
                "—";


            document.getElementById(
                "scannedStudentSection"
            ).textContent =
                "—";

            document.getElementById(
                "scannedStudentParentPhone"
            ).textContent =
                "—";

            rfidScannerInput.value =
                "";


            setTimeout(
                function() {

                    focusRFIDScanner();

                },
                100
            );


            return;

        }


        /* ==========================================
           RFID SUCCESS
        ========================================== */

        scannedStudentCard.style.display =
            "block";

        const scannedStudent = data.student || {};

        document.getElementById(
            "scannedStudentRFID"
        ).textContent =
            scannedStudent.rfid_number || rfidNumber;

        document.getElementById(
            "scannedStudentName"
        ).textContent =
            scannedStudent.full_name || "Student name unavailable";


        document.getElementById(
            "scannedStudentGrade"
        ).textContent =
            scannedStudent.grade_level || "—";


        document.getElementById(
            "scannedStudentSection"
        ).textContent =
            scannedStudent.strand || "—";


        if (data.attendance_id) {
            const smsResult = data.sms || {
                status: "unknown",
                message: "The server did not return an SMS status."
            };
            const studentName =
                scannedStudent.full_name || "the student";
            const parentName =
                scannedStudent.parent_name || "the parent/guardian";
            const parentMessage = smsResult.status === "sent"
                ? `Attendance message for ${studentName} was sent to ` +
                    `${parentName} via PhilSMS. Check PhilSMS logs for delivery status.`
                : ["failed", "disabled"].includes(smsResult.status)
                    ? `Attendance message was not sent to ${parentName}.`
                    : `Could not confirm whether the attendance message was sent to ${parentName}.`;
            lastScanStatus.textContent =
                `${data.message || "Attendance recorded."} ${parentMessage}`;
            showRfidSmsResult(scannedStudent, data.event, smsResult);
        } else {
            lastScanStatus.textContent =
                data.message || "Attendance recorded.";
        }


        scannerStatusText.textContent =
            data.attendance_status || "Attendance recorded";


        scannerStatusIndicator.style.background =
            "#4f8064";


        /* ==========================================
           REFRESH DASHBOARD ATTENDANCE
        ========================================== */

        loadDashboardAttendance();
        loadDashboardStats();

        /* ==========================================
           CLEAR RFID INPUT
        ========================================== */

        rfidScannerInput.value =
            "";


        setTimeout(
            function() {

                if (!smsSendModal || smsSendModal.hidden) {
                    focusRFIDScanner();
                }

            },
            100
        );


    } catch (error) {

        console.error(
            "RFID scan error:",
            error
        );


        const scanErrorMessage =
            error instanceof Error
                ? error.message
                : "An unknown error occurred.";

        lastScanStatus.textContent =
            "Unable to process RFID scan: " + scanErrorMessage;


        scannerStatusText.textContent =
            "Scan Failed";


        scannerStatusIndicator.style.background =
            "#b44b4b";


        rfidScannerInput.value =
            "";


        setTimeout(
            function() {

                focusRFIDScanner();

            },
            100
        );

    }

}


/* ==========================================
   DASHBOARD ATTENDANCE TABLE
========================================== */

async function loadDashboardAttendance() {

    const attendanceTable =
        document.getElementById(
            "dashboardAttendanceTable"
        );


    if (!attendanceTable) {

        return;

    }


    attendanceTable.innerHTML = `
        <tr>
        <td colspan="8">
                Loading attendance records...
            </td>
        </tr>
    `;


    try {

        const response =
            await fetch(
                "/api/dashboard-attendance"
            );


        if (!response.ok) {

            throw new Error(
                "Could not load attendance records."
            );

        }


        const records =
            await response.json();


        /* NO RECORDS */

        if (records.length === 0) {

            attendanceTable.innerHTML = `
                <tr class="empty-attendance-row">
                    <td colspan="8">
                        No attendance records for today.
                    </td>
                </tr>
            `;

            return;

        }


        /* CLEAR TABLE */

        attendanceTable.innerHTML = "";


        /* DISPLAY RECORDS */

        records.forEach(
            function(record) {

                const row =
                    document.createElement(
                        "tr"
                    );


                row.innerHTML = `
                    <td>${record.rfid_number}</td>

                    <td>${record.full_name}</td>

                    <td>${record.grade_level}</td>

                    <td>${record.strand}</td>

                    <td>${record.date}</td>

                    <td>${record.time_in || "—"}</td>

                    <td>${record.time_out || "—"}</td>

                    <td>${record.status}</td>
                `;

                attendanceTable.appendChild(
                    row
                );

            }
        );


    } catch (error) {

        console.error(
            "Dashboard attendance error:",
            error
        );


        attendanceTable.innerHTML = `
            <tr>
                <td colspan="8">
                    Unable to load attendance records.
                </td>
            </tr> 
        `;

    }

}

/* ==========================================
   LOAD DASHBOARD ATTENDANCE + STATISTICS
========================================== */

let dashboardCurrentDate = "";


/* ==========================================
   GET TODAY'S DATE
========================================== */

function getDashboardDate() {

    const today = new Date();

    return (
        today.getFullYear() +
        "-" +
        String(
            today.getMonth() + 1
        ).padStart(2, "0") +
        "-" +
        String(
            today.getDate()
        ).padStart(2, "0")
    );

}


/* ==========================================
   CHECK FOR NEW DAY
========================================== */

function checkForNewDashboardDay() {

    const currentDate =
        getDashboardDate();


    /*
     * First time the dashboard loads
     */

    if (!dashboardCurrentDate) {

        dashboardCurrentDate =
            currentDate;

        return;

    }


    /*
     * A new day has started
     */

    if (
        currentDate !==
        dashboardCurrentDate
    ) {

        dashboardCurrentDate =
            currentDate;


        console.log(
            "New day detected. Refreshing dashboard..."
        );


        /*
         * Clear the old attendance display
         */

        const attendanceTable =
            document.getElementById(
                "dashboardAttendanceTable"
            );


        if (attendanceTable) {

            attendanceTable.innerHTML = `
                <tr class="empty-attendance-row">
                    <td colspan="8">
                        No attendance records for today.
                    </td>
                </tr>
            `;

        }


        /*
         * Load the new day's data
         */

        loadDashboardAttendance();

        loadDashboardStats();

    }

}


/* ==========================================
   INITIAL DASHBOARD LOAD
========================================== */

document.addEventListener(
    "DOMContentLoaded",
    function() {
        const locationState = window.location.hash.slice(1);
        const [savedSection, ...savedGroupParts] = locationState.split("/");
        const sectionId = document.getElementById(savedSection)?.classList
            .contains("section")
            ? savedSection
            : "home";

        dashboardCurrentDate =
            getDashboardDate();

        showSection(sectionId);
        if (sectionId === "students" && savedGroupParts.length) {
            const savedGroup = decodeURIComponent(savedGroupParts.join("/"));
            if (/^.+ (11|12)$/.test(savedGroup)) {
                showStudentGroup(savedGroup);
            }
        }

        loadDashboardAttendance();

        loadDashboardStats();

    }
);


/* ==========================================
   CHECK DATE EVERY MINUTE
========================================== */

setInterval(
    checkForNewDashboardDay,
    60000
);
/* ==========================================
   DASHBOARD STATISTICS
========================================== */

async function loadDashboardStats() {

    try {

        const response =
            await fetch("/api/dashboard-stats");

        if (!response.ok) {

            throw new Error(
                "Could not load dashboard statistics."
            );

        }

        const data =
            await response.json();

        console.log(
            "Dashboard statistics:",
            data
        );


        if (data.success) {

            /* TOTAL STUDENTS */

            const totalStudents =
                document.getElementById(
                    "totalStudents"
                );

            if (totalStudents) {

                totalStudents.textContent =
                    data.total_students;

            }


            /* ENTERED TODAY */

            const enteredToday =
                document.getElementById(
                    "enteredToday"
                );

            if (enteredToday) {

                enteredToday.textContent =
                    data.entered_today;

            }


            /* ABSENT TODAY */

            const absentToday =
                document.getElementById(
                    "absentToday"
                );

            if (absentToday) {

                absentToday.textContent =
                    data.absent_today;

            }

        }

    } catch (error) {

        console.error(
            "Dashboard statistics error:",
            error
        );

    }

}


/* ==========================================
   SETTINGS - CHANGE ADMIN PASSWORD
========================================== */

const changePasswordForm =
    document.getElementById("changePasswordForm");

if (changePasswordForm) {

    changePasswordForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const currentUsername =
                document.getElementById(
                    "currentUsername"
                ).value.trim();

            const currentPassword =
                document.getElementById(
                    "currentPassword"
                ).value;

            const administrativeCode =
                document.getElementById(
                    "administrativeCode"
                ).value;

            const newPassword =
                document.getElementById(
                    "newPassword"
                ).value;

            const confirmNewPassword =
                document.getElementById(
                    "confirmNewPassword"
                ).value;

            const message =
                document.getElementById(
                    "changePasswordMessage"
                );


            /* ==========================================
               CHECK EMPTY FIELDS
            ========================================== */

            if (
                !currentUsername ||
                !currentPassword ||
                !administrativeCode ||
                !newPassword ||
                !confirmNewPassword
            ) {

                message.textContent =
                    "Please complete all fields.";

                message.style.display =
                    "block";

                return;
            }


            /* ==========================================
               CHECK CURRENT PASSWORD FORMAT
            ========================================== */

            if (!/^\d{6}$/.test(currentPassword)) {

                message.textContent =
                    "Current password must contain exactly 6 digits.";

                message.style.display =
                    "block";

                return;
            }


            /* ==========================================
               CHECK NEW PASSWORD FORMAT
            ========================================== */

            if (!/^\d{6}$/.test(newPassword)) {

                message.textContent =
                    "New password must contain exactly 6 digits.";

                message.style.display =
                    "block";

                return;
            }


            /* ==========================================
               CHECK PASSWORD MATCH
            ========================================== */

            if (
                newPassword !==
                confirmNewPassword
            ) {

                message.textContent =
                    "New passwords do not match.";

                message.style.display =
                    "block";

                return;
            }


            /* ==========================================
               SEND TO FLASK
            ========================================== */

            try {

                const response =
                    await fetch(
                        "/api/change-password",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({

                                currentUsername:
                                    currentUsername,

                                currentPassword:
                                    currentPassword,

                                administrativeCode:
                                    administrativeCode,

                                newPassword:
                                    newPassword,

                                confirmNewPassword:
                                    confirmNewPassword

                            })
                        }
                    );


                const result =
                    await response.json();


                /* ==========================================
                   FAILED
                ========================================== */

                if (
                    !response.ok ||
                    !result.success
                ) {

                    message.textContent =
                        result.message ||
                        "Password change failed.";

                    message.style.display =
                        "block";

                    return;
                }


                /* ==========================================
                   SUCCESS
                ========================================== */

                message.textContent =
                    "Administrator password changed successfully.";

                message.style.display =
                    "block";


                /* CLEAR FORM */

                changePasswordForm.reset();

            }

            catch (error) {

                console.error(
                    "Change password error:",
                    error
                );

                message.textContent =
                    "Unable to connect to the server. Make sure Flask is running.";

                message.style.display =
                    "block";

            }

        }
    );

}

/* ==========================================
   PHILSMS SETTINGS
========================================== */

const smsSettingsForm =
    document.getElementById("smsSettingsForm");

const philSmsSettingsMessage =
    document.getElementById("philSmsSettingsMessage");

const DEFAULT_PHILSMS_TIME_IN_TEMPLATE =
    "Dear Parent/Guardian, please be informed that {student_name} arrived at school on {date} at {time}. Student details: {grade} {strand}. Thank you.";
const DEFAULT_PHILSMS_TIME_OUT_TEMPLATE =
    "Dear Parent/Guardian, please be informed that {student_name} departed from school on {date} at {time}. Student details: {grade} {strand}. Thank you.";

function showPhilSmsSettingsMessage(message, success) {
    philSmsSettingsMessage.textContent = message;
    philSmsSettingsMessage.style.display = "block";
    philSmsSettingsMessage.style.background =
        success ? "#edf5ef" : "#fff0f0";
    philSmsSettingsMessage.style.color =
        success ? "#315c47" : "#9b3434";
}

async function readPhilSmsApiResponse(response) {
    const responseText = await response.text();
    try {
        return JSON.parse(responseText);
    } catch (error) {
        if (responseText.trimStart().startsWith("<")) {
            throw new Error(
                "The app returned an HTML page instead of the SMS API response. " +
                "Stop the old Flask server and restart main.py."
            );
        }
        throw new Error("The SMS API returned an invalid response.");
    }
}

async function loadPhilSmsSettings() {
    try {
        const response = await fetch("/api/sms/settings");
        const result = await readPhilSmsApiResponse(response);
        if (!response.ok || !result.success) {
            throw new Error(result.message || "Could not load PhilSMS settings.");
        }
        document.getElementById("philSmsSenderId").value =
            result.sender_id || "";
        document.getElementById("philSmsApiUrl").value =
            result.api_url || "https://app.philsms.com/api/v3/sms/send";
        document.getElementById("philSmsEnabled").checked =
            result.enabled;
        document.getElementById("philSmsTimeIn").checked =
            result.notify_time_in;
        document.getElementById("philSmsTimeOut").checked =
            result.notify_time_out;
        document.getElementById("philSmsTimeInTemplate").value =
            result.time_in_template || DEFAULT_PHILSMS_TIME_IN_TEMPLATE;
        document.getElementById("philSmsTimeOutTemplate").value =
            result.time_out_template || DEFAULT_PHILSMS_TIME_OUT_TEMPLATE;
        document.getElementById("philSmsTokenStatus").textContent =
            result.token_configured
                ? "API token is saved securely (••••••••). The actual token is never shown. Leave blank to keep it or enter a new token to replace it."
                : "Token is not configured. Your token is never shown after saving.";
        document.getElementById("philSmsApiToken").placeholder =
            result.token_configured
                ? "Saved securely — leave blank to keep current token"
                : "Paste your PhilSMS API token";
    } catch (error) {
        showPhilSmsSettingsMessage(error.message, false);
    }
}

if (smsSettingsForm) {
    smsSettingsForm.addEventListener("submit", async function(event) {
        event.preventDefault();
        const submitButton = smsSettingsForm.querySelector(
            'button[type="submit"]'
        );
        submitButton.disabled = true;

        try {
            const response = await fetch("/api/sms/settings", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    api_token: document.getElementById("philSmsApiToken").value,
                    sender_id: document.getElementById("philSmsSenderId").value,
                    api_url: document.getElementById("philSmsApiUrl").value,
                    enabled: document.getElementById("philSmsEnabled").checked,
                    notify_time_in: document.getElementById("philSmsTimeIn").checked,
                    notify_time_out: document.getElementById("philSmsTimeOut").checked,
                    time_in_template: document.getElementById("philSmsTimeInTemplate").value,
                    time_out_template: document.getElementById("philSmsTimeOutTemplate").value
                })
            });
            const result = await readPhilSmsApiResponse(response);
            if (!response.ok || !result.success) {
                throw new Error(result.message || "Could not save PhilSMS settings.");
            }
            document.getElementById("philSmsApiToken").value = "";
            showPhilSmsSettingsMessage(result.message, true);
            await loadPhilSmsSettings();
        } catch (error) {
            showPhilSmsSettingsMessage(error.message, false);
        } finally {
            submitButton.disabled = false;
        }
    });
}

const philSmsTestButton =
    document.getElementById("philSmsTestButton");

if (philSmsTestButton) {
    philSmsTestButton.addEventListener("click", async function() {
        const phoneNumber =
            document.getElementById("philSmsTestPhone").value.trim();
        if (!phoneNumber) {
            showPhilSmsSettingsMessage("Enter a mobile number for the test SMS.", false);
            return;
        }

        philSmsTestButton.disabled = true;
        const originalLabel = philSmsTestButton.textContent;
        philSmsTestButton.textContent = "Sending test SMS...";
        showPhilSmsSettingsMessage("Sending test SMS. Please wait...", true);
        try {
            const response = await fetch("/api/sms/test", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({phone_number: phoneNumber})
            });
            const result = await readPhilSmsApiResponse(response);
            if (!response.ok || !result.success) {
                throw new Error(result.message || "Test SMS failed.");
            }
            showPhilSmsSettingsMessage(result.message, true);
        } catch (error) {
            showPhilSmsSettingsMessage(error.message, false);
        } finally {
            philSmsTestButton.disabled = false;
            philSmsTestButton.textContent = originalLabel;
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.reset();

        const password = loginForm.querySelector(
            'input[type="password"], input[type="text"]'
        );

        if (password) {
            password.value = "";
        }
    }
});
