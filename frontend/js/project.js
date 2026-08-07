async function loadProjects() {

    try {

        // Fetch projects from FastAPI backend
        const response = await fetch(
            `${API_BASE_URL}/projects/`
        );

        // Check if request was successful
        if (!response.ok) {
            throw new Error(
                `Failed to load projects: ${response.status}`
            );
        }

        const projects = await response.json();


        // ==========================================
        // DASHBOARD STATISTICS
        // ==========================================

        document.getElementById("projectCount").innerText =
            projects.length;


        // Count unique departments
        const departments = new Set(
            projects.map(project => project.department)
        );

        document.getElementById("departmentCount").innerText =
            departments.size;


        // Calculate total estimated budget
        const totalBudget = projects.reduce(
            (sum, project) =>
                sum + (Number(project.budget) || 0),
            0
        );

        const totalCrores = (totalBudget / 10000000).toFixed(0);

        document.getElementById("budgetTotal").innerText =
        `₹${totalCrores} Cr`;


        // ==========================================
        // PROJECT CARDS
        // ==========================================

        const container =
            document.getElementById("projectsContainer");

        container.innerHTML = "";


        // Handle empty database
        if (projects.length === 0) {

            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info text-center">
                        No infrastructure projects are currently available.
                    </div>
                </div>
            `;

            return;
        }


        // Generate project cards
        projects.forEach(project => {


            // ======================================
            // STATUS STYLING
            // ======================================

            let statusBadge = "bg-secondary";
            let borderClass = "border-secondary";


            if (project.status === "APPROVED") {

                statusBadge = "bg-success";
                borderClass = "border-success";

            }

            else if (project.status === "ONGOING") {

                statusBadge = "bg-primary";
                borderClass = "border-primary";

            }

            else if (project.status === "PLANNING") {

                statusBadge = "bg-warning text-dark";
                borderClass = "border-warning";

            }

            else if (project.status === "TENDER") {

                statusBadge = "bg-info text-dark";
                borderClass = "border-info";

            }

            else if (project.status === "COMPLETED") {

                statusBadge = "bg-dark";
                borderClass = "border-dark";

            }


            // ======================================
            // BUDGET FORMATTING
            // ======================================

            const formattedBudget =
                project.budget !== null &&
                project.budget !== undefined

                ? "₹" +
                  Number(project.budget)
                      .toLocaleString("en-IN")

                : "Not Available";


            // ======================================
            // DATE FORMATTING
            // ======================================

            const completionDate =
                project.expected_completion

                ? new Date(
                    project.expected_completion
                  ).toLocaleDateString(
                    "en-IN",
                    {
                        day: "2-digit",
                        month: "short",
                        year: "numeric"
                    }
                  )

                : "TBD";


            // ======================================
            // CREATE CARD
            // ======================================

            container.innerHTML += `

                <div class="col-md-6 col-lg-4 mb-4">

                    <div class="
                        card
                        shadow-sm
                        h-100
                        border-start
                        border-5
                        ${borderClass}
                    ">

                        <div class="card-body d-flex flex-column">


                            <!-- Project Name -->

                            <h4 class="card-title">

                                ${project.name}

                            </h4>


                            <!-- Description -->

                            <p class="card-text text-muted">

                                ${project.description}

                            </p>


                            <hr>


                            <!-- Department -->

                            <p>

                                <strong>
                                    Department:
                                </strong>

                                ${project.department}

                            </p>


                            <!-- Category -->

                            <p>

                                <strong>
                                    Category:
                                </strong>

                                ${project.category}

                            </p>


                            <!-- Location -->

                            <p>

                                <strong>
                                    📍 Location:
                                </strong>

                                ${project.location_name}

                            </p>


                            <!-- Status -->

                            <p>

                                <strong>
                                    Status:
                                </strong>

                                <span class="
                                    badge
                                    ${statusBadge}
                                ">

                                    ${project.status}

                                </span>

                            </p>


                            <!-- Budget -->

                            <p>

                                <strong>
                                    Budget:
                                </strong>

                                ${formattedBudget}

                            </p>


                            <!-- Completion -->

                            <p>

                                <strong>
                                    Expected Completion:
                                </strong>

                                ${completionDate}

                            </p>


                            <!-- View Details Button -->

                            <div class="mt-auto">

                                <button
                                    class="btn btn-outline-primary w-100"
                                    onclick="showProjectDetails(${project.id})"
                                >

                                    View Details

                                </button>

                            </div>


                        </div>

                    </div>

                </div>

            `;

        });

    }

    catch (error) {

        console.error(
            "Error loading projects:",
            error
        );


        const container =
            document.getElementById(
                "projectsContainer"
            );


        if (container) {

            container.innerHTML = `

                <div class="col-12">

                    <div
                        class="alert alert-danger text-center"
                    >

                        Unable to load projects.

                        <br>

                        Please make sure the backend server
                        is running.

                    </div>

                </div>

            `;

        }

    }

}



// ==========================================
// PROJECT DETAILS
// ==========================================

async function showProjectDetails(projectId) {

    try {

        const response = await fetch(
            `${API_BASE_URL}/projects/${projectId}`
        );


        if (!response.ok) {

            throw new Error(
                "Project not found"
            );

        }


        const project =
            await response.json();


        const budget =
            project.budget !== null &&
            project.budget !== undefined

            ? "₹" +
              Number(project.budget)
                  .toLocaleString("en-IN")

            : "Not Available";


        const completion =
            project.expected_completion

            ? new Date(
                project.expected_completion
              ).toLocaleDateString(
                "en-IN"
              )

            : "TBD";


        alert(
`PROJECT DETAILS

Project:
${project.name}

Department:
${project.department}

Category:
${project.category}

Status:
${project.status}

Location:
${project.location_name}

Budget:
${budget}

Expected Completion:
${completion}

Description:
${project.description}`
        );

    }

    catch (error) {

        console.error(error);

        alert(
            "Unable to load project details."
        );

    }

}



// ==========================================
// START PAGE
// ==========================================

loadProjects();