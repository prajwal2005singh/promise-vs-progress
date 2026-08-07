const proposalForm =
document.getElementById("proposalForm");

proposalForm.addEventListener(
    "submit",
    submitProposal
);

async function submitProposal(e){

    e.preventDefault();

    const proposal = {

        name:
        document.getElementById("name").value,

        description:
        document.getElementById("description").value,

        category:
        document.getElementById("category").value,

        location_name:
        document.getElementById("location").value,

        latitude:
        parseFloat(
            document.getElementById("latitude").value
        ),

        longitude:
        parseFloat(
            document.getElementById("longitude").value
        ),

        budget:
        parseInt(
            document.getElementById("budget").value
        )

    };

    const response = await fetch(

        `${API_BASE_URL}/proposals/`,

        {

            method:"POST",

            headers:getHeaders(),

            body:JSON.stringify(proposal)

        }

    );

    const message =
    document.getElementById("message");

    if(response.ok){

        message.innerHTML=

        "<span class='text-success fw-bold'>Proposal submitted successfully. Awaiting admin approval.</span>";

        proposalForm.reset();

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