loadProposals();

async function loadProposals(){

    const response = await fetch(

        `${API_BASE_URL}/proposals/`,

        {

            headers: getHeaders()

        }

    );

    const proposals = await response.json();

    const table =
        document.getElementById(
            "proposalTable"
        );

    table.innerHTML = "";

    proposals.forEach(p=>{

        table.innerHTML += `

        <tr>

            <td>${p.id}</td>

            <td>${p.name}</td>

            <td>${p.category}</td>

            <td>${p.status}</td>

            <td>

                <button
                    class="btn btn-success btn-sm"

                    onclick="approveProposal(${p.id})">

                    Approve

                </button>

            </td>

        </tr>

        `;

    });

}

async function approveProposal(id){

    const response = await fetch(

        `${API_BASE_URL}/proposals/approve/${id}`,

        {

            method:"PUT",

            headers:getHeaders()

        }

    );

    if(response.ok){

        alert("Proposal Approved");

        loadProposals();

    }

    else{

        alert("Approval Failed");

    }

}