console.log("auth.js loaded");

const loginForm = document.getElementById("loginForm");

console.log("Form:", loginForm);

if (loginForm) {

    console.log("Listener attached");

    loginForm.addEventListener("submit", login);

}

async function login(e){

    e.preventDefault();

    const email =
        document.getElementById("email").value;

    const password =
        document.getElementById("password").value;

    const formData = new URLSearchParams();

    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch(

        `${API_BASE_URL}/auth/login`,

        {

            method: "POST",

            headers:{

                "Content-Type":
                "application/x-www-form-urlencoded"

            },

            body: formData

        }

    );

    const data = await response.json();

    const message =
        document.getElementById("message");


    if(response.ok){

        // Save JWT

        localStorage.setItem(
            "token",
            data.access_token
        );

        console.log("Token saved.");

        console.log(localStorage.getItem("token"));

        message.innerHTML =

        "<span class='text-success'>Login Successful!</span>";

        setTimeout(()=>{

            window.location.href =
            "projects.html";

        },1000);

    }

    else{

        if(Array.isArray(data.detail)){

            message.innerHTML =
            "<span class='text-danger'>Invalid request.</span>";

        }

        else{

            message.innerHTML =

            `<span class='text-danger'>

                ${data.detail}

            </span>`;

        }

    }

}