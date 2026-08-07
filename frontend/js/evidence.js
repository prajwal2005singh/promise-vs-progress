loadProjects();

async function loadProjects(){

    const response =
    await fetch(

        `${API_BASE_URL}/projects/`

    );

    const projects =
    await response.json();

    const dropdown =
    document.getElementById("project");

    projects.forEach(project=>{

        dropdown.innerHTML += `

        <option value="${project.id}">

        ${project.name}

        </option>

        `;

    });

}

const form =
document.getElementById("evidenceForm");

form.addEventListener(
"submit",
uploadEvidence
);

async function uploadEvidence(e){

    e.preventDefault();

    const evidence={

        project_id:
        Number(document.getElementById("project").value),

        description:
        document.getElementById("description").value,

        latitude:
        Number(document.getElementById("latitude").value),

        longitude:
        Number(document.getElementById("longitude").value),

        captured_at:
        new Date(
            document.getElementById("captured_at").value
        ).toISOString()

    };

    const response=
    await fetch(

        `${API_BASE_URL}/evidence/`,

        {

            method:"POST",

            headers:getHeaders(),

            body:JSON.stringify(evidence)

        }

    );

    const message=
    document.getElementById("message");

    if(response.ok){

        message.innerHTML=

        "<span class='text-success fw-bold'>Evidence uploaded successfully.</span>";

        form.reset();

    }

    else{

        const data=
        await response.json();

        message.innerHTML=

        `<span class="text-danger">

        ${data.detail}

        </span>`;

    }

}